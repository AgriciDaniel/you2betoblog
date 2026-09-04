"""Tests for make_run_note.py: create, update, idempotent log, video and gallery sections."""

from __future__ import annotations

import yt2b_common as common
from conftest import place_avt, run_main


def test_create_from_info(vault, run_dir, capsys):
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--status", "fetched",
                                           "--set", "rights=own", "mode=companion", "--log", "fetched: ok"], capsys)
    assert code == 0 and out["status"] == "fetched"
    fm, body = common.read_note(run_dir / "run.md")
    for key in ("type", "video_id", "video_url", "title", "channel", "channel_url", "published", "duration_s", "rights",
                "mode", "status", "captions", "blogs", "queue", "approvals", "created", "updated", "tags"):
        assert key in fm, key
    assert fm["type"] == "yt2b-video" and fm["video_url"] == "https://www.youtube.com/watch?v=abcdefghijk"
    assert fm["rights"] == "own" and fm["duration_s"] == 32 and fm["blogs"] == []
    assert fm["tags"] == ["yt2b", "stage/fetched", "format/video", "source/youtube", "rights/own"]
    headings = [h for h, _ in common.split_sections(body)[1]]
    assert headings == ["Video", "Summary", "Key takeaways", "Tags", "Frames", "Approvals", "Artifacts", "Log"]
    assert "fetched: ok" in body
    assert fm["thumbnail"] == "" and fm["frames"] == 0 and "hero" not in fm


def test_update_keeps_sections_and_log_idempotent(vault, run_dir, tmp_path, capsys):
    run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--log", "fetched: ok"], capsys)
    summary = tmp_path / "summary.txt"
    summary.write_text("A short summary.\n", encoding="utf-8")
    takeaways = tmp_path / "takeaways.md"
    takeaways.write_text("- one\n- two\n", encoding="utf-8")
    for _ in range(2):
        code, out = run_main("make_run_note", ["--vault", str(vault), "--run", common.rel(run_dir, vault), "--status", "briefed",
                                               "--summary", str(summary), "--takeaways", str(takeaways), "--tags", "Claude Code, tutorial",
                                               "--log", "briefed: brief written"], capsys)
        assert code == 0 and out["status"] == "briefed"
    fm, body = common.read_note(run_dir / "run.md")
    sections = dict(common.split_sections(body)[1])
    assert sections["Summary"] == "A short summary." and sections["Key takeaways"] == "- one\n- two"
    assert sections["Tags"] == "#claude-code #tutorial"
    assert body.count("fetched: ok") == 1 and body.count("briefed: brief written") == 1
    assert sections["Log"].index("fetched: ok") < sections["Log"].index("briefed: brief written")


def test_add_blog_and_artifacts(vault, run_dir, capsys):
    (run_dir / "analysis").mkdir()
    (run_dir / "analysis" / "transcript.md").write_text("x", encoding="utf-8")
    blog = vault / "03 Blogs" / "2026-09-03 my-post"
    blog.mkdir(parents=True)
    (blog / "my-post.md").write_text("---\ntitle: x\n---\n", encoding="utf-8")
    for _ in range(2):
        code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--add-blog", str(blog)], capsys)
        assert code == 0
    fm, body = common.read_note(run_dir / "run.md")
    assert fm["blogs"] == ["[[03 Blogs/2026-09-03 my-post/my-post|my-post]]"]
    assert "- Transcript: [[02 Videos/" in body and "- Blog: [[03 Blogs/2026-09-03 my-post/my-post|my-post]]" in body


def test_bad_status_and_missing_run(vault, run_dir, capsys):
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(vault / "02 Videos" / "nope")], capsys)
    assert code == 2


def test_from_brief_json(vault, run_dir, capsys):
    common.json_dump(run_dir / "brief" / "video-brief.json", {"summary": "Brief summary.", "key_takeaways": ["a", "b"], "tags": ["Claude Code", "setup"]})
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--status", "briefed", "--from-brief"], capsys)
    assert code == 0 and out["status"] == "briefed"
    sections = dict(common.split_sections(common.read_note(run_dir / "run.md")[1])[1])
    assert sections["Summary"] == "Brief summary." and sections["Key takeaways"] == "- a\n- b" and sections["Tags"] == "#claude-code #setup"
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--from-brief", str(run_dir / "missing.json")], capsys)
    assert code == 2


