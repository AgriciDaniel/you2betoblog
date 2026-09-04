"""Browser harness for the real Home plugin source, not native Obsidian.

Requires an installed patchright Chromium. All browser network traffic is
blocked. Synthetic vault and icon APIs isolate layout and navigation behavior.
"""

from pathlib import Path
import json
import tempfile
from patchright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[3]
out = Path(tempfile.mkdtemp(prefix="yt2b-dashboard-browser-"))
bootstrap = r"""
window.module={exports:{}};
window.notices=[];window.opened=[];
for(const name of ['notices','opened']){window[name].push=function(...items){const n=Array.prototype.push.apply(this,items);document.body.dataset[name]=JSON.stringify(this);return n};document.body.dataset[name]='[]'}
for(const [name,tag] of [['createDiv','div'],['createSpan','span']]) HTMLElement.prototype[name]=function(o={}){return this.createEl(tag,o)};
HTMLElement.prototype.createEl=function(tag,o={}){const e=document.createElement(tag);if(o.cls)e.className=o.cls;if(o.text)e.textContent=o.text;if(o.type)e.type=o.type;if(o.placeholder)e.placeholder=o.placeholder;this.append(e);return e};
HTMLElement.prototype.empty=function(){this.replaceChildren()};
HTMLElement.prototype.addClass=function(c){this.classList.add(c)};
HTMLElement.prototype.removeClass=function(c){this.classList.remove(c)};
window.require=()=>({Plugin:class{},ItemView:class{constructor(leaf){this.contentEl=leaf}},PluginSettingTab:class{},Setting:class{},Notice:class{constructor(t){window.notices.push(t)}},normalizePath:x=>x,setIcon:(el,name)=>{el.textContent='○';el.dataset.icon=name;el.setAttribute('aria-hidden','true')}});
"""
setup = r"""
const p=new module.exports();
p.settings={wordmark:'you2toblog',defaultRights:'ask',defaultMode:'companion',showRecentRuns:true};
p.app={vault:{getFileByPath:path=>({path}),getMarkdownFiles:()=>[]},metadataCache:{getFileCache:()=>({frontmatter:{default_rights:'ask',default_mode:'companion'}})},workspace:{getLeaf:()=>({openFile:async f=>window.opened.push(f.path)})}};
p.recentRuns=()=>[{title:'A sample video with a long title to check narrow layouts',status:'briefed',updated:'2026-09-05',path:'02 Videos/sample/run.md'}];
p.pipelineCounts=()=>({queue:0,active:1,approvals:0,blogs:0});
p.runCommand=(id)=>{window.opened.push(id);return true};
p.openHome=async()=>window.opened.push('home');
p.queueActiveSource=async()=>window.notices.push('Open a saved YouTube source note first.');
window.home=new HomeView(document.querySelector('#main'),p);home.render();
window.sidebar=new SidebarView(document.querySelector('#sidebar'),p);sidebar.render();
"""
base = """<style>:root{--background-primary:#202020;--background-secondary:#252525;--text-normal:#eee;--text-muted:#bbb;--text-faint:#aaa;--background-modifier-border:#555;--interactive-accent:#ef4444;--background-modifier-hover:#373737;--font-interface:Arial}*{box-sizing:border-box}body{margin:0;background:#202020;color:#eee;font-family:Arial}#layout{height:100vh;display:grid;grid-template-columns:260px minmax(0,1fr)}#sidebar{overflow:auto}#main{min-width:0}button,input{font:inherit}button{cursor:pointer}button:focus-visible{outline:2px solid white}</style><div id="layout"><div id="sidebar"></div><div id="main"></div></div>"""
results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.route("**/*", lambda route: route.abort())
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(base)
    page.add_style_tag(
        content=(root / "plugins/youtubetoblog-home/styles.css").read_text()
    )
    page.add_script_tag(content=bootstrap)
    page.add_script_tag(
        content=(root / "plugins/youtubetoblog-home/main.js").read_text()
    )
    page.add_script_tag(content=setup)
    page.get_by_role("textbox", name="YouTube video URL").fill("not a video")
    page.get_by_role("button", name="Process", exact=True).click()
    assert "Paste a valid YouTube video link." in json.loads(
        page.locator("body").get_attribute("data-notices")
    )
    page.get_by_role("button", name="third-party", exact=True).click()
    assert (
        page.get_by_role("button", name="third-party", exact=True).get_attribute(
            "aria-pressed"
        )
        == "true"
    )
    assert (
        page.get_by_role("button", name="ask", exact=True).get_attribute("aria-pressed")
        == "false"
    )
    page.get_by_role("button", name="Setup and help", exact=True).click()
    assert "00 Home/Home.md" in json.loads(
        page.locator("body").get_attribute("data-opened")
    )
    for name in [
        "Feeds",
        "Discover",
        "Sources",
        "Queue",
        "Videos",
        "Blogs",
        "Approvals",
        "Evaluations",
        "Settings",
    ]:
        page.locator("#sidebar").get_by_role("button", name=name, exact=True).click()
    page.locator(".yt2b-home-recent-row").focus()
    page.keyboard.press("Enter")
    assert "02 Videos/sample/run.md" in json.loads(
        page.locator("body").get_attribute("data-opened")
    )
    for width, height in [(1440, 1000), (900, 700), (640, 700)]:
        page.set_viewport_size({"width": width, "height": height})
        page.screenshot(path=str(out / f"dashboard-{width}.png"))
        assert (
            page.get_by_role("textbox", name="YouTube video URL").bounding_box()[
                "height"
            ]
            >= 44
        )
        overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth")
        assert not overflow, f"horizontal overflow at {width}"
        results.append(
            {"width": width, "height": height, "horizontal_overflow": overflow}
        )
    assert not errors, errors
    results.append(
        {
            "page_errors": errors,
            "navigation_targets": len(
                json.loads(page.locator("body").get_attribute("data-opened"))
            ),
            "checks": [
                "invalid URL feedback",
                "chip aria state",
                "setup help",
                "nine sidebar routes",
                "keyboard recent run",
            ],
        }
    )
    browser.close()
(out / "results.json").write_text(
    json.dumps(
        {"kind": "browser harness, not native Obsidian", "results": results}, indent=2
    )
)
print(json.dumps({"output": str(out), "results": results}))
