#!/usr/bin/env python3
"""Deterministic controller for YouTube to Blog state and release gates.

The controller never calls a model, downloads a video, publishes, or spends
money. Agents create content between checkpoints. This script records current
authorization, checks write readiness, audits stale state, and performs the
final local state transition only after delivery and evaluation pass.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contract  # noqa: E402
import make_run_note  # noqa: E402
import yt2b_common as common  # noqa: E402

queue_script = common.load_module(Path(__file__).with_name("queue.py"), "yt2b_pipeline_queue")


def resolve(vault: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else vault / path).resolve()


def run_record(run: Path) -> tuple[dict, str]:
    note = run / "run.md"
    if not note.is_file():
        raise ValueError(f"run note missing: {note}")
    return common.read_note(note)


def evaluation_for(vault: Path, run: Path, blog: Path) -> tuple[Path | None, dict]:
    wanted_run = (run / "run.md").resolve()
    wanted_blog = contract.post_path(blog).resolve()
    matches: list[tuple[Path, dict]] = []
    folder = vault / common.ROOMS["evaluations"]
    for note in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        try:
            fm, _body = common.read_note(note)
        except Exception:
            continue
        if fm.get("type") != common.NOTE_TYPES["evaluation"]:
            continue
        run_target = contract.resolve_wikilink(vault, fm.get("run"), "run.md")
        blog_target = contract.resolve_wikilink(vault, fm.get("blog"))
        if run_target == wanted_run and blog_target == wanted_blog:
            matches.append((note, fm))
    return matches[-1] if matches else (None, {})


def registered_blogs(vault: Path, fm: dict) -> list[Path]:
    blogs: list[Path] = []
    for link in fm.get("blogs") or []:
        post = contract.resolve_wikilink(vault, link)
        if post is not None and post.is_file() and post.parent not in blogs:
            blogs.append(post.parent)
    return blogs


def selected_strategy_count(vault: Path, run: Path) -> int:
    return len(contract.approved_strategy_ids(vault, run))


def approval_links(vault: Path, run: Path) -> list[str]:
    return [common.wikilink(common.rel(note, vault), note.stem) for note, _fm, _body in contract.approval_notes(vault, run)]


def cmd_inspect(vault: Path, run: Path) -> int:
    fm, _body = run_record(run)
    status = str(fm.get("status") or "fetched")
    checks = {
        "provider_authorized": contract.provider_authorized(run),
        "segments": (run / "analysis" / "segments.json").is_file(),
        "brief": (run / "brief" / "video-brief.json").is_file(),
        "strategy": (run / "strategy.md").is_file(),
        "strategy_approved": contract.strategy_approval_selected(vault, run),
        "blogs": bool(fm.get("blogs")),
    }
    if not checks["provider_authorized"]:
        next_action = "record current analyze or full authorization"
    elif not checks["segments"]:
        next_action = "analyze video"
    elif not checks["brief"]:
        next_action = "build brief"
    elif not checks["strategy"]:
        next_action = "create strategy"
    elif not checks["strategy_approved"]:
        next_action = "wait for strategy approval"
    elif not checks["blogs"]:
        next_action = "create approved blog and request outline approval when required"
    elif status != "done":
        next_action = "deliver, evaluate, then complete"
    else:
        next_action = "complete"
    common.emit({"ok": True, "run": str(run), "status": status, "checks": checks, "next_action": next_action})
    return common.EXIT_OK


def cmd_authorize(vault: Path, run: Path, current_request: str) -> int:
    run_record(run)
    note = make_run_note.update_run_note(
        vault,
        run,
        log=f"provider authorization: current {current_request} request",
    )
    common.emit({"ok": True, "run_note": str(note), "authorization": current_request})
    return common.EXIT_OK


def cmd_check_write(vault: Path, run: Path, blog: Path) -> int:
    run_record(run)
    failures = contract.pre_write_violations(vault, run, blog)
    common.emit({"ok": not failures, "run": str(run), "blog": str(blog), "violations": failures})
    return common.EXIT_OK if not failures else common.EXIT_POLICY


def completion_violations(vault: Path, run: Path, blog: Path) -> tuple[list[str], dict, Path | None]:
    failures: list[str] = []
    report = common.json_load(blog / "preflight-report.json", {}) or {}
    gate6 = next((g for g in report.get("gates") or [] if isinstance(g, dict) and g.get("gate") == 6), None)
    gates = [g for g in report.get("gates") or [] if isinstance(g, dict)]
    numbers = [g.get("gate") for g in gates]
    complete_report = all(numbers.count(n) == 1 for n in range(1, 7)) and all(g.get("passed") is True for g in gates)
    if not complete_report or not gate6 or not gate6.get("passed") or report.get("blocked", True):
        failures.append("delivery preflight, including Gate 6, has not passed")
    elif (not (blog / "review.md").is_file()
          or gate6.get("post_sha256") != contract.post_contract_sha256(contract.post_path(blog))
          or gate6.get("review_sha256") != contract.file_sha256(blog / "review.md")):
        failures.append("post or review changed after delivery gates; rerun render, review and gates")
    # Revalidate approvals, selected angles, site, and review severity at completion.
    live_gate = contract.contract_gate(vault, run, blog, report)
    failures.extend(live_gate["violations"])
    post_fm, _ = common.read_note(contract.post_path(blog))
    linked_run = contract.resolve_wikilink(vault, post_fm.get("yt2b_video"), "run.md")
    if linked_run != (run / "run.md").resolve():
        failures.append("post does not belong to this run")
    evaluation, eval_fm = evaluation_for(vault, run, blog)
    if evaluation is None:
        failures.append("matching evaluation note is missing")
    elif not eval_fm.get("rubric_pass") or not eval_fm.get("gates_passed"):
        failures.append("matching evaluation has not passed the rubric and gates")
    post_fm, _body = common.read_note(contract.post_path(blog))
    if post_fm.get("yt2b_status") != "reviewed":
        failures.append("post yt2b_status is not reviewed")
    return failures, eval_fm, evaluation


def cleanup_video_cache(vault: Path, run: Path, keep: bool) -> list[str]:
    if keep:
        return []
    fm, _body = run_record(run)
    video_id = str(fm.get("video_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("refusing cache cleanup: invalid video_id")
    cache = (vault / common.CACHE_DIR).resolve()
    deleted: list[str] = []
    if cache.is_dir():
        for path in sorted(cache.glob(f"{video_id}.*")):
            if path.is_file() and path.parent.resolve() == cache:
                path.unlink()
                deleted.append(str(path))
    return deleted


def cmd_complete(vault: Path, run: Path, blog: Path, keep_video: bool) -> int:
    fm, _body = run_record(run)
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(fm.get("video_id") or "")):
        return common.fail(common.EXIT_POLICY, "cannot complete a run with an invalid video_id")
    blogs = registered_blogs(vault, fm)
    if blog not in blogs:
        blogs.append(blog)
    failures: list[str] = []
    selected = selected_strategy_count(vault, run)
    if selected and len(blogs) < selected:
        failures.append(f"strategy approved {selected} angles but only {len(blogs)} blogs are registered")
    records: list[tuple[Path, dict, Path | None]] = []
    for item in blogs:
        item_failures, eval_fm, evaluation = completion_violations(vault, run, item)
        failures.extend(f"{item.name}: {failure}" for failure in item_failures)
        records.append((item, eval_fm, evaluation))
    if failures:
        common.emit({"ok": False, "run": str(run), "blogs": [str(item) for item in blogs], "violations": failures})
        return common.EXIT_POLICY
    scores = [int(eval_fm.get("score") or 0) for _item, eval_fm, _evaluation in records]
    note = make_run_note.update_run_note(
        vault,
        run,
        status="done",
        add_blog=blog,
        log=f"done: {len(blogs)} blog(s), scores {','.join(str(score) for score in scores)}, all delivery gates passed",
    )
    queue_note = contract.resolve_wikilink(vault, fm.get("queue"))
    if queue_note and queue_note.is_file():
        queue_script.set_status(vault, queue_note, "done", str(run))
    settings = common.load_settings(vault)
    deleted = cleanup_video_cache(vault, run, keep_video or bool(settings.get("keep_video")))
    make_run_note.update_run_note(vault, run, log=f"cache cleanup: removed {len(deleted)} downloaded video file(s)")
    common.emit({"ok": True, "run_note": str(note),
                 "evaluations": [str(evaluation) for _item, _eval_fm, evaluation in records], "scores": scores,
                 "queue": str(queue_note) if queue_note else "", "deleted_cache_files": deleted})
    return common.EXIT_OK


def audit_run(vault: Path, run: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        fm, _body = run_record(run)
    except ValueError as exc:
        return [{"severity": "blocking", "run": str(run), "issue": str(exc)}]
    status = str(fm.get("status") or "")
    if status in ("analyzed", "briefed", "strategy", "writing", "done") and not contract.provider_authorized(run):
        issues.append({"severity": "blocking", "run": str(run), "issue": "provider authorization is missing from the log"})
    expected = approval_links(vault, run)
    recorded = list(fm.get("approvals") or [])
    if expected and set(expected) != set(recorded):
        issues.append({"severity": "warning", "run": str(run), "issue": "approval backlinks are stale"})
    queue_note = contract.resolve_wikilink(vault, fm.get("queue"))
    if queue_note and queue_note.is_file():
        queue_fm, _queue_body = common.read_note(queue_note)
        wanted = "done" if status == "done" else "running"
        if queue_fm.get("status") != wanted:
            issues.append({"severity": "blocking", "run": str(run),
                           "issue": f"queue status {queue_fm.get('status')} disagrees with run status {status}"})
    if status == "done" and not common.load_settings(vault).get("keep_video"):
        video_id = str(fm.get("video_id") or "")
        cache = vault / common.CACHE_DIR
        if video_id and cache.is_dir() and any(p.is_file() for p in cache.glob(f"{video_id}.*")):
            issues.append({"severity": "warning", "run": str(run), "issue": "downloaded video remains after a completed run"})
    if status != "done":
        issues.append({"severity": "info", "run": str(run), "issue": f"run is incomplete at {status or 'unknown'}"})
    return issues


def cmd_audit(vault: Path, run: Path | None) -> int:
    runs = [run] if run else sorted((vault / common.ROOMS["videos"]).glob("*/"))
    issues = [issue for item in runs if item.is_dir() for issue in audit_run(vault, item)]
    blocking = [issue for issue in issues if issue["severity"] == "blocking"]
    common.emit({"ok": not blocking, "runs": len(runs), "blocking": len(blocking), "issues": issues})
    return common.EXIT_OK if not blocking else common.EXIT_POLICY


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="vault root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "authorize"):
        command = sub.add_parser(name)
        command.add_argument("--run", required=True)
        if name == "authorize":
            command.add_argument("--current-request", required=True, choices=("analyze", "full"))
    write = sub.add_parser("check-write")
    write.add_argument("--run", required=True)
    write.add_argument("--blog", required=True)
    complete = sub.add_parser("complete")
    complete.add_argument("--run", required=True)
    complete.add_argument("--blog", required=True)
    complete.add_argument("--keep-video", action="store_true")
    audit = sub.add_parser("audit")
    audit.add_argument("--run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
        run = resolve(vault, args.run) if getattr(args, "run", None) else None
        if run is not None and not run.is_dir():
            return common.fail(common.EXIT_INPUT, f"run folder not found: {run}")
        if args.command == "inspect":
            return cmd_inspect(vault, run)
        if args.command == "authorize":
            return cmd_authorize(vault, run, args.current_request)
        if args.command == "audit":
            return cmd_audit(vault, run)
        blog = resolve(vault, args.blog)
        if not blog.is_dir():
            return common.fail(common.EXIT_INPUT, f"blog folder not found: {blog}")
        if args.command == "check-write":
            return cmd_check_write(vault, run, blog)
        return cmd_complete(vault, run, blog, args.keep_video)
    except (OSError, ValueError) as exc:
        return common.fail(common.EXIT_INPUT, str(exc))


if __name__ == "__main__":
    sys.exit(main())