def test_video_section_without_thumbnail_or_frames(vault, run_dir, capsys):
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir)], capsys)
    assert code == 0
    sections = dict(common.split_sections(common.read_note(run_dir / "run.md")[1])[1])
    video = sections["Video"]
    assert video.startswith("![](https://www.youtube.com/watch?v=abcdefghijk)")
    assert "<iframe" not in video
    assert "thumbnail.jpg" not in video and "[!tip]" not in video
    assert "[Test Channel](https://www.youtube.com/@testchannel), published 2026-09-01, duration 00:32, captions none." in video
    assert "[Watch on YouTube](https://www.youtube.com/watch?v=abcdefghijk)" in video
    assert sections["Frames"] == "- (no frames extracted yet)" and "Blogs" not in sections


def test_video_thumbnail_chapters_and_frames_gallery(vault, run_dir, capsys):
    (run_dir / "source" / "thumbnail.jpg").write_bytes(b"\xff\xd8\xff")
    place_avt(run_dir, "avt", frames=3)
    (run_dir / "analysis" / "transcript.md").write_text("x", encoding="utf-8")
    common.json_dump(run_dir / "analysis" / "segments.json", {"chapters": [{"start_s": 0, "title": "Intro"}, {"start_s": 4.4, "title": "Install"}], "segments": []})
    for _ in range(2):
        code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--set", "captions=manual"], capsys)
        assert code == 0
    fm, body = common.read_note(run_dir / "run.md")
    run_rel = common.rel(run_dir, vault)
    assert fm["thumbnail"] == f"{run_rel}/source/thumbnail.jpg" and fm["frames"] == 3
    sections = dict(common.split_sections(body)[1])
    video = sections["Video"]
    assert "![Thumbnail of Test Video: Claude Code setup](source/thumbnail.jpg)" in video
    assert "captions manual" in video
    assert "> [!tip] Chapters\n> - [00:00](https://www.youtube.com/watch?v=abcdefghijk&t=0s) Intro\n> - [00:04](https://www.youtube.com/watch?v=abcdefghijk&t=4s) Install" in video
    frames = sections["Frames"]
    assert frames.startswith("```image-layout-masonry-4\n---\n")
    assert f"fromFolder: {run_rel}/analysis/avt_outputs/abcdefghijk/frames\nsortBy: name\ncaption: 3 frames extracted by video-analyzer (512 px, one per visual segment)\n---\n```" in frames
    assert f"[[{run_rel}/analysis/transcript|transcript]]" in frames
    assert body.count("```image-layout-masonry-4") == 1
    assert body.count("![](https://www.youtube.com/watch?v=abcdefghijk)") == 1


def test_blogs_section_hero_and_gallery_idempotent(vault, run_dir, capsys):
    blog = vault / "03 Blogs" / "2026-09-03 my-post"
    (blog / "images").mkdir(parents=True)
    (blog / "my-post.md").write_text("---\ntitle: My post title\n---\n", encoding="utf-8")
    (blog / "hero.jpg").write_bytes(b"\xff\xd8\xff")
    (blog / "images" / "01-frame-0001.jpg").write_bytes(b"\xff\xd8\xff")
    for _ in range(2):
        code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--add-blog", str(blog)], capsys)
        assert code == 0
    fm, body = common.read_note(run_dir / "run.md")
    assert fm["hero"] == "03 Blogs/2026-09-03 my-post/hero.jpg"
    headings = [h for h, _ in common.split_sections(body)[1]]
    assert headings == ["Video", "Summary", "Key takeaways", "Tags", "Frames", "Blogs", "Approvals", "Artifacts", "Log"]
    blogs = dict(common.split_sections(body)[1])["Blogs"]
    assert blogs.startswith("**[[03 Blogs/2026-09-03 my-post/my-post|My post title]]**")
    assert "![hero](03%20Blogs/2026-09-03%20my-post/hero.jpg)" in blogs
    assert "```image-layout-masonry-3\n---\nfromFolder: 03 Blogs/2026-09-03 my-post/images\nlimit: 12\ncaption: Frames used in my-post\n---\n```" in blogs
    assert body.count("image-layout-masonry-3") == 1 and body.count("![hero]") == 1


def test_user_sections_survive_updates(vault, run_dir, capsys):
    run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--log", "fetched: ok"], capsys)
    note = run_dir / "run.md"
    note.write_text(note.read_text(encoding="utf-8") + "\n## My notes\n\nKeep this.\n", encoding="utf-8")
    code, out = run_main("make_run_note", ["--vault", str(vault), "--run", str(run_dir), "--status", "analyzed", "--log", "analyzed: 0 frames"], capsys)
    assert code == 0
    fm, body = common.read_note(note)
    sections = dict(common.split_sections(body)[1])
    assert sections["My notes"] == "Keep this." and fm["status"] == "analyzed"
    assert [h for h, _ in common.split_sections(body)[1]][-1] == "My notes"
