#!/usr/bin/env python3
"""Queue notes for the youtube-to-blog pipeline (01 Queue/<date>-<videoId>.md).

Usage:
    queue.py [--vault PATH] add URL [--rights own|third-party|ask] [--mode companion|expand] [--priority N] [--note TEXT]
    queue.py [--vault PATH] list [--status S]
    queue.py [--vault PATH] next
    queue.py [--vault PATH] set NOTE_PATH --status S [--run RUN_DIR] [--error TEXT]
    queue.py [--vault PATH] import-inbox

Priority 1 is the most urgent, 3 is the default. "next" returns the most
urgent, oldest queued note. "import-inbox" reads the "## Inbox" section of
00 Home/Home.md (plain lines or lines inside a callout), queues every unticked
task line of the form "- [ ] <url> [own|third-party] [companion|expand] [note]"
and rewrites it as "- [x] <url> -> [[01 Queue/<note>|queued]]".
One JSON object on stdout; exit 0 ok, 1 failure, 2 invalid input.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

RIGHTS_CHOICES = common.RIGHTS + ("ask",)
INBOX_HEADING = re.compile(r"^#{1,6}\s+Inbox\s*$", re.I)
INBOX_CALLOUT = re.compile(r"^>\s*\[![^\]]+\][+-]?\s*Inbox\s*$", re.I)
ANY_HEADING = re.compile(r"^#{1,6}\s+\S")
TASK_LINE = re.compile(r"^(?P<prefix>\s*(?:>\s*)*)-\s\[(?P<mark>[ xX])\]\s+(?P<rest>.*?)\s*$")
URL_TOKEN = re.compile(r"https?://[^\s<>()\[\]]+")


def queue_dir(vault: Path) -> Path:
    return vault / common.ROOMS["queue"]


def find_note(vault: Path, video_id: str) -> Path | None:
    """Existing queue note for a video id, whatever its date."""
    hits = sorted(queue_dir(vault).glob(f"*-{video_id}.md")) if queue_dir(vault).is_dir() else []
    return hits[0] if hits else None


def resolve_note(vault: Path, note_path: str) -> Path:
    path = Path(note_path).expanduser()
    return path if path.is_absolute() else vault / path


def queue_tags(status: str, rights: str) -> list[str]:
    """Structural tags for a governed queue item, never for a discovery item."""
    stage = {
        "queued": "queue",
        "running": "fetched",
        "done": "done",
        "failed": "blocked",
    }.get(status, "queue")
    tags = ["yt2b", f"stage/{stage}", "format/video", "source/youtube"]
    if rights in common.RIGHTS:
        tags.append(f"rights/{rights}")
    return tags


def note_record(vault: Path, path: Path) -> dict:
    fm, _ = common.read_note(path)
    record = {"path": str(path.resolve()), "name": path.stem}
    for key in ("video_id", "video_url", "rights", "mode", "priority", "status", "run", "note", "created", "updated"):
        record[key] = fm.get(key, "")
    return record


def create_note(vault: Path, url: str, rights: str, mode: str, priority: int, note_text: str) -> tuple[Path, bool]:
    """Create the queue note for a URL; return (path, created). Existing ids are reused."""
    video_id = common.youtube_video_id(url)
    if not video_id:
        raise ValueError(f"not a YouTube video URL: {url}")
    existing = find_note(vault, video_id)
    if existing:
        return existing, False
    watch = common.watch_url(video_id)
    frontmatter = {
        "type": common.NOTE_TYPES["queue"],
        "video_url": watch,
        "video_id": video_id,
        "rights": rights,
        "mode": mode,
        "priority": int(priority),
        "status": "queued",
        "run": "",
        "note": note_text or "",
        "source_notes": [],
        "discovered_via": "cli",
        "created": common.today(),
        "updated": common.today(),
        "tags": queue_tags("queued", rights),
    }
    body = f"[Watch on YouTube]({watch})"
    if note_text:
        body += f" {note_text}"
    path = queue_dir(vault) / f"{common.today()}-{video_id}.md"
    common.write_note(path, frontmatter, body + "\n")
    return path, True


def set_status(vault: Path, note_path: Path, status: str, run_dir: str | None = None, error: str | None = None) -> Path:
    """Update status, run link and an optional failure line on a queue note."""
    if status not in common.QUEUE_STATUSES:
        raise ValueError(f"status must be one of {', '.join(common.QUEUE_STATUSES)}")
    if not note_path.is_file():
        raise FileNotFoundError(f"queue note not found: {note_path}")
    updates: dict = {"status": status}
    if run_dir:
        run = Path(run_dir)
        run_abs = run if run.is_absolute() else vault / run
        updates["run"] = common.wikilink(common.rel(run_abs, vault) + "/run.md", run_abs.name)
    fm, body = common.read_note(note_path)
    if error:
        line = f"> [!failure] {error.strip()}"
        if line not in body:
            body = body.rstrip("\n") + f"\n\n{line}\n"
    fm.update(updates)
    fm["tags"] = queue_tags(status, str(fm.get("rights") or "ask"))
    fm["updated"] = common.today()
    common.write_note(note_path, fm, body)
    return note_path


def queued_notes(vault: Path, status: str | None = None) -> list[Path]:
    notes = common.list_notes(queue_dir(vault), common.NOTE_TYPES["queue"])
    if status:
        notes = [n for n in notes if common.read_note(n)[0].get("status") == status]
    return notes


def pick_next(vault: Path) -> Path | None:
    """Most urgent (lowest priority number), then oldest created, then name."""
    candidates = []
    for path in queued_notes(vault, "queued"):
        fm, _ = common.read_note(path)
        try:
            priority = int(fm.get("priority", 3))
        except (TypeError, ValueError):
            priority = 3
        candidates.append((priority, str(fm.get("created", "")), path.name, path))
    return sorted(candidates)[0][3] if candidates else None


def parse_inbox_line(line: str) -> dict | None:
    """Return {prefix, done, url, rights, mode, note} for a task line, else None."""
    m = TASK_LINE.match(line)
    if not m:
        return None
    rest = m.group("rest")
    url_match = URL_TOKEN.search(rest)
    if not url_match:
        return None
    url = url_match.group(0).rstrip(".,;")
    words = (rest[: url_match.start()] + " " + rest[url_match.end():]).split()
    rights = mode = ""
    note_words = []
    for word in words:
        token = word.strip("[](),").lower()
        if token in RIGHTS_CHOICES and not rights:
            rights = token
        elif token in common.MODES and not mode:
            mode = token
        else:
            note_words.append(word)
    return {"prefix": m.group("prefix"), "done": m.group("mark").lower() == "x", "url": url,
            "rights": rights, "mode": mode, "note": " ".join(note_words).strip(" -:")}


def inbox_line_indexes(lines: list[str]) -> list[int]:
    """Indexes of lines inside the Inbox section (heading form) or Inbox callout."""
    indexes: list[int] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if INBOX_HEADING.match(line):
            i += 1
            while i < len(lines) and not ANY_HEADING.match(lines[i]):
                indexes.append(i)
                i += 1
            continue
        if INBOX_CALLOUT.match(line):
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                indexes.append(i)
                i += 1
            continue
        i += 1
    return indexes


def import_inbox(vault: Path, settings: dict) -> dict:
    home = vault / common.HOME_NOTE
    if not home.is_file():
        raise FileNotFoundError(f"missing {home}")
    text = home.read_text(encoding="utf-8")
    lines = text.split("\n")
    result = {"created": [], "existing": [], "skipped": [], "home": str(home)}
    indexes = inbox_line_indexes(lines)
    if not indexes:
        result["skipped"].append({"line": "", "reason": "no '## Inbox' section or Inbox callout in Home.md"})
    for i in indexes:
        parsed = parse_inbox_line(lines[i])
        if parsed is None or parsed["done"]:
            continue
        if not common.youtube_video_id(parsed["url"]):
            result["skipped"].append({"line": lines[i].strip(), "reason": "not a YouTube video URL"})
            continue
        path, created = create_note(vault, parsed["url"], parsed["rights"] or settings["default_rights"],
                                    parsed["mode"] or settings["default_mode"], 3, parsed["note"])
        link = common.wikilink(common.rel(path, vault), "queued")
        lines[i] = f"{parsed['prefix']}- [x] {common.watch_url(common.youtube_video_id(parsed['url']))} -> {link}"
        result["created" if created else "existing"].append(str(path))
    new_text = "\n".join(lines)
    if new_text != text:
        home.write_text(new_text, encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the video queue.")
    parser.add_argument("--vault", help="Vault root (default: detected)")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="Queue one video URL")
    add.add_argument("url")
    add.add_argument("--rights", choices=RIGHTS_CHOICES)
    add.add_argument("--mode", choices=common.MODES)
    add.add_argument("--priority", type=int, default=3)
    add.add_argument("--note", default="")
    lst = sub.add_parser("list", help="List queue notes")
    lst.add_argument("--status", choices=common.QUEUE_STATUSES)
    sub.add_parser("next", help="Print the next queued note")
    st = sub.add_parser("set", help="Update a queue note")
    st.add_argument("note_path")
    st.add_argument("--status", required=True, choices=common.QUEUE_STATUSES)
    st.add_argument("--run")
    st.add_argument("--error")
    sub.add_parser("import-inbox", help="Queue the Inbox lines of Home.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    settings = common.load_settings(vault)
    try:
        if args.command == "add":
            path, created = create_note(vault, args.url, args.rights or settings["default_rights"],
                                        args.mode or settings["default_mode"], args.priority, args.note)
            record = note_record(vault, path)
            record.update({"ok": True, "created": created})
            common.emit(record)
        elif args.command == "list":
            items = [note_record(vault, p) for p in queued_notes(vault, args.status)]
            common.emit({"ok": True, "count": len(items), "items": items})
        elif args.command == "next":
            path = pick_next(vault)
            payload = {"ok": True, "empty": path is None, "note": None}
            if path:
                payload["note"] = note_record(vault, path)
                payload["path"] = str(path.resolve())
            common.emit(payload)
        elif args.command == "set":
            path = set_status(vault, resolve_note(vault, args.note_path), args.status, args.run, args.error)
            record = note_record(vault, path)
            record["ok"] = True
            common.emit(record)
        else:
            result = import_inbox(vault, settings)
            result["ok"] = True
            common.emit(result)
    except ValueError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_FAIL, str(exc))
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
