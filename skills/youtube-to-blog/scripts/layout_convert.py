#!/usr/bin/env python3
"""Convert Image Layouts fenced blocks to HTML figure groups and back.

--to html (default): every fenced block whose info string is `image-layout`
or starts with `image-layout-` becomes

    <figure class="yt2b-layout image-layout-<name>">
    <figure><img src="images/<file>" alt="..."><figcaption>...</figcaption></figure>
    <img src="images/<file>" alt="...">
    <figcaption>group caption</figcaption>
    </figure>

one element per line. Wikilinks `![[file|caption]]` resolve to `images/<file>`
when that file exists under images/ next to the markdown; markdown images pass
through. Options `caption`, `descriptions`, `fit`, `align` and `width` survive
the round trip (fit, align and width as `yt2b-*` classes); other options are
dropped with a warning. Any other fenced block is left untouched.

--to obsidian reverses the conversion.

Exit codes: 0 ok, 1 failure, 2 invalid input.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
WIKI_IMG_RE = re.compile(r"^!\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]\s*$")
MD_IMG_RE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)\s*$')
FIT_VALUES = ("cover", "contain", "natural")
ALIGN_VALUES = ("left", "center", "right")
GROUP_OPEN_RE = re.compile(r'^<figure class="yt2b-layout image-layout-([a-z0-9-]+)((?:\s+yt2b-[^"\s]+)*)">\s*$')
NESTED_RE = re.compile(r'^<figure><img src="([^"]*)" alt="([^"]*)"><figcaption>(.*?)</figcaption></figure>\s*$')
IMG_RE = re.compile(r'^<img src="([^"]*)" alt="([^"]*)">\s*$')
CAPTION_RE = re.compile(r"^<figcaption>(.*?)</figcaption>\s*$")
GROUP_CLOSE = "</figure>"


def _esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def _fence_closes(line: str, marker: str) -> bool:
    m = re.match(r"^(`{3,}|~{3,})\s*$", line)
    return bool(m) and m.group(1)[0] == marker[0] and len(m.group(1)) >= len(marker)


def parse_block(info: str, lines: list[str], md_dir: Path | None) -> tuple[str, dict, list[dict], list[str]]:
    """Return (layout name, options, images, warnings) for one fenced block."""
    warnings: list[str] = []
    options: dict = {}
    body = list(lines)
    if body and body[0].strip() == "---":
        try:
            end = next(i for i in range(1, len(body)) if body[i].strip() == "---")
        except StopIteration:
            end = len(body)
        options = common.parse_frontmatter("\n".join(body[1:end])) or {}
        body = body[end + 1:]
    name = info[len("image-layout"):].lstrip("-").strip()
    if not name:
        name = str(options.get("layout") or "single").strip()
    descriptions = options.get("descriptions")
    if isinstance(descriptions, str):
        descriptions = [d.strip() for d in descriptions.split(",")]
    if not isinstance(descriptions, list):
        descriptions = []
    images: list[dict] = []
    for raw in body:
        line = raw.strip()
        if not line:
            continue
        wm = WIKI_IMG_RE.match(line)
        mm = MD_IMG_RE.match(line)
        if wm:
            target = wm.group(1).strip().split("#")[0]
            alias = (wm.group(2) or "").strip()
            caption = "" if re.fullmatch(r"\d+(x\d+)?", alias) else alias
            base = Path(target).name
            if md_dir is not None and (md_dir / "images" / base).is_file():
                src = f"images/{base}"
            elif md_dir is not None and (md_dir / target).is_file():
                src = Path(target).as_posix()
            else:
                src = f"images/{base}"
                warnings.append(f"image not found under images/: {base}")
            images.append({"src": src, "alt": caption or base, "caption": caption})
        elif mm:
            images.append({"src": mm.group(2), "alt": mm.group(1), "caption": mm.group(3) or ""})
        else:
            warnings.append(f"ignored line in layout block: {line[:60]}")
    for i, desc in enumerate(descriptions):
        if i < len(images) and not images[i]["caption"] and str(desc).strip():
            images[i]["caption"] = str(desc).strip()
    for key in options:
        if key not in ("caption", "descriptions", "fit", "align", "width", "layout"):
            warnings.append(f"option '{key}' is Obsidian-only and was dropped")
    return name, options, images, warnings


def block_to_html(name: str, options: dict, images: list[dict]) -> str:
    classes = ["yt2b-layout", f"image-layout-{name}"]
    fit = str(options.get("fit") or "").strip().lower()
    if fit in FIT_VALUES:
        classes.append(f"yt2b-fit-{fit}")
    align = str(options.get("align") or "").strip().lower()
    if align in ALIGN_VALUES:
        classes.append(f"yt2b-align-{align}")
    width = str(options.get("width") or "").strip()
    if width and re.fullmatch(r"[0-9.]+(px|%|em|rem)?", width):
        classes.append(f"yt2b-width-{width}")
    out = [f'<figure class="{" ".join(classes)}">']
    for img in images:
        tag = f'<img src="{_esc(img["src"])}" alt="{_esc(img["alt"])}">'
        if img["caption"]:
            out.append(f"<figure>{tag}<figcaption>{_esc(img['caption'])}</figcaption></figure>")
        else:
            out.append(tag)
    caption = str(options.get("caption") or "").strip()
    if caption:
        out.append(f"<figcaption>{_esc(caption)}</figcaption>")
    out.append(GROUP_CLOSE)
    return "\n".join(out)


def convert_to_html(text: str, md_dir: Path | None) -> tuple[str, int, list[str]]:
    lines = text.split("\n")
    out: list[str] = []
    warnings: list[str] = []
    count = 0
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        marker, rest = m.group(1), m.group(2).strip()
        info = rest.split()[0] if rest else ""
        j = i + 1
        while j < len(lines) and not _fence_closes(lines[j], marker):
            j += 1
        if j >= len(lines):
            out.extend(lines[i:])
            break
        if info == "image-layout" or info.startswith("image-layout-"):
            name, options, images, warns = parse_block(info, lines[i + 1:j], md_dir)
            warnings.extend(warns)
            out.append(block_to_html(name, options, images))
            count += 1
        else:
            out.extend(lines[i:j + 1])
        i = j + 1
    return "\n".join(out), count, warnings


def group_to_block(name: str, extra_classes: str, inner: list[str]) -> str:
    options: dict = {}
    for cls in extra_classes.split():
        if cls.startswith("yt2b-fit-"):
            options["fit"] = cls[len("yt2b-fit-"):]
        elif cls.startswith("yt2b-align-"):
            options["align"] = cls[len("yt2b-align-"):]
        elif cls.startswith("yt2b-width-"):
            options["width"] = cls[len("yt2b-width-"):]
    images: list[tuple[str, str]] = []
    for line in inner:
        nm = NESTED_RE.match(line)
        im = IMG_RE.match(line)
        cm = CAPTION_RE.match(line)
        if nm:
            images.append((html.unescape(nm.group(1)), html.unescape(nm.group(3))))
        elif im:
            images.append((html.unescape(im.group(1)), ""))
        elif cm:
            options["caption"] = html.unescape(cm.group(1))
    lines = [f"```image-layout-{name}"]
    ordered = {k: options[k] for k in ("caption", "fit", "align", "width") if k in options}
    if ordered:
        lines.append("---")
        lines.append(common.dump_frontmatter(ordered).rstrip("\n"))
        lines.append("---")
    for src, caption in images:
        target = src[len("images/"):] if src.startswith("images/") else src
        lines.append(f"![[{target}|{caption}]]" if caption else f"![[{target}]]")
    lines.append("```")
    return "\n".join(lines)


def convert_to_obsidian(text: str) -> tuple[str, int, list[str]]:
    lines = text.split("\n")
    out: list[str] = []
    warnings: list[str] = []
    count = 0
    i = 0
    while i < len(lines):
        m = GROUP_OPEN_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() != GROUP_CLOSE:
            j += 1
        if j >= len(lines):
            warnings.append("unterminated yt2b-layout figure left untouched")
            out.extend(lines[i:])
            break
        out.append(group_to_block(m.group(1), m.group(2) or "", lines[i + 1:j]))
        count += 1
        i = j + 1
    return "\n".join(out), count, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--md", required=True, help="Markdown source")
    parser.add_argument("--out", required=True, help="Output path")
    parser.add_argument("--to", choices=("html", "obsidian"), default="html")
    args = parser.parse_args(argv)
    src = Path(args.md).expanduser()
    if not src.is_file():
        return common.fail(common.EXIT_INPUT, f"markdown not found: {src}")
    out_path = Path(args.out).expanduser()
    text = src.read_text(encoding="utf-8")
    if args.to == "html":
        result, count, warnings = convert_to_html(text, src.resolve().parent)
    else:
        result, count, warnings = convert_to_obsidian(text)
    for w in warnings:
        common.warn(w)
    common.ensure_dir(out_path.parent)
    out_path.write_text(result, encoding="utf-8")
    common.emit({"blocks": count, "out": str(out_path.resolve()), "to": args.to, "warnings": warnings})
    return common.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
