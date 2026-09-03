"""Tests for layout_convert.py: round trip, other fences untouched, options."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import yt2b_common as common  # noqa: E402

lc = common.load_module(SCRIPTS / "layout_convert.py", "yt2b_layout_convert_test")

SOURCE = """Intro paragraph.

```image-layout-a
---
caption: Before and after the refactor
fit: contain
align: center
---
![[03-before-0412.jpg|Before]]
![[04-after-0455.jpg|After: the fix]]
```

```bash
echo untouched
```

````markdown
```image-layout-h
![[x.jpg]]
```
````

End.
"""

EXPECTED_GROUP = """<figure class="yt2b-layout image-layout-a yt2b-fit-contain yt2b-align-center">
<figure><img src="images/03-before-0412.jpg" alt="Before"><figcaption>Before</figcaption></figure>
<figure><img src="images/04-after-0455.jpg" alt="After: the fix"><figcaption>After: the fix</figcaption></figure>
<figcaption>Before and after the refactor</figcaption>
</figure>"""


def run_script(*args):
    proc = subprocess.run([sys.executable, str(SCRIPTS / "layout_convert.py"), *map(str, args)], capture_output=True, text=True)
    lines = [line for line in proc.stdout.strip().splitlines() if line.strip()]
    return proc.returncode, (json.loads(lines[-1]) if lines else {}), proc.stderr


def make_md(tmp_path: Path, text: str = SOURCE) -> Path:
    (tmp_path / "images").mkdir(exist_ok=True)
    for name in ("03-before-0412.jpg", "04-after-0455.jpg", "x.jpg"):
        (tmp_path / "images" / name).write_bytes(b"jpg")
    md = tmp_path / "post.md"
    md.write_text(text, encoding="utf-8")
    return md


def test_round_trip_with_options_and_captions(tmp_path):
    md = make_md(tmp_path)
    out = tmp_path / ".render" / "post.md"
    code, data, err = run_script("--md", md, "--out", out, "--to", "html")
    assert code == 0, err
    assert data["blocks"] == 1 and Path(data["out"]) == out.resolve()
    html_text = out.read_text(encoding="utf-8")
    assert EXPECTED_GROUP in html_text
    assert "```bash\necho untouched\n```" in html_text, "other fences stay untouched"
    assert "````markdown\n```image-layout-h\n![[x.jpg]]\n```\n````" in html_text, "nested example fence stays untouched"
    back = tmp_path / "back.md"
    code, data, err = run_script("--md", out, "--out", back, "--to", "obsidian")
    assert code == 0, err
    assert data["blocks"] == 1
    assert back.read_text(encoding="utf-8") == SOURCE
    twice = tmp_path / "twice.md"
    code, data, _ = run_script("--md", out, "--out", twice, "--to", "html")
    assert data["blocks"] == 0 and twice.read_text(encoding="utf-8") == html_text, "html to html is a no-op"


def test_descriptions_markdown_images_and_bare_block(tmp_path):
    text = """```image-layout-d
---
descriptions: [One, Two, Three]
---
![[03-before-0412.jpg]]
![Alt text](images/04-after-0455.jpg "Explicit caption")
![[missing.jpg|Gone]]
```

```image-layout
---
layout: masonry-3
caption: Grid
---
![[x.jpg|X]]
```
"""
    md = make_md(tmp_path, text)
    converted, count, warnings = lc.convert_to_html(md.read_text(encoding="utf-8"), tmp_path)
    assert count == 2
    assert '<figure class="yt2b-layout image-layout-d">' in converted
    assert '<figure><img src="images/03-before-0412.jpg" alt="03-before-0412.jpg"><figcaption>One</figcaption></figure>' in converted
    assert '<figure><img src="images/04-after-0455.jpg" alt="Alt text"><figcaption>Explicit caption</figcaption></figure>' in converted
    assert '<figure><img src="images/missing.jpg" alt="Gone"><figcaption>Gone</figcaption></figure>' in converted
    assert any("missing.jpg" in w for w in warnings)
    assert '<figure class="yt2b-layout image-layout-masonry-3">' in converted
    assert "<figcaption>Grid</figcaption>" in converted
    back, n, _ = lc.convert_to_obsidian(converted)
    assert n == 2 and "```image-layout-masonry-3" in back and "![[x.jpg|X]]" in back


def test_html_escaping(tmp_path):
    text = '```image-layout-a\n---\ncaption: A & B <c>\n---\n![[03-before-0412.jpg|Quote "here"]]\n![[04-after-0455.jpg|Two]]\n```\n'
    converted, count, _ = lc.convert_to_html(text, make_md(tmp_path, text).parent)
    assert count == 1
    assert "<figcaption>A &amp; B &lt;c&gt;</figcaption>" in converted
    assert 'alt="Quote &quot;here&quot;"' in converted
    back, _, _ = lc.convert_to_obsidian(converted)
    assert 'Quote "here"' in back and "A & B <c>" in back
