#!/usr/bin/env python3
"""Render the YT2B Writers Alembic workflows into the vault's _alembic/ folder.

Templates live in skills/youtube-to-blog/references/alembic/*.md. Each carries
the Alembic frontmatter (name, id, prompt, replaceSelection, humanize,
linkDepth, providerId) plus a yt2b_id line, and a system prompt body that may
contain {{VOICE}} and {{BRAND}}. Those placeholders are filled from the body of
the root VOICE.md and BRAND.md (written by the setup command) or from the
neutral fallback text below when a file is missing or empty.

Every rendered workflow gets a yt2b_hash property. On the next run a workflow
whose content still matches its hash is refreshed in place when the template
or the voice changed; one the user edited is kept and listed under "skipped"
unless --force is given.

Usage:
    alembic_sync.py [--vault PATH] [--force] [--templates DIR]

Prints exactly one JSON object on stdout:
    {"written": [...], "skipped": [...], "unchanged": [...],
     "voice_source": "root|neutral", "brand_source": "root|neutral",
     "alembic_dir": "...", "warnings": [...]}

Exit codes: 0 ok, 1 generic failure, 2 invalid input (no templates, bad
template). Standard library only; PyYAML is optional through yt2b_common.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "references" / "alembic"
ALEMBIC_KEYS = ("name", "id", "prompt", "replaceSelection", "humanize", "linkDepth", "providerId")
REQUIRED_KEYS = ALEMBIC_KEYS + ("yt2b_id",)
HASH_KEY = "yt2b_hash"
PLACEHOLDER_RE = re.compile(r"\{\{[A-Za-z0-9_]+\}\}")
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

NEUTRAL_VOICE = """Neutral voice (no VOICE.md at the vault root yet; run the youtube-to-blog setup command, then alembic_sync.py, to replace this):
- Second person for the reader. First person only for the author's own verified experience.
- Contractions allowed. Sentences average under 20 words and never pass 30. Paragraphs under 120 words.
- Concrete nouns and verbs. No hype, no rhetorical questions, no exclamation marks.
- Summary label: Key Takeaways.
- Taboo phrases: in today's fast-paced world, game-changer, unlock the power, it's important to note, in conclusion, delve into, seamlessly, cutting-edge, revolutionize.
- Never use em dashes or en dashes."""

NEUTRAL_BRAND = """Neutral brand (no BRAND.md at the vault root yet):
- Audience: practitioners who searched for this topic and want the answer without watching the whole video.
- Positioning: none. Do not promote a product, a service or the author. Name the video's creator as the source.
- Disclosure: say when the article is a companion to someone else's video."""

CONTEXT_FILES = {"VOICE": ("VOICE.md", NEUTRAL_VOICE), "BRAND": ("BRAND.md", NEUTRAL_BRAND)}


class TemplateError(ValueError):
    """A template is missing a key or breaks the naming rules."""


# ---------------------------------------------------------------------------
# Root context (VOICE.md, BRAND.md)
# ---------------------------------------------------------------------------

def clean_context_body(text: str) -> str:
    """Body of a root context file without frontmatter, its H1 and the auto-load note."""
    _, body = common.split_frontmatter(text)
    kept: list[str] = []
    in_head = True
    for line in body.splitlines():
        stripped = line.strip()
        if in_head:
            if not stripped or stripped.startswith("# ") or stripped.startswith("> This file is auto-loaded"):
                continue
            in_head = False
        kept.append(line.rstrip())
    return "\n".join(kept).strip()


def _injection_scan(text: str) -> list[str]:
    """Reuse the blog helper's instruction-pattern scan when it is installed."""
    helper = Path.home() / ".claude" / "scripts" / "load_untrusted_root.py"
    if not helper.is_file():
        return []
    try:
        spec = importlib.util.spec_from_file_location("yt2b_load_untrusted_root", helper)
        if spec is None or spec.loader is None:
            return []
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return [str(m) for m in module.scan_for_injection(text)]
    except Exception:  # pragma: no cover
        return []


