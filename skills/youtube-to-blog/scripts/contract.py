#!/usr/bin/env python3
"""Local, deterministic policy checks for one YouTube to Blog article.

This module does not call the network or a model. It is shared by deliver.py
and pipeline.py so the same rules guard delivery and final state changes.
"""

from __future__ import annotations

import re
import ipaddress
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import yt2b_common as common

PLACEHOLDER_HOSTS = {
    "example.com",
    "www.example.com",
    "example.org",
    "www.example.org",
    "example.net",
    "www.example.net",
    "localhost",
    "127.0.0.1",
}
WIKILINK_RE = re.compile(r"^\[\[([^]|]+)(?:\|[^]]*)?\]\]$")
STRATEGY_SLUG_RE = re.compile(r"^\s*-?\s*\*\*Slug\*\*\s*:\s*`?([a-z0-9][a-z0-9-]*)`?\s*$", re.I | re.M)
STRATEGY_HEADING_RE = re.compile(r"^###\s+([A-Za-z0-9_.-]+)(?:\s*:|\s|$)", re.M)
IFRAME_RE = re.compile(r"<iframe\b[^>]*>", re.I | re.S)
IFRAME_SRC_RE = re.compile(r"\bsrc\s*=\s*['\"]([^'\"]+)['\"]", re.I)
VIDEO_FIGURE_RE = re.compile(r"<figure\b[^>]*\bclass\s*=\s*['\"][^'\"]*\bvideo-embed\b[^'\"]*['\"][^>]*>.*?</figure>", re.I | re.S)


def wikilink_target(value) -> str:
    """Return a normalized vault-relative target from an Obsidian wikilink."""
    match = WIKILINK_RE.match(str(value or "").strip())
    target = match.group(1).strip() if match else str(value or "").strip()
    return target[:-3] if target.endswith(".md") else target


def resolve_wikilink(vault: Path, value, default_name: str | None = None) -> Path | None:
    target = wikilink_target(value)
    if not target:
        return None
    path = Path(target)
    path = path if path.is_absolute() else vault / path
    if path.suffix:
        return path.resolve()
    as_note = path.with_suffix(".md")
    if as_note.is_file():
        return as_note.resolve()
    if path.is_dir() and default_name:
        return (path / default_name).resolve()
    return as_note.resolve()


def post_path(blog: Path) -> Path:
    posts = [p for p in blog.glob("*.md") if p.name != "review.md"]
    if len(posts) != 1:
        raise ValueError(f"expected exactly one post markdown in {blog}, found {len(posts)}")
    return posts[0]


def run_for_blog(vault: Path, blog: Path, explicit: Path | None = None) -> Path:
    if explicit is not None:
        run = explicit.resolve()
        if not (run / "run.md").is_file():
            raise ValueError(f"run note missing: {run / 'run.md'}")
        return run
    fm, _ = common.read_note(post_path(blog))
    run_note = resolve_wikilink(vault, fm.get("yt2b_video"), "run.md")
    if run_note is None or not run_note.is_file():
        raise ValueError("post yt2b_video does not resolve to a run note")
    return run_note.parent


