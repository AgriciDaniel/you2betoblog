"""Tests for alembic_sync.py: neutral render, root VOICE.md render, hash skip logic, --force."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import alembic_sync  # noqa: E402
import yt2b_common as common  # noqa: E402

TEMPLATES = SKILL_DIR / "references" / "alembic"
DASHES = ("\u2014", "\u2013")


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    return vault


def run(vault: Path, *extra: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = alembic_sync.main(["--vault", str(vault), *extra])
    text = out.getvalue()
    return code, (json.loads(text) if text.strip() else {})


def parse_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    block, body = common.split_frontmatter(text)
    assert block is not None, f"{path.name} has no frontmatter"
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(block)
        assert isinstance(data, dict)
    except ImportError:
        data = common.parse_frontmatter(block)
    return data, body


def write_voice(vault: Path, phrase: str) -> None:
    (vault / "VOICE.md").write_text(
        "# Voice Context\n\n> This file is auto-loaded by all blog sub-skills. Last updated: 2026-09-03.\n\n"
        f"## Pronoun stance\nsecond person\n\n## Taboo phrases\n- {phrase}\n",
        encoding="utf-8",
    )


def write_brand(vault: Path, phrase: str) -> None:
    (vault / "BRAND.md").write_text(
        f"# Brand Context\n\n## Audience\n- **Primary**: {phrase}\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def test_templates_are_well_formed():
    templates = sorted(TEMPLATES.glob("*.md"))
    assert len(templates) == 11
    ids = set()
    for path in templates:
        fm, body = common.read_note(path)
        for key in alembic_sync.REQUIRED_KEYS:
            assert key in fm, f"{path.name} lacks {key}"
        assert fm["id"] == f"yt2b-{fm['yt2b_id']}"
        assert path.stem == fm["yt2b_id"]
        assert fm["id"] not in ids
        ids.add(fm["id"])
        assert fm["providerId"] == "default-claude-cli"
        assert isinstance(fm["replaceSelection"], bool) and isinstance(fm["humanize"], bool)
        assert 0 <= fm["linkDepth"] <= 3
        assert "{=SELECTION=}" in fm["prompt"] or "{=CONTEXT=}" in fm["prompt"]
        assert len(body.strip().splitlines()) < 40, f"{path.name} body is 40 lines or more"
        text = path.read_text(encoding="utf-8")
        assert not any(d in text for d in DASHES), f"{path.name} contains an em or en dash"


def test_selection_and_context_modes_match_spec():
    modes = {}
    for path in TEMPLATES.glob("*.md"):
        fm, _ = common.read_note(path)
        modes[fm["yt2b_id"]] = (fm["prompt"], fm["replaceSelection"], fm["humanize"])
    assert modes["rewrite-in-my-voice"] == ("{=SELECTION=}", True, True)
    assert modes["key-takeaways"] == ("{=CONTEXT=}", False, False)
    assert modes["meta-description"][0] == "{=CONTEXT=}" and modes["meta-description"][1] is False
    assert modes["faq-from-context"][0] == "{=CONTEXT=}" and modes["faq-from-context"][1] is False
    assert modes["section-from-transcript"] == ("{=SELECTION=}", False, False)
    for wf in ("tighten-section", "answer-first-intro", "attribute-claims", "alt-text", "de-slop", "fact-check-flags"):
        assert modes[wf] == ("{=SELECTION=}", True, False), wf


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def test_render_without_voice_uses_neutral_fallback(tmp_path):
    vault = make_vault(tmp_path)
    code, result = run(vault)
    assert code == 0
    assert result["voice_source"] == "neutral" and result["brand_source"] == "neutral"
    assert len(result["written"]) == 11 and result["skipped"] == [] and result["unchanged"] == []
    assert result["warnings"] == []
    alembic_dir = vault / "_alembic"
    files = sorted(alembic_dir.glob("yt2b-*.md"))
    assert [p.name for p in files] == sorted(Path(p).name for p in result["written"])
    for path in files:
        fm, body = parse_note(path)
        for key in alembic_sync.ALEMBIC_KEYS:
            assert key in fm, f"{path.name} lacks {key}"
        assert fm["yt2b_hash"].startswith("sha256:")
        assert fm["id"] == path.stem
        assert "{{" not in path.read_text(encoding="utf-8")
        assert not any(d in body for d in DASHES)
    rewrite = (alembic_dir / "yt2b-rewrite-in-my-voice.md").read_text(encoding="utf-8")
    assert "Neutral voice" in rewrite
    intro = (alembic_dir / "yt2b-answer-first-intro.md").read_text(encoding="utf-8")
    assert "Neutral brand" in intro and "Neutral voice" in intro
    flags = (alembic_dir / "yt2b-fact-check-flags.md").read_text(encoding="utf-8")
    assert "Neutral voice" not in flags


def test_render_with_root_voice_and_brand(tmp_path):
    vault = make_vault(tmp_path)
    write_voice(vault, "synergy-word-9f3")
    write_brand(vault, "solo indie developers-7c1")
    code, result = run(vault)
    assert code == 0
    assert result["voice_source"] == "root" and result["brand_source"] == "root"
    rewrite = (vault / "_alembic" / "yt2b-rewrite-in-my-voice.md").read_text(encoding="utf-8")
    assert "synergy-word-9f3" in rewrite
    assert "# Voice Context" not in rewrite and "auto-loaded" not in rewrite
    assert "Neutral voice" not in rewrite
    intro = (vault / "_alembic" / "yt2b-answer-first-intro.md").read_text(encoding="utf-8")
    assert "solo indie developers-7c1" in intro and "# Brand Context" not in intro


def test_empty_voice_falls_back_with_warning(tmp_path):
    vault = make_vault(tmp_path)
    (vault / "VOICE.md").write_text("# Voice Context\n\n", encoding="utf-8")
    code, result = run(vault)
    assert code == 0
    assert result["voice_source"] == "neutral"
    assert any("VOICE.md" in w and "empty" in w for w in result["warnings"])


def test_unfilled_placeholder_in_voice_is_reported(tmp_path):
    vault = make_vault(tmp_path)
    (vault / "VOICE.md").write_text("# Voice Context\n\n## Pronoun stance\n{{pronoun_stance}}\n", encoding="utf-8")
    code, result = run(vault)
    assert code == 0
    assert result["voice_source"] == "root"
    assert any("unfilled" in w for w in result["warnings"])
    assert any("yt2b-rewrite-in-my-voice.md" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Hash skip logic
# ---------------------------------------------------------------------------

def test_rerun_is_idempotent(tmp_path):
    vault = make_vault(tmp_path)
    run(vault)
    before = {p.name: p.read_text(encoding="utf-8") for p in (vault / "_alembic").glob("*.md")}
    code, result = run(vault)
    assert code == 0
    assert result["written"] == [] and result["skipped"] == []
    assert len(result["unchanged"]) == 11
    after = {p.name: p.read_text(encoding="utf-8") for p in (vault / "_alembic").glob("*.md")}
    assert before == after


def test_existing_state_detects_edits(tmp_path):
    vault = make_vault(tmp_path)
    run(vault)
    target = vault / "_alembic" / "yt2b-tighten-section.md"
    assert alembic_sync.existing_state(target) == "pristine"
    target.write_text(target.read_text(encoding="utf-8") + "\nMy own extra rule.\n", encoding="utf-8")
    assert alembic_sync.existing_state(target) == "edited"
    fm, body = common.read_note(target)
    fm.pop("yt2b_hash")
    common.write_note(target, fm, body)
    assert alembic_sync.existing_state(target) == "edited"
    assert alembic_sync.existing_state(vault / "_alembic" / "nope.md") == "missing"


def test_user_edit_is_kept_unless_force(tmp_path):
    vault = make_vault(tmp_path)
    run(vault)
    target = vault / "_alembic" / "yt2b-de-slop.md"
    edited = target.read_text(encoding="utf-8").replace("Repair the selected text", "Repair the chosen text")
    target.write_text(edited, encoding="utf-8")

    write_voice(vault, "brand-new-voice-4a2")
    code, result = run(vault)
    assert code == 0
    assert str(target.resolve()) in result["skipped"]
    assert target.read_text(encoding="utf-8") == edited
    rewrite = vault / "_alembic" / "yt2b-rewrite-in-my-voice.md"
    assert str(rewrite.resolve()) in result["written"]
    assert "brand-new-voice-4a2" in rewrite.read_text(encoding="utf-8")

    code, result = run(vault, "--force")
    assert code == 0
    assert str(target.resolve()) in result["written"] and result["skipped"] == []
    text = target.read_text(encoding="utf-8")
    assert "Repair the selected text" in text and "brand-new-voice-4a2" in text
    assert alembic_sync.existing_state(target) == "pristine"


def test_voice_change_refreshes_only_voice_dependent_files(tmp_path):
    vault = make_vault(tmp_path)
    run(vault)
    write_voice(vault, "second-voice-1b7")
    code, result = run(vault)
    assert code == 0
    written = {Path(p).name for p in result["written"]}
    unchanged = {Path(p).name for p in result["unchanged"]}
    assert "yt2b-rewrite-in-my-voice.md" in written
    assert "yt2b-fact-check-flags.md" in unchanged
    assert "yt2b-attribute-claims.md" in unchanged
    assert "yt2b-alt-text.md" in unchanged
    assert result["skipped"] == []


def test_stray_workflow_is_reported_not_deleted(tmp_path):
    vault = make_vault(tmp_path)
    stray = vault / "_alembic" / "yt2b-old-workflow.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("---\nname: Old\nid: yt2b-old-workflow\n---\nold body\n", encoding="utf-8")
    code, result = run(vault)
    assert code == 0
    assert stray.exists()
    assert any("yt2b-old-workflow.md" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Invalid input
# ---------------------------------------------------------------------------

def test_missing_template_dir_exits_2(tmp_path):
    vault = make_vault(tmp_path)
    code, result = run(vault, "--templates", str(tmp_path / "missing"))
    assert code == 2 and result == {}


def test_bad_template_exits_2(tmp_path):
    vault = make_vault(tmp_path)
    tdir = tmp_path / "templates"
    tdir.mkdir()
    (tdir / "broken.md").write_text(
        "---\nname: Broken\nid: yt2b-other\nprompt: \"{=SELECTION=}\"\nreplaceSelection: true\n"
        "humanize: false\nlinkDepth: 0\nproviderId: default-claude-cli\nyt2b_id: broken\n---\nbody\n",
        encoding="utf-8",
    )
    code, result = run(vault, "--templates", str(tdir))
    assert code == 2 and result == {}
    assert not (vault / "_alembic").exists() or not list((vault / "_alembic").glob("*.md"))


def test_unknown_vault_exits_2(tmp_path):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = alembic_sync.main(["--vault", str(tmp_path / "nowhere"), "--templates", str(tmp_path / "none")])
    assert code == 2
