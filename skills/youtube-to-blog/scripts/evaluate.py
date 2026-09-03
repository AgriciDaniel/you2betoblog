#!/usr/bin/env python3
"""Evaluate a delivered blog and write the evaluation note.

Reads <blog>/review.md (Overall Score, P0 count, BLOCKING line),
<blog>/preflight-report.json, the post markdown, the image manifest,
<run>/analysis/segments.json and <run>/brief/video-brief.json, then computes:

  overlap_ratio         fraction of the article's 8-grams found in the transcript
  frames_in_place       each frame sits in the article section that covers its timestamp
  attribution_ok        creator name and watch link in the first 200 words
                        (third-party mode also needs the disclosure line)
  links_ok              no youtu.be, every YouTube link in an allowed form,
                        HEAD 200 without redirect when the network is on
  thumbnail_ok          HEAD 200 for the metadata thumbnail (network only)
  verification_section  a "What we verified" heading exists
  voice_flags           occurrences of VOICE.md taboo phrases

Writes 05 Evaluations/<date>-<slug>.md and updates the post's yt2b_score and
yt2b_status (reviewed when score >= 90 and not blocking, else blocked).
Thresholds mirror 05 Evaluations/pipeline-rubric.md.

Exit codes: 0 ok, 1 failure, 2 invalid input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

SCORE_MIN = 90
P0_MAX = 0
OVERLAP_MAX = {"companion": 0.12, "expand": 0.06}
VOICE_FLAGS_MAX = 0
NGRAM = 8
ATTRIBUTION_WORDS = 200
HEAD_TIMEOUT = 5
MAX_LINK_CHECKS = 40
USER_AGENT = "yt2b-evaluate/1.0 (+https://github.com/AgriciDaniel)"
SKIP_HOSTS = {"example.com", "example.org", "www.example.com", "www.example.org"}

SCORE_RE = re.compile(r"Overall Score:\s*(\d{1,3})\s*/\s*100", re.I)
BLOCKING_RE = re.compile(r"^BLOCKING:\s*(true|false)\s*(?:\((.*?)\))?\s*$", re.I)
NO_P0_RE = re.compile(r"\b(?:no|zero)\s+P0\b", re.I)
P0_ITEM_RE = re.compile(r"^\s*[-*]\s*\**P0\**\s*[:)]", re.I | re.M)
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
DEEP_LINK_RE = re.compile(r"youtube\.com/watch\?v=[A-Za-z0-9_-]{11}&t=(\d+)s?")
DISCLOSURE_RE = re.compile(r"^\s*(?:>\s*)?(?:\*{1,2}|_)?\s*(?:Disclosure:|This article is an independent companion to)", re.I | re.M)
VERIFIED_RE = re.compile(r"^#{2,3}\s+what we verified\b", re.I | re.M)
YT_ALLOWED = [
    re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}(?:&t=\d+s?)?$"),
    re.compile(r"^https://www\.youtube\.com/@[A-Za-z0-9._-]+/?$"),
    re.compile(r"^https://www\.youtube\.com/channel/[A-Za-z0-9_-]+/?$"),
    re.compile(r"^https://www\.youtube\.com/c/[A-Za-z0-9_-]+/?$"),
    re.compile(r"^https://www\.youtube\.com/playlist\?list=[A-Za-z0-9_-]+$"),
    re.compile(r"^https://www\.youtube-nocookie\.com/embed/[A-Za-z0-9_-]{11}$"),
]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def plain_text(body: str) -> str:
    text = re.sub(r"```.*?```", " ", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\{#[^}]*\}", " ", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    return text.replace("|", " ")


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def ngram_set(tokens: list[str], n: int = NGRAM) -> set[tuple[str, ...]]:
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def overlap_ratio(article_tokens: list[str], transcript_tokens: list[str], n: int = NGRAM) -> tuple[float, int, int]:
    grams = ngram_set(transcript_tokens, n)
    total = max(0, len(article_tokens) - n + 1)
    if total == 0 or not grams:
        return 0.0, 0, total
    hits = sum(1 for i in range(total) if tuple(article_tokens[i:i + n]) in grams)
    return hits / total, hits, total


def transcript_tokens(run_dir: Path) -> tuple[list[str], str]:
    segments = common.json_load(run_dir / "analysis" / "segments.json", None)
    parts: list[str] = []
    if isinstance(segments, dict):
        for seg in segments.get("segments") or []:
            if not isinstance(seg, dict):
                continue
            for key in ("audio", "text", "transcript"):
                if isinstance(seg.get(key), str):
                    parts.append(seg[key])
            for key in ("cues", "lines"):
                for cue in seg.get(key) or []:
                    if isinstance(cue, dict) and isinstance(cue.get("text"), str):
                        parts.append(cue["text"])
                    elif isinstance(cue, str):
                        parts.append(cue)
        if parts:
            return words(" ".join(parts)), "segments.json"
    transcript = run_dir / "analysis" / "transcript.md"
    if transcript.is_file():
        _, body = common.read_note(transcript)
        _, sections = common.split_sections(body)
        text = next((c for h, c in sections if h.strip().lower() == "transcript"), body)
        return words(plain_text(text)), "transcript.md"
    return [], "none"


# ---------------------------------------------------------------------------
# Review and preflight parsing
# ---------------------------------------------------------------------------

def parse_review(text: str | None) -> dict:
    result = {"present": text is not None, "score": 0, "blocking": True, "reason": "", "p0": 0,
              "categories": [], "issues": [], "nonce": False}
    if text is None:
        result["reason"] = "review.md missing"
        return result
    m = SCORE_RE.search(text)
    if m:
        result["score"] = max(0, min(100, int(m.group(1))))
    non_empty = [line.strip() for line in text.splitlines() if line.strip()]
    if non_empty:
        bm = BLOCKING_RE.match(non_empty[-1])
        if bm:
            result["blocking"] = bm.group(1).lower() == "true"
            result["reason"] = (bm.group(2) or "").strip()
        else:
            result["reason"] = "review.md does not end with a BLOCKING line"
    result["nonce"] = bool(re.search(r"^Nonce:\s*[0-9a-f]{32}\s*$", text, re.I | re.M))
    for line in text.splitlines():
        cm = re.match(r"^\|\s*([A-Za-z][A-Za-z -]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+)\s*\|(.*)\|\s*$", line)
        if cm and cm.group(1).strip().lower() not in ("category",):
            result["categories"].append({"name": cm.group(1).strip(), "score": cm.group(2), "max": cm.group(3),
                                         "note": cm.group(4).strip()})
    severity = None
    critical_items = 0
    for line in text.splitlines():
        hm = re.match(r"^#{2,4}\s+(Critical|High|Medium|Low)\b", line, re.I)
        if hm:
            severity = hm.group(1).capitalize()
            continue
        if re.match(r"^#{1,4}\s", line):
            severity = None
            continue
        im = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if im and severity:
            item = im.group(1)
            if re.fullmatch(r"\(?none\)?\.?|no issues\.?|n/?a", item.strip().lower()):
                continue
            result["issues"].append({"severity": severity, "text": item})
            if severity == "Critical":
                critical_items += 1
    if NO_P0_RE.search(text):
        result["p0"] = 0
    else:
        result["p0"] = max(critical_items, len(P0_ITEM_RE.findall(text)))
    return result


def parse_preflight(path: Path) -> dict:
    report = common.json_load(path, None)
    gates: list[dict] = []
    if not isinstance(report, dict):
        return {"present": False, "passed": False, "gates": gates, "blocked": True}
    for g in report.get("gates") or []:
        if isinstance(g, dict):
            gates.append({"gate": g.get("gate"), "name": g.get("name"), "passed": bool(g.get("passed")),
                          "violations": list(g.get("violations") or [])})
    numbers = {g["gate"] for g in gates}
    passed = (not report.get("blocked", True)) and {1, 2, 3, 4, 5} <= numbers and all(g["passed"] for g in gates)
    return {"present": True, "passed": passed, "gates": gates, "blocked": bool(report.get("blocked", True))}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _heading_tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "with", "on", "how", "what", "why", "is", "do", "does", "your", "you"}
    return {w for w in words(text) if w not in stop}


def frames_in_place(body: str, manifest: dict | None, sections: list[dict]) -> tuple[bool, list[str]]:
    images = [i for i in (manifest or {}).get("images", []) if isinstance(i, dict) and i.get("t_s") is not None]
    if not images:
        return True, []
    if not sections:
        return True, ["brief has no section map; frame placement not judged"]
    preamble, blocks = common.split_sections(body)
    findings: list[str] = []
    ok = True
    for img in images:
        name = Path(str(img.get("rel") or img.get("path") or "")).name
        if not name:
            continue
        t = float(img["t_s"])
        brief_section = next((s for s in sections if float(s.get("start_s", 0)) <= t <= float(s.get("end_s", t))), None)
        if brief_section is None:
            findings.append(f"{name}: no brief section covers {t:.0f}s; skipped")
            continue
        placed = None
        for heading, content in blocks:
            if name in content:
                placed = (heading, content)
                break
        if placed is None:
            if name in preamble:
                findings.append(f"{name}: placed in the introduction, expected under '{brief_section.get('title')}'")
                ok = False
            else:
                findings.append(f"{name}: in the manifest but not used in the post")
            continue
        heading, content = placed
        lines = content.splitlines()
        kept = []
        skip_next = False
        for line in lines:
            if skip_next and line.strip().startswith(("*", "_")):
                skip_next = False
                continue
            skip_next = False
            if name in line:
                skip_next = True
                continue
            kept.append(line)
        times = [int(t_) for t_ in DEEP_LINK_RE.findall("\n".join(kept))]
        start, end = float(brief_section.get("start_s", 0)), float(brief_section.get("end_s", t))
        by_link = any(start <= x <= end for x in times)
        title = str(brief_section.get("title") or "")
        ht, st = _heading_tokens(heading), _heading_tokens(title)
        jaccard = len(ht & st) / len(ht | st) if (ht | st) else 0.0
        by_heading = bool(title) and (title.lower() in heading.lower() or jaccard >= 0.4)
        by_map = str(brief_section.get("heading") or "").strip().lower() in (heading.strip().lower(), common.slugify(heading, 80))
        if not (by_link or by_heading or by_map):
            ok = False
            findings.append(f"{name} ({common.seconds_to_mmss(t)}) sits under '{heading}' but belongs to '{title}' ({common.seconds_to_mmss(start)} to {common.seconds_to_mmss(end)})")
    return ok, findings


def attribution_ok(body: str, channel: str, video_id: str, rights: str,
                   aliases: tuple[str, ...] = (), channel_url: str = "") -> tuple[bool, list[str]]:
    """The creator must be identifiable in the first ATTRIBUTION_WORDS words.

    Accepted: the channel display name, any alias (the author name in own
    mode, the name with its words reversed), or a link to the channel URL.
    """
    findings: list[str] = []
    tokens = list(re.finditer(r"\S+", body))
    cutoff = tokens[ATTRIBUTION_WORDS - 1].end() if len(tokens) >= ATTRIBUTION_WORDS else len(body)
    head = body[:cutoff]
    head_l = head.lower()
    ok = True
    names = [n for n in (channel, *aliases) if n]
    for n in list(names):
        parts = n.split()
        if len(parts) > 1:
            names.append(" ".join(reversed(parts)))
    named = any(n.lower() in head_l for n in names) or (bool(channel_url) and channel_url.rstrip("/") in head)
    if names and not named:
        ok = False
        findings.append(f"creator '{channel}' not named in the first {ATTRIBUTION_WORDS} words")
    if f"youtube.com/watch?v={video_id}" not in head:
        ok = False
        findings.append(f"watch link for {video_id} not in the first {ATTRIBUTION_WORDS} words")
    if rights != "own" and not DISCLOSURE_RE.search(body):
        ok = False
        findings.append("third-party mode: disclosure line missing")
    return ok, findings


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def head_status(url: str) -> int:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with _OPENER.open(req, timeout=HEAD_TIMEOUT) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        return 0


def links_ok(body: str, network: bool) -> tuple[bool, list[str], int]:
    findings: list[str] = []
    ok = True
    urls = []
    for raw in URL_RE.findall(body):
        url = raw.rstrip(".,;:!?*_)")
        if url not in urls:
            urls.append(url)
    for url in urls:
        host = (urllib.parse.urlparse(url).hostname or "").lower()
        if "youtu.be" in host:
            ok = False
            findings.append(f"youtu.be link (redirects): {url}")
        elif "youtube" in host and not any(p.match(url) for p in YT_ALLOWED):
            ok = False
            findings.append(f"YouTube link not in an allowed form (www.youtube.com/watch?v=ID&t=NNs, @handle, channel): {url}")
    checked = 0
    if network:
        for url in urls:
            host = (urllib.parse.urlparse(url).hostname or "").lower()
            if host in SKIP_HOSTS or "youtube-nocookie.com" in host or not url.startswith(("http://", "https://")):
                continue
            if checked >= MAX_LINK_CHECKS:
                findings.append(f"link checks capped at {MAX_LINK_CHECKS}")
                break
            status = head_status(url)
            checked += 1
            if status != 200:
                ok = False
                findings.append(f"link returned {status}: {url}")
    return ok, findings, checked


def voice_flags(body_text: str, vault: Path) -> tuple[int, list[str]]:
    voice = vault / "VOICE.md"
    if not voice.is_file() or voice.is_symlink():
        return 0, []
    fm, voice_body = common.read_note(voice)
    phrases: list[str] = []
    for key in ("taboo_phrases", "taboo", "avoid"):
        value = fm.get(key)
        if isinstance(value, list):
            phrases.extend(str(v) for v in value)
    active = False
    for line in voice_body.splitlines():
        hm = re.match(r"^#{1,6}\s+(.*)$", line)
        if hm:
            active = bool(re.search(r"taboo|avoid|never use|banned|do not use", hm.group(1), re.I))
            continue
        if active:
            im = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.*\S)\s*$", line)
            if im:
                phrases.append(im.group(1))
    findings: list[str] = []
    count = 0
    lower = body_text.lower()
    for phrase in phrases:
        clean = phrase.strip().strip("`\"'").strip()
        clean = re.split(r"\s+\((?:[^)]*)\)\s*$", clean)[0].strip()
        if len(clean) < 3:
            continue
        hits = len(re.findall(r"(?<![a-z0-9])" + re.escape(clean.lower()) + r"(?![a-z0-9])", lower))
        if hits:
            count += hits
            findings.append(f"'{clean}' appears {hits} time(s)")
    return count, findings


# ---------------------------------------------------------------------------
# Note
# ---------------------------------------------------------------------------

def _yn(value: bool | None) -> str:
    if value is None:
        return "not checked"
    return "yes" if value else "no"


def build_note_body(ctx: dict) -> str:
    r = ctx["review"]
    rows = [
        ("Reviewer score", str(r["score"]), f"at least {SCORE_MIN}", r["score"] >= SCORE_MIN),
        ("Blocking", str(r["blocking"]).lower(), "false", not r["blocking"]),
        ("P0 issues", str(r["p0"]), str(P0_MAX), r["p0"] <= P0_MAX),
        ("Preflight gates", str(ctx["preflight"]["passed"]).lower(), "true", ctx["preflight"]["passed"]),
        ("Transcript overlap", f"{ctx['overlap']:.3f}", f"at most {ctx['overlap_max']:.2f} ({ctx['mode']})", ctx["overlap"] <= ctx["overlap_max"]),
        ("Frames in place", str(ctx["frames_ok"]).lower(), "true", ctx["frames_ok"]),
        ("Attribution", str(ctx["attribution"]).lower(), "true", ctx["attribution"]),
        ("Links", str(ctx["links"]).lower(), "true", ctx["links"]),
        ("Verification section", str(ctx["verification"]).lower(), "true", ctx["verification"]),
        ("Voice flags", str(ctx["voice"]), str(VOICE_FLAGS_MAX), ctx["voice"] <= VOICE_FLAGS_MAX),
        ("Thumbnail URL", "not checked" if ctx["thumbnail_ok"] is None else str(ctx["thumbnail_ok"]).lower(), "true (network only)", ctx["thumbnail_ok"]),
    ]
    lines = [
        f"# Evaluation: {ctx['title']}",
        "",
        f"Evaluated on {common.today()} for {ctx['blog_link']} from {ctx['run_link']}. "
        f"Status set to **{ctx['status']}** (score and blocking decide the status; the other rows are findings for the editor).",
        "",
        "## Result",
        "",
        "| Metric | Value | Threshold | Pass |",
        "|---|---|---|---|",
    ]
    for name, value, threshold, passed in rows:
        lines.append(f"| {name} | {value} | {threshold} | {_yn(passed)} |")
    lines += ["", f"Rubric: [[05 Evaluations/pipeline-rubric|pipeline-rubric]]. Overall rubric pass: **{_yn(ctx['rubric_pass'])}**.", ""]
    lines += ["## Reviewer scorecard", ""]
    if r["categories"]:
        lines += ["| Category | Score | Max | Notes |", "|---|---|---|---|"]
        for c in r["categories"]:
            lines.append(f"| {c['name']} | {c['score']} | {c['max']} | {c['note']} |")
    else:
        lines.append("No category table found in review.md." if r["present"] else "review.md is missing.")
    if r["reason"]:
        lines += ["", f"Reviewer decision: `BLOCKING: {str(r['blocking']).lower()}` ({r['reason']})."]
    lines += ["", "## Preflight gates", ""]
    if ctx["preflight"]["gates"]:
        lines += ["| Gate | Name | Passed | Violations |", "|---|---|---|---|"]
        for g in ctx["preflight"]["gates"]:
            v = "; ".join(str(x) for x in g["violations"]) or ""
            lines.append(f"| {g['gate']} | {g['name']} | {_yn(g['passed'])} | {v} |")
    else:
        lines.append("preflight-report.json is missing or empty.")
    lines += ["", "## Findings", ""]
    findings = [f"- [{i['severity']}] {i['text']}" for i in r["issues"]] + [f"- [Metric] {f}" for f in ctx["findings"]]
    lines += findings or ["- No findings."]
    lines += ["", "## Method", ""]
    lines += [
        f"- Overlap: {ctx['overlap_hits']} of {ctx['overlap_total']} article {NGRAM}-grams appear in the transcript ({ctx['transcript_source']}).",
        f"- Links: {ctx['links_checked']} external link(s) HEAD-checked" + ("." if ctx["network"] else " (network off, form checks only)."),
        f"- Frames: {ctx['frames_count']} manifest image(s) with timestamps compared with the brief's section map.",
        f"- Voice: taboo phrases read from the root VOICE.md" + (" (file present)." if ctx["voice_present"] else " (no VOICE.md, 0 flags)."),
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def safe_wikilink(path: Path, alias: str, vault: Path) -> str:
    """Wikilink relative to the vault; falls back to the file name when the path is outside it."""
    try:
        return common.wikilink(path, alias, root=vault)
    except ValueError:
        return common.wikilink(Path(path.name), alias)


def blog_markdown(blog_dir: Path) -> Path | None:
    mds = sorted(p for p in blog_dir.glob("*.md") if p.name != "review.md")
    return mds[0] if len(mds) == 1 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="Vault root (default: auto-detect)")
    parser.add_argument("--run", required=True, help="Run folder (02 Videos/<run>)")
    parser.add_argument("--blog", required=True, help="Blog folder (03 Blogs/<blog>)")
    parser.add_argument("--no-network", action="store_true", help="Skip HEAD checks")
    args = parser.parse_args(argv)

    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    run_dir = Path(args.run).expanduser().resolve()
    blog_dir = Path(args.blog).expanduser().resolve()
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run dir not found: {run_dir}")
    if not blog_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"blog dir not found: {blog_dir}")
    md_path = blog_markdown(blog_dir)
    if md_path is None:
        return common.fail(common.EXIT_INPUT, f"expected exactly one post markdown (besides review.md) in {blog_dir}")
    fm, body = common.read_note(md_path)
    slug = str(fm.get("slug") or md_path.stem)
    network = not args.no_network

    info = common.json_load(run_dir / "source" / "video.info.json", {}) or {}
    run_fm = {}
    if (run_dir / "run.md").is_file():
        run_fm, _ = common.read_note(run_dir / "run.md")
    video_id = str(run_fm.get("video_id") or info.get("id") or run_dir.name.rsplit("-", 1)[-1])
    channel = str(info.get("channel") or info.get("uploader") or run_fm.get("channel") or "")
    rights = fm.get("yt2b_rights") if fm.get("yt2b_rights") in common.RIGHTS else run_fm.get("rights")
    rights = rights if rights in common.RIGHTS else "third-party"
    mode = fm.get("yt2b_mode") if fm.get("yt2b_mode") in common.MODES else run_fm.get("mode")
    mode = mode if mode in common.MODES else "companion"

    review_path = blog_dir / "review.md"
    review = parse_review(review_path.read_text(encoding="utf-8") if review_path.is_file() else None)
    preflight = parse_preflight(blog_dir / "preflight-report.json")
    brief = common.json_load(run_dir / "brief" / "video-brief.json", {}) or {}
    sections = [s for s in (brief.get("sections") or []) if isinstance(s, dict)] if isinstance(brief, dict) else []
    manifest = common.json_load(blog_dir / "images" / "manifest.json", None)

    article_tokens = words(plain_text(body))
    t_tokens, t_source = transcript_tokens(run_dir)
    overlap, hits, total = overlap_ratio(article_tokens, t_tokens)
    frames_ok, frame_findings = frames_in_place(body, manifest if isinstance(manifest, dict) else None, sections)
    author_alias = str(fm.get("author") or "").strip()
    attribution, attr_findings = attribution_ok(
        body, channel, video_id, rights,
        aliases=(author_alias,) if (rights == "own" and author_alias) else (),
        channel_url=str(info.get("channel_url") or run_fm.get("channel_url") or ""))
    links, link_findings, checked = links_ok(body, network)
    verification = bool(VERIFIED_RE.search(body))
    voice, voice_findings = voice_flags(plain_text(body), vault)
    thumbnail_ok: bool | None = None
    thumb_url = str(info.get("thumbnail") or "")
    if network and thumb_url.startswith("https://"):
        thumbnail_ok = head_status(thumb_url) == 200
    findings = list(frame_findings) + attr_findings + link_findings + voice_findings
    if not verification:
        findings.append("no 'What we verified' section (## or ### heading)")
    if not review["present"]:
        findings.append("review.md missing; score 0 and blocking assumed")
    if thumbnail_ok is False:
        findings.append(f"thumbnail URL did not answer 200: {thumb_url}")
    if not review["nonce"] and review["present"]:
        findings.append("review.md has no Nonce line (Gate 4 will reject it)")

    overlap_max = OVERLAP_MAX["expand" if mode == "expand" else "companion"]
    status = "reviewed" if (review["score"] >= SCORE_MIN and not review["blocking"]) else "blocked"
    rubric_pass = (
        review["score"] >= SCORE_MIN and not review["blocking"] and review["p0"] <= P0_MAX
        and preflight["passed"] and overlap <= overlap_max and frames_ok and attribution and links
        and voice <= VOICE_FLAGS_MAX and verification and thumbnail_ok is not False
    )

    eval_dir = common.ensure_dir(vault / common.ROOMS["evaluations"])
    note = eval_dir / f"{common.today()}-{slug}.md"
    existing = {}
    if note.is_file():
        existing, _ = common.read_note(note)
    run_note = run_dir / "run.md"
    ctx = {
        "title": str(fm.get("title") or slug),
        "blog_link": safe_wikilink(md_path, slug, vault),
        "run_link": safe_wikilink(run_note, "run", vault),
        "status": status,
        "review": review,
        "preflight": preflight,
        "overlap": overlap, "overlap_max": overlap_max, "overlap_hits": hits, "overlap_total": total,
        "transcript_source": t_source,
        "mode": mode,
        "frames_ok": frames_ok, "frames_count": len((manifest or {}).get("images", [])) if isinstance(manifest, dict) else 0,
        "attribution": attribution,
        "links": links, "links_checked": checked, "network": network,
        "verification": verification,
        "voice": voice, "voice_present": (vault / "VOICE.md").is_file(),
        "thumbnail_ok": thumbnail_ok,
        "rubric_pass": rubric_pass,
        "findings": findings,
    }
    frontmatter = {
        "type": common.NOTE_TYPES["evaluation"],
        "blog": ctx["blog_link"],
        "run": ctx["run_link"],
        "score": int(review["score"]),
        "blocking": bool(review["blocking"]),
        "p0": int(review["p0"]),
        "gates_passed": bool(preflight["passed"]),
        "overlap_ratio": round(overlap, 4),
        "frames_in_place": bool(frames_ok),
        "attribution_ok": bool(attribution),
        "links_ok": bool(links),
        "verification_section": bool(verification),
        "thumbnail_ok": "" if thumbnail_ok is None else bool(thumbnail_ok),
        "voice_flags": int(voice),
        "rubric_pass": bool(rubric_pass),
        "created": str(existing.get("created") or common.today()),
        "updated": common.today(),
        "tags": ["yt2b", "evaluation"],
    }
    common.write_note(note, frontmatter, build_note_body(ctx))
    binder_status = "complete" if status == "reviewed" else "in-progress"
    common.update_note(md_path, {
        "yt2b_score": int(review["score"]),
        "yt2b_status": status,
        "binder-status": binder_status,
        "binder-type": "article",
    })

    for f in findings:
        common.warn(f"finding: {f}")
    common.emit({
        "score": int(review["score"]),
        "blocking": bool(review["blocking"]),
        "p0": int(review["p0"]),
        "gates_passed": bool(preflight["passed"]),
        "overlap_ratio": round(overlap, 4),
        "frames_in_place": bool(frames_ok),
        "attribution_ok": bool(attribution),
        "links_ok": bool(links),
        "thumbnail_ok": thumbnail_ok,
        "verification_section": bool(verification),
        "voice_flags": int(voice),
        "status": status,
        "rubric_pass": bool(rubric_pass),
        "evaluation_note": str(note),
        "findings": findings,
    })
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
