#!/usr/bin/env python3
"""Approval notes for the youtube-to-blog pipeline (04 Approvals/queue).

Commands:
  create   write a new approval note (strategy | outline | image | editorial)
  check    read the decision: status property, ticked options, answers, expiry
  set      record a decision (status, selected options, decision text)

Note names: strategy `<date>-<videoId>-strategy.md`; outline
`<date>-<videoId>-outline[-<blog-slug>].md` (slug when --blog is given);
image and editorial `<date>-<videoId>-<kind>-<blog-slug>.md` (--blog required).

Approval is granted only when the note's `status` property is `approved`.
A ticked option box on its own is never approval. A request that passes its
`expires` time while still `requested` is reported (and marked) as expired;
the orchestrator must ask again with a fresh note.

Exit codes: 0 ok, 1 failure, 2 invalid input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402
import contract  # noqa: E402
import make_run_note  # noqa: E402

DEFAULT_EXPIRES_HOURS = 48
OPTION_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$")
QUESTION_RE = re.compile(r"^\s*-\s*\*\*([A-Za-z0-9_.-]+)\*\*\s*:\s*(.*?)\s*$")
ANSWER_RE = re.compile(r"^\s*answer:\s*(.*?)\s*$")
ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


# ---------------------------------------------------------------------------
# Local helpers (kept here on purpose; yt2b_common is shared and frozen)
# ---------------------------------------------------------------------------

def _iso(value) -> str:
    """Frontmatter dates may come back as date/datetime objects through PyYAML."""
    if isinstance(value, dt.datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value or "")


def _parse_dt(value) -> dt.datetime | None:
    if isinstance(value, dt.datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.fromisoformat(text).replace(tzinfo=None)
    except ValueError:
        return None


def parse_pairs(raw: str) -> list[tuple[str, str]]:
    """Parse "id=label;id=label" into ordered pairs."""
    pairs: list[tuple[str, str]] = []
    for part in (raw or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"expected id=label, got {part!r}")
        key, value = part.split("=", 1)
        key, value = key.strip(), value.strip()
        if not ID_RE.match(key):
            raise ValueError(f"invalid option id {key!r}")
        pairs.append((key, value))
    return pairs


def video_id_for_run(run_dir: Path) -> str:
    run_note = run_dir / "run.md"
    if run_note.is_file():
        fm, _ = common.read_note(run_note)
        if fm.get("video_id"):
            return str(fm["video_id"])
    info = common.json_load(run_dir / "source" / "video.info.json", {}) or {}
    if info.get("id"):
        return str(info["id"])
    return run_dir.name.rsplit("-", 1)[-1]


def safe_wikilink(path: Path, alias: str, vault: Path) -> str:
    """Wikilink relative to the vault; falls back to the file name when the path is outside it."""
    try:
        return common.wikilink(path, alias, root=vault)
    except ValueError:
        return common.wikilink(Path(path.name), alias)


def blog_slug(blog_dir: Path) -> str:
    mds = [p for p in blog_dir.glob("*.md") if p.name != "review.md"]
    if len(mds) == 1:
        fm, _ = common.read_note(mds[0])
        return str(fm.get("slug") or mds[0].stem)
    m = re.match(r"^\d{4}-\d{2}-\d{2}\s+(.+)$", blog_dir.name)
    return common.slugify(m.group(1) if m else blog_dir.name, 60)


def note_name(video_id: str, kind: str, slug: str | None) -> str:
    base = common.approval_note_name(video_id, kind)[:-3]
    if slug and kind in ("image", "outline", "editorial"):
        base = f"{base}-{slug}"
    return base + ".md"


def _section(sections: list[tuple[str, str]], heading: str) -> str:
    for name, content in sections:
        if name.strip().lower() == heading.lower():
            return content
    return ""


def parse_options(content: str) -> list[dict]:
    options = []
    for line in content.splitlines():
        m = OPTION_RE.match(line)
        if m:
            options.append({"id": m.group(2), "label": m.group(3), "ticked": m.group(1).lower() == "x"})
    return options


def parse_answers(content: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    key = None
    in_answer = False
    for line in content.splitlines():
        qm = QUESTION_RE.match(line)
        if qm:
            key = qm.group(1)
            answers.setdefault(key, "")
            in_answer = False
            continue
        am = ANSWER_RE.match(line)
        if am and key:
            answers[key] = am.group(1).strip()
            in_answer = True
            continue
        if in_answer and key and line.startswith((" ", "\t")) and line.strip():
            answers[key] = (answers[key] + " " + line.strip()).strip()
        elif not line.strip():
            in_answer = False
    return answers


def read_state(note: Path) -> tuple[dict, str, dict]:
    fm, body = common.read_note(note)
    _, sections = common.split_sections(body)
    options = parse_options(_section(sections, "Options"))
    answers = parse_answers(_section(sections, "Questions"))
    status = str(fm.get("status") or "requested")
    expires = _parse_dt(fm.get("expires"))
    expired = status in ("requested", "expired") and expires is not None and dt.datetime.now() > expires
    state = {
        "status": status,
        "selected": [o["id"] for o in options if o["ticked"]],
        "options": options,
        "answers": answers,
        "expired": expired,
        "kind": fm.get("kind"),
    }
    return fm, body, state


def tick_options(body: str, ids: list[str]) -> str:
    wanted = set(ids)
    out = []
    for line in body.splitlines():
        m = OPTION_RE.match(line)
        if m and m.group(2) in wanted:
            line = f"- [x] {m.group(2)}: {m.group(3)}"
        out.append(line)
    return "\n".join(out) + ("\n" if body.endswith("\n") else "")


def refresh_run(vault: Path, fm: dict) -> None:
    """Refresh approval backlinks on the related run note."""
    run_note = contract.resolve_wikilink(vault, fm.get("run"), "run.md")
    if run_note is not None and run_note.is_file():
        make_run_note.update_run_note(vault, run_note.parent)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_create(args, vault: Path) -> int:
    kind = args.kind
    if kind not in common.APPROVAL_KINDS:
        return common.fail(common.EXIT_INPUT, f"kind must be one of {common.APPROVAL_KINDS}")
    run_dir = Path(args.run).expanduser().resolve()
    if not run_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"run dir not found: {run_dir}")
    request_file = Path(args.request_file).expanduser()
    if not request_file.is_file():
        return common.fail(common.EXIT_INPUT, f"request file not found: {request_file}")
    try:
        options = parse_pairs(args.options or "")
        questions = parse_pairs(args.questions or "")
    except ValueError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    blog_dir = Path(args.blog).expanduser().resolve() if args.blog else None
    if blog_dir is not None and not blog_dir.is_dir():
        return common.fail(common.EXIT_INPUT, f"blog dir not found: {blog_dir}")
    if kind in ("image", "editorial") and blog_dir is None:
        return common.fail(common.EXIT_INPUT, f"--blog is required for --kind {kind}")
    slug = blog_slug(blog_dir) if blog_dir is not None else None

    video_id = video_id_for_run(run_dir)
    queue_dir = vault / common.ROOMS["approvals_queue"]
    note = queue_dir / note_name(video_id, kind, slug)
    if note.exists():
        existing_fm, _, state = read_state(note)
        refresh_run(vault, existing_fm)
        common.warn(f"approval note exists, left untouched: {note}")
        common.emit({"note": str(note), "status": state["status"], "kind": kind, "created": False,
                     "selected": state["selected"], "expired": state["expired"]})
        return common.EXIT_OK

    now = dt.datetime.now().replace(microsecond=0)
    hours = args.expires_hours if args.expires_hours is not None else DEFAULT_EXPIRES_HOURS
    expires = now + dt.timedelta(hours=float(hours))
    run_note = run_dir / "run.md"
    run_link = safe_wikilink(run_note if run_note.exists() else run_dir / "run.md", "run", vault)
    blog_link = ""
    if blog_dir is not None:
        mds = [p for p in blog_dir.glob("*.md") if p.name != "review.md"]
        target = mds[0] if len(mds) == 1 else blog_dir
        blog_link = safe_wikilink(target, blog_dir.name, vault)

    frontmatter = {
        "type": common.NOTE_TYPES["approval"],
        "kind": kind,
        "status": "requested",
        "run": run_link,
        "blog": blog_link,
        "requested": now.isoformat(),
        "decided": "",
        "expires": expires.isoformat(),
        "selected": [],
        "cost_estimate": args.cost_estimate or "",
        "created": common.today(),
        "updated": common.today(),
        "tags": contract.approval_tags(kind, "requested"),
    }
    request_text = request_file.read_text(encoding="utf-8").strip()
    option_lines = "\n".join(f"- [ ] {oid}: {label}" for oid, label in options) or "- [ ] proceed: Proceed as requested"
    question_lines = "\n".join(f"- **{key}**: {text}\n  answer:" for key, text in questions)
    sections = [
        ("Request", request_text),
        ("Options", option_lines),
        ("Questions", question_lines or "(none)"),
        ("Decision", ""),
    ]
    body = common.join_sections(f"# {args.title}\n", sections)
    common.write_note(note, frontmatter, body)
    refresh_run(vault, frontmatter)
    common.emit({"note": str(note), "status": "requested", "kind": kind, "created": True,
                 "options": [oid for oid, _ in options], "questions": [key for key, _ in questions],
                 "expires": expires.isoformat()})
    return common.EXIT_OK


def cmd_check(args, vault: Path) -> int:
    note = Path(args.note).expanduser().resolve()
    if not note.is_file():
        return common.fail(common.EXIT_INPUT, f"approval note not found: {note}")
    fm, body, state = read_state(note)
    if fm.get("type") != common.NOTE_TYPES["approval"]:
        return common.fail(common.EXIT_INPUT, f"not an approval note: {note}")
    updates: dict = {}
    if state["expired"] and state["status"] == "requested":
        updates["status"] = "expired"
        state["status"] = "expired"
    if list(fm.get("selected") or []) != state["selected"]:
        updates["selected"] = state["selected"]
    updates["tags"] = contract.approval_tags(str(fm.get("kind") or "approval"), state["status"])
    if updates:
        common.update_note(note, updates)
        fm.update(updates)
    refresh_run(vault, fm)
    common.emit({
        "note": str(note),
        "status": state["status"],
        "approved": state["status"] == "approved",
        "selected": state["selected"],
        "answers": state["answers"],
        "expired": state["expired"],
        "kind": state["kind"],
    })
    return common.EXIT_OK


def cmd_set(args, vault: Path) -> int:
    note = Path(args.note).expanduser().resolve()
    if not note.is_file():
        return common.fail(common.EXIT_INPUT, f"approval note not found: {note}")
    if args.status not in common.APPROVAL_STATUSES:
        return common.fail(common.EXIT_INPUT, f"status must be one of {common.APPROVAL_STATUSES}")
    fm, body, state = read_state(note)
    if fm.get("type") != common.NOTE_TYPES["approval"]:
        return common.fail(common.EXIT_INPUT, f"not an approval note: {note}")
    select = [s.strip() for s in (args.select or "").split(",") if s.strip()]
    for item in args.selected or []:
        select.extend(s.strip() for s in str(item).split(",") if s.strip())
    known = {o["id"] for o in state["options"]}
    unknown = [s for s in select if s not in known]
    if unknown:
        return common.fail(common.EXIT_INPUT, f"unknown option id(s): {unknown}; known: {sorted(known)}")
    if select:
        body = tick_options(body, select)
    if args.decision:
        preamble, sections = common.split_sections(body)
        new_sections = []
        found = False
        for heading, content in sections:
            if heading.strip().lower() == "decision":
                found = True
                if args.decision.strip() not in content:
                    content = (content.rstrip() + "\n\n" + args.decision.strip()).strip()
            new_sections.append((heading, content))
        if not found:
            new_sections.append(("Decision", args.decision.strip()))
        body = common.join_sections(preamble, new_sections)
    options = parse_options(_section(common.split_sections(body)[1], "Options"))
    selected = [o["id"] for o in options if o["ticked"]]
    updates = {"status": args.status, "selected": selected,
               "tags": contract.approval_tags(str(fm.get("kind") or "approval"), args.status)}
    if args.status in ("approved", "declined"):
        updates["decided"] = dt.datetime.now().replace(microsecond=0).isoformat()
    common.update_note(note, updates, body)
    fm.update(updates)
    refresh_run(vault, fm)
    common.emit({"note": str(note), "status": args.status, "selected": selected,
                 "decided": updates.get("decided", _iso(fm.get("decided")))})
    return common.EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="Vault root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create", help="Write a new approval note")
    c.add_argument("--kind", required=True, choices=common.APPROVAL_KINDS)
    c.add_argument("--run", required=True, help="Run folder (02 Videos/<run>)")
    c.add_argument("--blog", help="Blog folder (03 Blogs/<blog>)")
    c.add_argument("--title", required=True)
    c.add_argument("--request-file", required=True, help="Markdown file with the request text")
    c.add_argument("--options", default="", help='"id=label;id=label"')
    c.add_argument("--questions", default="", help='"key=question;key=question"')
    c.add_argument("--expires-hours", type=float, default=None)
    c.add_argument("--cost-estimate", "--cost", dest="cost_estimate", default="", help="Cost estimate text (Banana image approvals)")

    k = sub.add_parser("check", help="Read the decision state")
    k.add_argument("note")

    s = sub.add_parser("set", help="Record a decision")
    s.add_argument("note")
    s.add_argument("--status", required=True, choices=common.APPROVAL_STATUSES)
    s.add_argument("--decision", default="")
    s.add_argument("--selected", action="append", default=[], help="Option id to tick (repeatable)")
    s.add_argument("--select", default="", help="Comma separated option ids to tick")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        if args.command == "create":
            return common.fail(common.EXIT_INPUT, str(exc))
        vault = Path.cwd()
    try:
        if args.command == "create":
            return cmd_create(args, vault)
        if args.command == "check":
            return cmd_check(args, vault)
        return cmd_set(args, vault)
    except Exception as exc:  # pragma: no cover - defensive
        return common.fail(common.EXIT_FAIL, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
