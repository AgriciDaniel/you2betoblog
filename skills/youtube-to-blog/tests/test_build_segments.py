"""Tests for build_segments.py using the copied video-analyzer fixtures."""

from __future__ import annotations

import json
import re

import yt2b_common as common
from conftest import FIXTURES, copy_fixture, place_avt, run_main


def avt_text(transcript_source: str = "captions", with_audio: bool = True) -> str:
    text = (FIXTURES / "sample.avt").read_text(encoding="utf-8")
    text = text.replace("transcript_source: captions", f"transcript_source: {transcript_source}")
    if not with_audio:
        text = re.sub(r"^AUDIO: '.*'$", "AUDIO: ''", text, flags=re.M)
    return text


def build(run, analyze_dir, capsys):
    code, out = run_main("build_segments", ["--run", str(run), "--analyze-dir", str(analyze_dir)], capsys)
    assert code == 0, out
    return out, json.loads((run / "analysis" / "segments.json").read_text(encoding="utf-8")), (run / "analysis" / "transcript.md").read_text(encoding="utf-8")


def test_shapes_and_description_chapters(run_dir, analyze_dir, capsys):
    place_avt(run_dir, avt_text())
    out, data, md = build(run_dir, analyze_dir, capsys)
    assert out["segments"] == 3 and out["chapters"] == 3 and out["frames"] == 3 and out["transcript_source"] == "captions"
    assert data["schema"] == "yt2b/v1" and data["video"]["id"] == "abcdefghijk" and data["transcript_source"] == "captions"
    seg = data["segments"][1]
    assert seg["start_s"] == 4.0 and seg["end_s"] == 15.0 and seg["start"] == "00:04" and seg["scene"] == "screen-recording"
    assert seg["frame"] == "analysis/avt_outputs/abcdefghijk/frames/frame-002.jpg" and "install this package" in seg["audio"]
    assert data["chapters"] == [{"start_s": 0, "title": "Intro"}, {"start_s": 4, "title": "Install the package"}, {"start_s": 15, "title": "See it working"}]
    assert md.startswith("---\n") and "type: yt2b-knowledge" in md and "kind: transcript" in md
    assert "[!warning] Untrusted source text" in md and "[Test Channel](https://www.youtube.com/@testchannel)" in md
    for heading in ("## Chapters", "## Transcript", "## Segments"):
        assert heading in md
    assert "- [00:04](https://www.youtube.com/watch?v=abcdefghijk&t=4s) Install the package" in md
    assert "### 00:04 Install the package" in md
    assert "![frame\\|240](avt_outputs/abcdefghijk/frames/frame-001.jpg)" in md
    assert "youtu.be" not in md
    avt_path = run_dir / "analysis" / "avt_outputs" / "abcdefghijk" / "abcdefghijk.avt"
    assert avt_path.read_text(encoding="utf-8") == avt_text()


def test_midpoint_alignment_without_duplicates(run_dir, analyze_dir, capsys):
    place_avt(run_dir, avt_text("none", with_audio=False))
    vtt = (FIXTURES / "sample.vtt").read_text(encoding="utf-8").rstrip("\n") + (
        "\n\n00:00:14.000 --> 00:00:16.000\nstraddles the boundary\n\n00:00:40.000 --> 00:00:42.000\nafter the end\n")
    (run_dir / "source" / "captions.en.vtt").write_text(vtt, encoding="utf-8")
    common.write_note(run_dir / "run.md", {"type": "yt2b-video", "captions": "auto"}, "")
    out, data, md = build(run_dir, analyze_dir, capsys)
    audio = [s["audio"] for s in data["segments"]]
    assert out["transcript_source"] == "captions-auto"
    assert audio[0] == "What's up guys, today I want to show you something"
    assert audio[1] == "that completely changed how I use Claude Code. So the first thing you need to do is install this package."
    assert audio[2] == "straddles the boundary after the end"
    joined = " ".join(audio)
    for phrase in ("straddles the boundary", "after the end", "install this package"):
        assert joined.count(phrase) == 1


def test_rollup_captions_deduplicated(run_dir, analyze_dir, capsys):
    place_avt(run_dir, avt_text("none", with_audio=False))
    copy_fixture("rollup.vtt", run_dir / "source" / "captions.en.vtt")
    out, data, md = build(run_dir, analyze_dir, capsys)
    joined = " ".join(s["audio"] for s in data["segments"]).split()
    assert " ".join(joined) == "what's up guys today I want to show you something"
    assert out["transcript_source"] == "captions"


def test_chapters_fallback_to_info_field(run_dir, analyze_dir, info, capsys):
    info["description"] = "No chapter lines here.\n0:10 only two\n0:20 entries"
    common.json_dump(run_dir / "source" / "video.info.json", info)
    place_avt(run_dir, avt_text())
    out, data, md = build(run_dir, analyze_dir, capsys)
    assert [c["title"] for c in data["chapters"]] == ["Field intro", "Field install", "Field demo"]
    info["description"] = "1:00 Late start\n2:00 Second\n3:00 Third"
    info["chapters"] = None
    common.json_dump(run_dir / "source" / "video.info.json", info)
    out, data, md = build(run_dir, analyze_dir, capsys)
    assert data["chapters"] == [] and "- (no chapters)" in md and "### 00:00 Full transcript" in md


def test_missing_avt_exit_1(run_dir, analyze_dir, capsys):
    code, out = run_main("build_segments", ["--run", str(run_dir), "--analyze-dir", str(analyze_dir)], capsys)
    assert code == 1 and "analyze" in out["error"]
