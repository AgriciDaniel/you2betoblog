"""Tests for deterministic controller inspection and completion."""

from __future__ import annotations

import yt2b_common as common
from conftest import run_main
from test_contract import SLUG, VIDEO_ID, make_world


def test_check_write_and_inspect(tmp_path, capsys):
    vault, run, blog = make_world(tmp_path)
    code, data = run_main("pipeline", ["--vault", str(vault), "check-write", "--run", str(run), "--blog", str(blog)], capsys)
    assert code == 0 and data["ok"] is True
    code, data = run_main("pipeline", ["--vault", str(vault), "inspect", "--run", str(run)], capsys)
    assert code == 0 and data["checks"]["provider_authorized"] is True


def test_authorize_is_idempotent(tmp_path, capsys):
    vault, run, _blog = make_world(tmp_path)
    note = run / "run.md"
    fm, body = common.read_note(note)
    body = body.replace("- 2026-09-04T10:00:00 provider authorization: current full request\n", "")
    common.write_note(note, fm, body)
    for _ in range(2):
        code, data = run_main("pipeline", ["--vault", str(vault), "authorize", "--run", str(run),
                                                "--current-request", "analyze"], capsys)
        assert code == 0 and data["authorization"] == "analyze"
    assert common.read_note(note)[1].count("provider authorization: current analyze request") == 1


def test_complete_updates_state_and_removes_only_matching_cache(tmp_path, capsys):
    vault, run, blog = make_world(tmp_path)
    post = blog / f"{SLUG}.md"
    import contract
    gate6 = contract.contract_gate(vault, run, blog)
    report = {"blocked": False, "gates": [
        {"gate": n, "name": f"Gate {n}", "passed": True, "violations": []} for n in range(1, 6)
    ] + [gate6]}
    common.json_dump(blog / "preflight-report.json", report)
    common.update_note(post, {"yt2b_status": "reviewed", "yt2b_score": 95, "binder-status": "complete"})
    eval_note = vault / common.ROOMS["evaluations"] / f"2026-09-04-{SLUG}.md"
    common.write_note(eval_note, {
        "type": "yt2b-evaluation", "blog": common.wikilink(common.rel(post, vault), SLUG),
        "run": common.wikilink(common.rel(run / "run.md", vault), "run"), "score": 95,
        "gates_passed": True, "rubric_pass": True, "tags": ["yt2b", "format/evaluation", "stage/done"],
    }, "# Evaluation\n")
    queue_note = vault / "01 Queue" / f"2026-09-04-{VIDEO_ID}.md"
    common.write_note(queue_note, {
        "type": "yt2b-queue", "video_id": VIDEO_ID, "status": "running", "rights": "own",
        "tags": ["yt2b", "stage/fetched", "format/video", "source/youtube", "rights/own"],
    }, "# Queue\n")
    common.update_note(run / "run.md", {"queue": common.wikilink(common.rel(queue_note, vault), queue_note.stem)})
    cache = vault / common.CACHE_DIR
    cache.mkdir(parents=True)
    matching = cache / f"{VIDEO_ID}.mp4"
    other = cache / "otherVideo1.mp4"
    matching.write_bytes(b"video")
    other.write_bytes(b"other")

    code, data = run_main("pipeline", ["--vault", str(vault), "complete", "--run", str(run), "--blog", str(blog)], capsys)
    assert code == 0 and data["ok"] is True and data["scores"] == [95]
    assert not matching.exists() and other.exists()
    assert common.read_note(run / "run.md")[0]["status"] == "done"
    assert common.read_note(queue_note)[0]["status"] == "done"


def test_complete_refuses_missing_evaluation(tmp_path, capsys):
    vault, run, blog = make_world(tmp_path)
    import contract
    common.json_dump(blog / "preflight-report.json", {"blocked": False, "gates": [
        {"gate": n, "passed": True} for n in range(1, 6)
    ] + [contract.contract_gate(vault, run, blog)]})
    code, data = run_main("pipeline", ["--vault", str(vault), "complete", "--run", str(run), "--blog", str(blog)], capsys)
    assert code == common.EXIT_POLICY and data["ok"] is False
    assert any("matching evaluation note is missing" in item for item in data["violations"])


def test_complete_waits_for_every_approved_angle(tmp_path, capsys):
    vault, run, blog = make_world(tmp_path)
    strategy = next((vault / common.ROOMS["approvals_queue"]).glob("*-strategy.md"))
    common.update_note(strategy, {"selected": ["blog-1", "blog-2"]})
    code, data = run_main("pipeline", ["--vault", str(vault), "complete", "--run", str(run), "--blog", str(blog)], capsys)
    assert code == common.EXIT_POLICY
    assert any("approved 2 angles" in item for item in data["violations"])