def valid_site_url(value) -> bool:
    try:
        parsed = urlparse(str(value or "").strip())
        host = str(parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in ("http", "https") or not host or parsed.username or parsed.password:
            return False
        if parsed.query or parsed.fragment or any(ch.isspace() for ch in parsed.netloc):
            return False
        if host in PLACEHOLDER_HOSTS or any(host.endswith("." + h) for h in PLACEHOLDER_HOSTS):
            return False
        if host.endswith((".test", ".invalid", ".localhost", ".example", ".local")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return "." in host
    except ValueError:
        return False


def setup_violations(vault: Path) -> list[str]:
    settings = common.load_settings(vault)
    failures: list[str] = []
    if not str(settings.get("author") or "").strip():
        failures.append("Settings author is empty")
    if not valid_site_url(settings.get("site_url")):
        failures.append("Settings site_url is empty, local, or a placeholder")
    for name in ("BRAND.md", "VOICE.md"):
        if not (vault / name).is_file():
            failures.append(f"{name} is missing")
    return failures


def approval_tags(kind: str, status: str) -> list[str]:
    return ["yt2b", "format/approval", f"approval/{kind}", f"decision/{status}"]


def evaluation_tags(passed: bool) -> list[str]:
    return ["yt2b", "format/evaluation", "stage/done" if passed else "stage/blocked"]


def approval_notes(vault: Path, run: Path, blog: Path | None = None, kind: str | None = None) -> list[tuple[Path, dict, str]]:
    wanted_run = (run / "run.md").resolve()
    wanted_blog = post_path(blog).resolve() if blog is not None else None
    out: list[tuple[Path, dict, str]] = []
    folder = vault / common.ROOMS["approvals_queue"]
    for note in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        try:
            fm, body = common.read_note(note)
        except Exception:
            continue
        if fm.get("type") != common.NOTE_TYPES["approval"]:
            continue
        if kind and fm.get("kind") != kind:
            continue
        target = resolve_wikilink(vault, fm.get("run"), "run.md")
        if target != wanted_run:
            continue
        if wanted_blog is not None:
            blog_target = resolve_wikilink(vault, fm.get("blog"))
            if blog_target != wanted_blog:
                continue
        out.append((note, fm, body))
    return out


def approved(vault: Path, run: Path, kind: str, blog: Path | None = None, selected: str | None = None) -> bool:
    for _note, fm, _body in approval_notes(vault, run, blog, kind):
        choices = [str(item) for item in (fm.get("selected") or [])]
        if fm.get("status") == "approved" and (selected is None or selected in choices):
            return True
    return False


def strategy_slugs(run: Path) -> list[str]:
    path = run / "strategy.md"
    if not path.is_file():
        return []
    _fm, body = common.read_note(path)
    return STRATEGY_SLUG_RE.findall(body)


def strategy_angles(run: Path) -> dict[str, str]:
    """Map strategy angle ids, such as blog-1, to their declared slugs."""
    path = run / "strategy.md"
    if not path.is_file():
        return {}
    _fm, body = common.read_note(path)
    headings = list(STRATEGY_HEADING_RE.finditer(body))
    angles: dict[str, str] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        slug = STRATEGY_SLUG_RE.search(body[heading.end():end])
        if slug:
            angles[heading.group(1)] = slug.group(1)
    return angles


def approved_strategy_ids(vault: Path, run: Path) -> list[str]:
    for _note, fm, _body in reversed(approval_notes(vault, run, kind="strategy")):
        if fm.get("status") == "approved":
            return [str(item) for item in (fm.get("selected") or [])]
    return []


def selected_strategy_slugs(vault: Path, run: Path) -> list[str]:
    angles = strategy_angles(run)
    return [angles[item] for item in approved_strategy_ids(vault, run) if item in angles]


def strategy_approval_selected(vault: Path, run: Path) -> bool:
    return any(
        fm.get("status") == "approved" and bool(fm.get("selected"))
        for _note, fm, _body in approval_notes(vault, run, kind="strategy")
    )


def auto_strategy(vault: Path, run: Path) -> bool:
    for _note, fm, body in approval_notes(vault, run, kind="strategy"):
        if fm.get("status") == "approved" and re.search(r"\bauto\s*:\s*(?:true|yes|current request)\b", body, re.I):
            return True
    return False


def provider_authorized(run: Path) -> bool:
    note = run / "run.md"
    if not note.is_file():
        return False
    _fm, body = common.read_note(note)
    return bool(re.search(r"provider authorization:\s*current\s+(?:analyze|full)\s+request", body, re.I))


def review_high_findings(blog: Path) -> list[str]:
    review = blog / "review.md"
    if not review.is_file():
        return []
    severity = ""
    findings: list[str] = []
    for line in review.read_text(encoding="utf-8", errors="replace").splitlines():
        heading = re.match(r"^#{2,4}\s+(Critical|High|Medium|Low)\b", line, re.I)
        if heading:
            severity = heading.group(1).lower()
            continue
        if re.match(r"^#{1,4}\s", line):
            severity = ""
            continue
        item = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if item and severity in ("critical", "high"):
            text = item.group(1).strip()
            if not re.match(r"^(?:\(?none\)?(?:[.\s]|$)|no\s+(?:critical|p0|issues?)\b|n/?a\b)", text, re.I):
                findings.append(f"{severity}: {text}")
    return findings


def editorial_waiver(vault: Path, run: Path, blog: Path) -> bool:
    return approved(vault, run, "editorial", blog, "accept-high")


def body_word_count(body: str) -> int:
    text = re.sub(r"```.*?```", " ", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\{#[^}]*\}", " ", text)
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def post_contract_sha256(path: Path) -> str:
    """Digest article content and release-relevant frontmatter only."""
    fm, body = common.read_note(path)
    keys = ("title", "description", "date", "author", "slug", "tags", "lang", "canonical",
            "yt2b_video", "yt2b_rights", "yt2b_mode", "yt2b_template", "word-count-goal")
    payload = {key: fm.get(key) for key in keys}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str) + "\n" + body
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def report_word_count(report: dict | None) -> int | None:
    for gate in (report or {}).get("gates") or []:
        if not isinstance(gate, dict):
            continue
        for key in ("actual_word_count", "word_count", "actual"):
            value = gate.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return int(value)
        details = gate.get("details")
        if isinstance(details, dict):
            value = details.get("actual_word_count") or details.get("word_count")
            if isinstance(value, (int, float)) and value > 0:
                return int(value)
    return None


def pre_write_violations(vault: Path, run: Path, blog: Path) -> list[str]:
    failures = setup_violations(vault)
    if not (run / "brief" / "video-brief.json").is_file():
        failures.append("video brief is missing")
    if not (run / "strategy.md").is_file():
        failures.append("strategy is missing")
    if not strategy_approval_selected(vault, run):
        failures.append("strategy approval is not approved with a selected angle")
    settings = common.load_settings(vault)
    if bool(settings.get("pause_for_outline")) and not auto_strategy(vault, run):
        if not approved(vault, run, "outline", blog):
            failures.append("outline approval is required and is not approved")
    if not provider_authorized(run):
        failures.append("current analyze or full provider authorization is not recorded in the run log")
    return failures


def contract_gate(vault: Path, run: Path, blog: Path, report: dict | None = None) -> dict:
    violations = pre_write_violations(vault, run, blog)
    warnings: list[str] = []
    post = post_path(blog)
    fm, body = common.read_note(post)
    settings = common.load_settings(vault)
    slug = str(fm.get("slug") or "").strip()
    if not slug or slug != post.stem:
        violations.append("post slug must match the markdown file name")
    if blog.name.split(" ", 1)[-1] != post.stem:
        violations.append("blog folder suffix must match the post file name")
    slugs = strategy_slugs(run)
    if post.stem not in slugs:
        violations.append("post slug is not one of the strategy slugs")
    selected_ids = approved_strategy_ids(vault, run)
    selected_slugs = selected_strategy_slugs(vault, run)
    if selected_ids and len(selected_slugs) != len(selected_ids):
        violations.append("an approved strategy option does not map to a declared angle slug")
    elif selected_slugs and post.stem not in selected_slugs:
        violations.append("post slug is not one of the approved strategy angles")

    canonical = str(fm.get("canonical") or "").strip()
    if not valid_site_url(canonical):
        violations.append("post canonical is empty, local, or a placeholder")
    site_url = str(settings.get("site_url") or "").rstrip("/")
    if valid_site_url(site_url) and canonical and not canonical.startswith(site_url + "/"):
        violations.append("post canonical is outside Settings site_url")

    run_fm, _run_body = common.read_note(run / "run.md")
    video_id = str(run_fm.get("video_id") or "")
    iframes = IFRAME_RE.findall(body)
    figures = VIDEO_FIGURE_RE.findall(body)
    if len(iframes) != 1 or len(figures) != 1:
        violations.append("post must contain exactly one video-embed figure and one iframe")
    elif iframes[0] not in figures[0]:
        violations.append("the iframe must be inside the video-embed figure")
    if len(iframes) == 1:
        source = IFRAME_SRC_RE.search(iframes[0])
        wanted = f"https://www.youtube-nocookie.com/embed/{video_id}"
        if source is None or source.group(1) != wanted:
            violations.append("iframe source must be the matching youtube-nocookie embed URL")
    if "\u2014" in body or "\u2013" in body:
        violations.append("post contains an em dash or en dash")

    goal = fm.get("word-count-goal")
    try:
        goal_i = int(goal)
    except (TypeError, ValueError):
        goal_i = 0
    actual = report_word_count(report) or body_word_count(body)
    try:
        block_pct = max(1, int(settings.get("word_count_tolerance_percent") or 30))
    except (TypeError, ValueError):
        block_pct = 30
    if goal_i > 0:
        drift = abs(actual - goal_i) * 100.0 / goal_i
        if drift > block_pct:
            violations.append(f"word count {actual} differs from goal {goal_i} by {drift:.1f} percent")
        elif drift > block_pct / 2:
            warnings.append(f"word count {actual} differs from goal {goal_i} by {drift:.1f} percent")

    review_path = blog / "review.md"
    if not review_path.is_file():
        violations.append("review.md is missing")
    findings = review_high_findings(blog)
    critical = [finding for finding in findings if finding.startswith("critical:")]
    high = [finding for finding in findings if finding.startswith("high:")]
    if critical:
        violations.append("review has unresolved Critical findings; these cannot be waived")
    if high and not editorial_waiver(vault, run, blog):
        violations.append("review has unresolved Critical or High findings and no approved editorial waiver")
    if critical or high:
        warnings.extend(findings[:8])

    return {
        "gate": 6,
        "name": "YouTube to Blog Contract",
        "passed": not violations,
        "violations": violations,
        "warnings": warnings,
        "actual_word_count": actual,
        "word_count_goal": goal_i,
        "post_sha256": post_contract_sha256(post),
        "review_sha256": file_sha256(review_path) if review_path.is_file() else "",
    }
