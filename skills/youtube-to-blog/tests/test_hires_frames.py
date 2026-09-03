"""Tests for hires_frames.py using a generated ffmpeg test clip."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

FFMPEG = shutil.which("ffmpeg")
VIDEO_ID = "abc123DEF45"
pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg not installed")

try:
    from PIL import Image  # type: ignore
    HAVE_PIL = True
except ImportError:  # pragma: no cover
    HAVE_PIL = False


def run_script(*args):
    proc = subprocess.run([sys.executable, str(SCRIPTS / "hires_frames.py"), *map(str, args)], capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    data = json.loads(lines[-1]) if lines else {}
    return proc.returncode, data, proc.stderr


def make_clip(tmp_path: Path) -> tuple[Path, Path]:
    clip = tmp_path / "clip.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=3:size=320x180:rate=10",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    thumb = tmp_path / "thumbnail.jpg"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360:rate=1",
                    "-frames:v", "1", str(thumb)], check=True)
    return clip, thumb


def make_world(tmp_path: Path, rights: str, cap_third: int = 1) -> tuple[Path, Path, Path, Path]:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    fm = dict(common.DEFAULT_SETTINGS)
    fm.update({"type": "yt2b-settings", "frame_width": 320, "max_frames_own": 8, "max_frames_third_party": cap_third})
    common.write_note(vault / "00 Home" / "Settings.md", fm, "Settings\n")
    clip, thumb = make_clip(tmp_path)
    run = vault / "02 Videos" / f"2026-09-03-sample-video-{VIDEO_ID}"
    (run / "source").mkdir(parents=True)
    shutil.copyfile(thumb, run / "source" / "thumbnail.jpg")
    common.json_dump(run / "source" / "video.info.json", {
        "id": VIDEO_ID, "title": "Sample Video", "channel": "Sample Channel",
        "channel_url": "https://www.youtube.com/@sample", "duration": 3, "license": "",
        "thumbnail": f"https://i.ytimg.com/vi/{VIDEO_ID}/maxresdefault.jpg", "upload_date": "20260830",
    })
    common.write_note(run / "run.md", {"type": "yt2b-video", "video_id": VIDEO_ID, "rights": rights, "mode": "companion",
                                       "tags": ["yt2b", "video"]}, "## Summary\n")
    common.json_dump(run / "brief" / "video-brief.json", {"key_moments": [
        {"id": "m1", "t_s": 1.0, "label": "Opening frame", "why": "Shows the test pattern", "hero": True, "section": "s1"},
        {"id": "m2", "t_s": 2.0, "label": "Second look", "blog": "sample-post", "section": "s1"},
        {"id": "m3", "t_s": 2.5, "label": "Other blog", "blog": "other-post"},
    ]})
    blog = vault / "03 Blogs" / "2026-09-03 sample-post"
    blog.mkdir(parents=True)
    common.write_note(blog / "sample-post.md", {"title": "Sample post", "slug": "sample-post", "yt2b_rights": rights,
                                                "type": "yt2b-blog"}, "<!-- draft pending -->\n")
    return vault, run, blog, clip


def test_own_mode_extracts_frames_thumb_credits_and_hero(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    names = [Path(i["path"]).name for i in data["images"]]
    assert names == ["01-opening-frame-0001.jpg", "02-second-look-0002.jpg"], names
    for entry in data["images"]:
        p = Path(entry["path"])
        assert p.is_file() and p.stat().st_size > 0
        assert entry["rel"] == f"images/{p.name}" and entry["url"].startswith(f"https://www.youtube.com/watch?v={VIDEO_ID}&t=")
    assert data["images"][0]["caption"] == "Opening frame (00:01)"
    assert data["rights"] == "own" and data["cap"] == 8
    thumb = blog / "images" / "video-thumb.jpg"
    assert thumb.is_file() and data["thumb"] == str(thumb)
    credits = (blog / "images" / "CREDITS.txt").read_text(encoding="utf-8")
    assert "Video: Sample Video" in credits and "Channel: Sample Channel" in credits
    assert "Rights mode: own" in credits and f"Watch: https://www.youtube.com/watch?v={VIDEO_ID}" in credits
    assert "01-opening-frame-0001.jpg  00:01" in credits and "video-thumb.jpg  thumbnail" in credits
    manifest = json.loads((blog / "images" / "manifest.json").read_text(encoding="utf-8"))
    assert [i["label"] for i in manifest["images"]] == ["Opening frame", "Second look"]
    if HAVE_PIL:
        hero = blog / "hero.jpg"
        assert hero.is_file() and data["hero"] == str(hero)
        with Image.open(hero) as im:
            assert im.size == (1200, 630)
        with Image.open(data["images"][0]["path"]) as im:
            assert im.size[0] == 320
        credit = (blog / "hero-credit.txt").read_text(encoding="utf-8")
        assert "frame at 00:01" in credit and "own video" in credit
    code, again, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    assert [i["status"] for i in again["images"]] == ["existing", "existing"]
    assert [Path(i["path"]).name for i in again["images"]] == names


def test_third_party_caps_frames_and_writes_no_hero(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "third-party", cap_third=1)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    assert len(data["images"]) == 1 and data["skipped"] == 1 and data["cap"] == 1
    assert data["hero"] is None and not (blog / "hero.jpg").exists()
    assert 'in "Sample Video" by Sample Channel' in data["images"][0]["caption"]
    credits = (blog / "images" / "CREDITS.txt").read_text(encoding="utf-8")
    assert "Rights mode: third-party" in credits and "commentary" in credits


def test_missing_inputs(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    code, data, _ = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", tmp_path / "nope.mp4")
    assert code == 2 and data["ok"] is False
    code, data, _ = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip, "--moments", tmp_path / "none.json")
    assert code == 2


CROP_REASON = "keeps the comparison table in the upper left, the webcam overlay and the desk are excluded"


def frame_size(path: Path) -> tuple[int, int]:
    if HAVE_PIL:
        with Image.open(path) as im:
            return im.size
    out = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    w, h = [p for p in out.stdout.strip().split(",") if p][:2]
    return int(w), int(h)


def write_moments(run: Path, crop):
    common.json_dump(run / "brief" / "video-brief.json", {"key_moments": [
        {"id": "m1", "t_s": 1.0, "label": "Opening frame", "section": "s1"},
        {"id": "m2", "t_s": 2.0, "label": "Table close up", "section": "s1", "crop": crop},
    ]})


def test_valid_crop_changes_size_and_lands_in_manifest_and_credits(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    write_moments(run, {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5, "reason": CROP_REASON})
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    full, cropped = data["images"]
    assert full["crop"] is None and full["crop_reason"] == ""
    assert frame_size(Path(full["path"])) == (320, 180)
    assert frame_size(Path(cropped["path"])) == (320, 112), "crop 256x90 scaled to the target width"
    assert cropped["crop"] == {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5, "keep_aspect": "free"}
    assert cropped["crop_reason"] == CROP_REASON
    assert cropped["crop_px"] == [256, 90, 32, 36], "even pixels"
    assert cropped["source_size"] == [320, 180] and cropped["output_size"] == [320, 112]
    assert data["cropped"] == 1 and data["crop_skipped"] == []
    manifest = json.loads((blog / "images" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["images"][1]["crop_reason"] == CROP_REASON
    credits = (blog / "images" / "CREDITS.txt").read_text(encoding="utf-8")
    assert f"  cropped: {CROP_REASON}" in credits
    assert credits.count("cropped:") == 1
    code, again, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0 and [i["status"] for i in again["images"]] == ["existing", "existing"]


def test_keep_aspect_widens_to_the_ratio(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    write_moments(run, {"x": 0.1, "y": 0.0, "w": 0.5, "h": 1.0, "keep_aspect": "16:9", "reason": CROP_REASON})
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    cropped = data["images"][1]
    assert cropped["crop_px"] == [320, 180, 0, 0], "a tall region widens to 16:9 and clamps to the frame"
    assert frame_size(Path(cropped["path"])) == (320, 180)


@pytest.mark.parametrize("crop, needle", [
    ({"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.8, "reason": CROP_REASON}, "45%"),
    ({"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8, "reason": "too short"}, "reason"),
    ({"x": 0.5, "y": 0.1, "w": 0.8, "h": 0.8, "reason": CROP_REASON}, "inside the frame"),
    ({"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8, "reason": CROP_REASON, "keep_aspect": "1:1"}, "keep_aspect"),
])
def test_invalid_crop_is_skipped_with_a_warning(tmp_path, crop, needle):
    vault, run, blog, clip = make_world(tmp_path, "own")
    write_moments(run, crop)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    assert "crop skipped" in err and needle in err
    cropped = data["images"][1]
    assert cropped["crop"] is None and frame_size(Path(cropped["path"])) == (320, 180)
    assert data["cropped"] == 0 and len(data["crop_skipped"]) == 1
    assert "cropped:" not in (blog / "images" / "CREDITS.txt").read_text(encoding="utf-8")


def test_no_crop_ignores_crops_and_a_changed_crop_re_extracts(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    write_moments(run, {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5, "reason": CROP_REASON})
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip, "--no-crop")
    assert code == 0, err
    assert data["no_crop"] is True and data["cropped"] == 0
    assert all(i["crop"] is None for i in data["images"])
    assert frame_size(Path(data["images"][1]["path"])) == (320, 180)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip)
    assert code == 0, err
    assert [i["status"] for i in data["images"]] == ["existing", "re-extracted"]
    assert frame_size(Path(data["images"][1]["path"])) == (320, 112)


def test_delete_video_only_inside_cache(tmp_path):
    vault, run, blog, clip = make_world(tmp_path, "own")
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--video", clip, "--delete-video")
    assert code == 0, err
    assert data["video_deleted"] is False and clip.is_file(), "a video outside .cache/video is never deleted"
    cache = vault / ".cache" / "video"
    cache.mkdir(parents=True)
    cached = cache / f"{VIDEO_ID}.mp4"
    shutil.copyfile(clip, cached)
    code, data, err = run_script("--vault", vault, "--run", run, "--blog", blog, "--force", "--delete-video")
    assert code == 0, err
    assert data["video_deleted"] is True and not cached.exists()
    assert len(data["images"]) == 2