def load_context(vault: Path, key: str) -> tuple[str, str, list[str]]:
    """Return (text, source, warnings) for VOICE or BRAND; source is root or neutral."""
    basename, fallback = CONTEXT_FILES[key]
    path = vault / basename
    warnings: list[str] = []
    if path.is_symlink() or not path.is_file():
        return fallback, "neutral", warnings
    try:
        body = clean_context_body(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        warnings.append(f"{basename}: unreadable ({exc}); neutral fallback used")
        return fallback, "neutral", warnings
    if not body:
        warnings.append(f"{basename}: empty body; neutral fallback used")
        return fallback, "neutral", warnings
    if PLACEHOLDER_RE.search(body):
        warnings.append(f"{basename}: unfilled {{{{placeholders}}}} remain; finish the setup interview")
    hits = _injection_scan(body)
    if hits:
        warnings.append(f"{basename}: instruction-shaped text found ({', '.join(hits[:5])}); review it before use")
    return body, "root", warnings


# ---------------------------------------------------------------------------
# Rendering and hashing
# ---------------------------------------------------------------------------

def content_hash(frontmatter: dict, body: str) -> str:
    """Stable hash over the workflow properties (without the hash itself) and the body."""
    payload = {
        "fm": {k: v for k, v in frontmatter.items() if k != HASH_KEY},
        "body": body.strip(),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:16]


def render_template(path: Path, voice: str, brand: str) -> tuple[dict, str]:
    """Render one template file into (frontmatter, body) ready for write_note."""
    fm, body = common.read_note(path)
    missing = [k for k in REQUIRED_KEYS if k not in fm]
    if missing:
        raise TemplateError(f"{path.name}: missing frontmatter keys {missing}")
    yt2b_id = str(fm["yt2b_id"]).strip()
    if not ID_RE.fullmatch(yt2b_id):
        raise TemplateError(f"{path.name}: yt2b_id must be lowercase letters, digits and hyphens")
    if fm["id"] != f"yt2b-{yt2b_id}":
        raise TemplateError(f"{path.name}: id must be yt2b-{yt2b_id}")
    depth = fm["linkDepth"]
    if not isinstance(depth, int) or isinstance(depth, bool) or not 0 <= depth <= 3:
        raise TemplateError(f"{path.name}: linkDepth must be an integer from 0 to 3")
    for key in ("replaceSelection", "humanize"):
        if not isinstance(fm[key], bool):
            raise TemplateError(f"{path.name}: {key} must be true or false")
    prompt = str(fm["prompt"])
    if "{=SELECTION=}" not in prompt and "{=CONTEXT=}" not in prompt:
        raise TemplateError(f"{path.name}: prompt needs {{=SELECTION=}} or {{=CONTEXT=}}")
    if not body.strip():
        raise TemplateError(f"{path.name}: empty system prompt body")
    rendered = body.replace("{{VOICE}}", voice).replace("{{BRAND}}", brand).strip() + "\n"
    out_fm = {k: fm[k] for k in REQUIRED_KEYS}
    out_fm[HASH_KEY] = content_hash(out_fm, rendered)
    return out_fm, rendered


def existing_state(path: Path) -> str:
    """missing, pristine (matches its yt2b_hash) or edited (changed by hand or no hash)."""
    if not path.exists():
        return "missing"
    try:
        fm, body = common.read_note(path)
    except (OSError, UnicodeDecodeError):
        return "edited"
    stored = fm.get(HASH_KEY)
    if not stored:
        return "edited"
    return "pristine" if content_hash(fm, body) == stored else "edited"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync(vault: Path, template_dir: Path, force: bool = False) -> dict:
    templates = sorted(p for p in template_dir.glob("*.md") if p.is_file())
    if not templates:
        raise TemplateError(f"no templates found in {template_dir}")
    voice, voice_source, warnings = load_context(vault, "VOICE")
    brand, brand_source, brand_warnings = load_context(vault, "BRAND")
    warnings.extend(brand_warnings)

    alembic_dir = common.ensure_dir(vault / common.ROOMS["alembic"])
    written: list[str] = []
    skipped: list[str] = []
    unchanged: list[str] = []
    seen_ids: set[str] = set()
    expected_files: set[str] = set()

    for template in templates:
        fm, body = render_template(template, voice, brand)
        if fm["id"] in seen_ids:
            raise TemplateError(f"{template.name}: duplicate id {fm['id']}")
        seen_ids.add(fm["id"])
        target = alembic_dir / f"{fm['id']}.md"
        expected_files.add(target.name)
        if PLACEHOLDER_RE.search(body):
            warnings.append(f"{target.name}: rendered body still contains a {{{{placeholder}}}}")
        state = existing_state(target)
        if state == "pristine":
            current_fm, _ = common.read_note(target)
            if current_fm.get(HASH_KEY) == fm[HASH_KEY]:
                unchanged.append(str(target.resolve()))
                continue
        elif state == "edited" and not force:
            skipped.append(str(target.resolve()))
            continue
        common.write_note(target, fm, body)
        written.append(str(target.resolve()))

    for stray in sorted(alembic_dir.glob("yt2b-*.md")):
        if stray.name not in expected_files:
            warnings.append(f"{stray.name}: no template with this id (left untouched)")

    return {
        "written": written,
        "skipped": skipped,
        "unchanged": unchanged,
        "voice_source": voice_source,
        "brand_source": brand_source,
        "alembic_dir": str(alembic_dir.resolve()),
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="Vault root (default: found from the current directory)")
    parser.add_argument("--force", action="store_true", help="Overwrite workflows the user edited")
    parser.add_argument("--templates", help=f"Template folder (default: {TEMPLATE_DIR})")
    args = parser.parse_args(argv)

    try:
        vault = Path(args.vault).resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        print(f"alembic_sync: {exc}", file=sys.stderr)
        return 2
    template_dir = Path(args.templates).resolve() if args.templates else TEMPLATE_DIR
    if not template_dir.is_dir():
        print(f"alembic_sync: template folder not found: {template_dir}", file=sys.stderr)
        return 2

    try:
        result = sync(vault, template_dir, force=args.force)
    except TemplateError as exc:
        print(f"alembic_sync: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"alembic_sync: {exc}", file=sys.stderr)
        return 1

    for warning in result["warnings"]:
        print(f"alembic_sync: warning: {warning}", file=sys.stderr)
    print(
        f"alembic_sync: voice {result['voice_source']}, brand {result['brand_source']}: "
        f"{len(result['written'])} written, {len(result['unchanged'])} unchanged, "
        f"{len(result['skipped'])} kept (user-edited)",
        file=sys.stderr,
    )
    common.emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
