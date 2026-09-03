#!/usr/bin/env python3
"""Environment check for the youtube-to-blog skill.

Usage:
    doctor.py [--vault PATH] [--json] [--print analyze-dir]

Runs every required and optional check (tools, video-analyzer, keys by name,
blog scripts and agents, browser, vault rooms, Obsidian plugins) and prints a
table on stderr plus exactly one JSON object on stdout:

    {ok, required_failures, warnings, analyze_dir, whisper_key, checks: [...]}

Each check is {name, status (ok | fail | warn | info), required, detail}.
Exit 0 when every required check passes, 4 otherwise, 2 for a bad vault path.
"--print analyze-dir" prints only the resolved video-analyzer path (exit 0 or 4).
Secret values are never read into the output; keys are reported by name only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

# Expected community plugin ids; the Image Layouts plugin registers as obsidian-image-layouts.
OBSIDIAN_PLUGINS = {"agent-client": ("agent-client",), "writers-alembic": ("writers-alembic",),
                    "writing-studio": ("writing-studio",), "image-layouts": ("image-layouts", "obsidian-image-layouts"),
                    "youtubetoblog-home": ("youtubetoblog-home",), "rss-dashboard": ("rss-dashboard",)}
SHIPPED_ROOMS = ("home", "queue", "approvals", "evaluations", "team", "templates")
RUNTIME_ROOMS = ("videos", "blogs")
BANANA_MARKETPLACE = "banana-claude-marketplace"
BANANA_PLUGIN = "banana-claude@banana-claude-marketplace"
PREFLIGHT_EXIT = {0: "ready", 2: "missing binaries", 3: "GOOGLE_API_KEY missing in its .env", 4: "binaries and key missing"}


class Report:
    """Collects check rows and derives the summary fields."""

    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, name: str, ok: bool, detail: str = "", required: bool = True, info: bool = False) -> None:
        if info:
            status = "info"
        else:
            status = "ok" if ok else ("fail" if required else "warn")
        self.checks.append({"name": name, "status": status, "required": required and not info, "detail": detail})

    @property
    def required_failures(self) -> list[str]:
        return [c["name"] for c in self.checks if c["status"] == "fail"]

    @property
    def warnings(self) -> list[str]:
        return [f"{c['name']}: {c['detail']}" for c in self.checks if c["status"] == "warn"]


def run_quiet(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess | None:
    """Run a tool with a timeout; None when it is missing or hangs."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def check_python(report: Report) -> None:
    version = ".".join(str(v) for v in sys.version_info[:3])
    report.add("python3 >= 3.11", sys.version_info >= (3, 11), version)


def check_binaries(report: Report) -> None:
    for name in ("yt-dlp", "ffmpeg", "ffprobe"):
        path = shutil.which(name)
        detail = path or "not on PATH"
        if path and name == "yt-dlp":
            proc = run_quiet([path, "--version"], timeout=20)
            if proc and proc.returncode == 0:
                detail = f"{path} ({proc.stdout.strip()})"
        report.add(name, bool(path), detail)


def check_analyze(report: Report) -> Path | None:
    analyze_dir = common.find_analyze_dir()
    report.add("video-analyzer", analyze_dir is not None, str(analyze_dir) if analyze_dir else "not found (set VIDEO_ANALYZER_DIR)")
    if analyze_dir is None:
        report.add("video-analyzer preflight", False, "skipped: analyzer not found")
        return None
    proc = run_quiet([sys.executable, str(analyze_dir / "scripts" / "preflight.py"), "--check"], timeout=60)
    code = proc.returncode if proc else -1
    report.add("video-analyzer preflight", code == 0, PREFLIGHT_EXIT.get(code, f"exit {code}"))
    return analyze_dir


def check_google_key(report: Report) -> None:
    present = common.key_present("GOOGLE_API_KEY")
    report.add("GOOGLE_API_KEY", present, "present (env or ~/.config/video-analyzer/.env)" if present else "missing: add it to ~/.config/video-analyzer/.env")


def check_blog_assets(report: Report) -> None:
    scripts = common.blog_scripts_dir()
    for name in common.BLOG_SCRIPTS:
        path = scripts / name
        report.add(f"blog script {name}", path.is_file(), str(path))
    agents = common.claude_home() / "agents"
    for name in common.BLOG_AGENTS:
        path = agents / name
        report.add(f"blog agent {name}", path.is_file(), str(path))


def check_browser(report: Report) -> None:
    driver = next((m for m in ("patchright", "playwright") if importlib.util.find_spec(m)), None)
    report.add("patchright or playwright", driver is not None, driver or "neither module imports")
    cache = Path.home() / ".cache" / "ms-playwright"
    chromium = sorted(cache.glob("chromium*")) if cache.is_dir() else []
    report.add("Chromium for the renderer", bool(chromium), str(chromium[-1]) if chromium else f"none under {cache}")


def check_optional_modules(report: Report) -> None:
    for module, why in (("yaml", "PyYAML: flat frontmatter parser is used instead"), ("PIL", "Pillow: hero cropping and thumbnail resizing are skipped")):
        found = importlib.util.find_spec(module) is not None
        report.add(module, found, "importable" if found else why, required=False)


def check_optional_keys(report: Report) -> bool:
    gai = common.key_present("GOOGLE_AI_API_KEY", env_file=None)
    report.add("GOOGLE_AI_API_KEY", gai, "present in env" if gai else "absent: generate_hero.py falls back to stock keys or Openverse", required=False)
    whisper = any(common.key_present(k) for k in common.WHISPER_KEYS)
    report.add("Whisper key (GROQ_API_KEY or OPENAI_API_KEY)", whisper,
               "present" if whisper else "absent: run analyze with --no-whisper", required=False)
    return whisper


def check_banana(report: Report) -> None:
    marketplace = common.claude_home() / "plugins" / "marketplaces" / BANANA_MARKETPLACE
    report.add("Banana Claude plugin", marketplace.is_dir(), str(marketplace) if marketplace.is_dir() else "not installed (optional AI images)", info=True)
    settings = common.claude_home() / "settings.json"
    state = "unknown"
    try:
        enabled = json.loads(settings.read_text(encoding="utf-8")).get("enabledPlugins", {})
        state = "enabled" if enabled.get(BANANA_PLUGIN) else "disabled"
    except (OSError, ValueError):
        state = "settings.json unreadable"
    report.add("Banana Claude enabled", state == "enabled", state, info=True)


def check_vault(report: Report, vault: Path) -> None:
    for key in SHIPPED_ROOMS:
        room = vault / common.ROOMS[key]
        report.add(f"room {common.ROOMS[key]}", room.is_dir(), "present" if room.is_dir() else "missing")
    for note in (common.SETTINGS_NOTE, common.HOME_NOTE):
        report.add(note, (vault / note).is_file(), "present" if (vault / note).is_file() else "missing")
    for key in RUNTIME_ROOMS:
        room = vault / common.ROOMS[key]
        report.add(f"room {common.ROOMS[key]}", room.is_dir(), "present" if room.is_dir() else "created on first run", info=True)


def check_obsidian_plugins(report: Report, vault: Path) -> None:
    listed: list[str] = []
    path = vault / ".obsidian" / "community-plugins.json"
    try:
        listed = list(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    for plugin, ids in OBSIDIAN_PLUGINS.items():
        found = next((i for i in ids if i in listed), None)
        report.add(f"obsidian plugin {plugin}", found is not None, f"listed as {found}" if found else "not listed in .obsidian/community-plugins.json", info=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_obsidian_plugin_integrity(report: Report, vault: Path) -> None:
    lock_path = vault / "_system" / "plugin-lock.json"
    enabled_path = vault / ".obsidian" / "community-plugins.json"
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        entries = {entry["id"]: entry for entry in lock_data.get("obsidian_plugins", [])}
    except (OSError, ValueError, KeyError, TypeError):
        report.add("obsidian plugin integrity lock", False, f"unreadable: {lock_path}")
        return
    try:
        enabled = set(json.loads(enabled_path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        enabled = set()

    for plugin_id in ("writing-studio", "youtubetoblog-home", "rss-dashboard"):
        entry = entries.get(plugin_id)
        failures: list[str] = []
        if plugin_id not in enabled:
            failures.append("not enabled in community-plugins.json")
        if not entry:
            failures.append("missing lock entry")
        else:
            for name, expected in entry.get("files", {}).items():
                installed = vault / ".obsidian" / "plugins" / plugin_id / name
                if not installed.is_file():
                    failures.append(f"missing {name}")
                elif file_sha256(installed) != expected:
                    failures.append(f"hash mismatch {name}")
        if entry and entry.get("patch"):
            patch = entry.get("patch", {})
            patch_path = vault / str(patch.get("path", ""))
            expected_patch = patch.get("sha256")
            if not patch_path.is_file():
                failures.append("missing safety patch")
            elif not expected_patch or file_sha256(patch_path) != expected_patch:
                failures.append("patch hash mismatch")
        if plugin_id == "rss-dashboard" and entry:
            bundle = vault / ".obsidian" / "plugins" / plugin_id / "main.js"
            if bundle.is_file() and "Refusing to overwrite existing article:" not in bundle.read_text(encoding="utf-8"):
                failures.append("no-overwrite guard absent")
            if bundle.is_file() and "titleYaml" not in bundle.read_text(encoding="utf-8"):
                failures.append("YAML metadata guard absent")
            data_path = vault / ".obsidian" / "plugins" / plugin_id / "data.json"
            try:
                data = json.loads(data_path.read_text(encoding="utf-8"))
                template = data["articleSaving"]["defaultTemplate"]
                safe_tokens = (
                    "{{titleYaml}}",
                    "{{linkYaml}}",
                    "{{feedTitleYaml}}",
                    "{{authorYaml}}",
                    "{{yt2bTagsYaml}}",
                )
                if not all(token in template for token in safe_tokens):
                    failures.append("active save template lacks safe YAML placeholders")
            except (OSError, ValueError, KeyError, TypeError):
                failures.append("active RSS save template unreadable")
        if plugin_id == "writing-studio" and entry:
            bundle = vault / ".obsidian" / "plugins" / plugin_id / "main.js"
            guard = "if (this.plugin.settings.openOnStartup) {"
            if bundle.is_file() and guard not in bundle.read_text(encoding="utf-8"):
                failures.append("workspace-restore startup guard absent")
        report.add(
            f"obsidian plugin {plugin_id} integrity",
            not failures,
            ", ".join(failures) if failures else "installed files match the lock",
        )


def check_root_docs(report: Report, vault: Path) -> None:
    for name in ("BRAND.md", "VOICE.md"):
        present = (vault / name).is_file()
        report.add(name, present, "present" if present else "missing: run /youtube-to-blog setup", info=True)


def print_table(report: Report) -> None:
    labels = {"ok": "OK  ", "fail": "FAIL", "warn": "WARN", "info": "INFO"}
    for row in report.checks:
        common.warn(f"[{labels[row['status']]}] {row['name']}: {row['detail']}")


def build_report(vault: Path) -> tuple[Report, Path | None, bool]:
    report = Report()
    check_python(report)
    check_binaries(report)
    analyze_dir = check_analyze(report)
    check_google_key(report)
    check_blog_assets(report)
    check_browser(report)
    check_optional_modules(report)
    whisper = check_optional_keys(report)
    check_banana(report)
    check_vault(report, vault)
    check_obsidian_plugins(report, vault)
    check_obsidian_plugin_integrity(report, vault)
    check_root_docs(report, vault)
    return report, analyze_dir, whisper


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the youtube-to-blog environment.")
    parser.add_argument("--vault", help="Vault root (default: detected from the working directory)")
    parser.add_argument("--json", action="store_true", help="Accepted for compatibility; JSON is always printed on stdout")
    parser.add_argument("--print", dest="print_what", choices=["analyze-dir"], help="Print only the resolved path")
    args = parser.parse_args(argv)

    if args.print_what == "analyze-dir":
        analyze_dir = common.find_analyze_dir()
        if analyze_dir is None:
            common.warn("video-analyzer not found (set VIDEO_ANALYZER_DIR)")
            return common.EXIT_MISSING
        sys.stdout.write(str(analyze_dir) + "\n")
        return common.EXIT_OK

    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
    except FileNotFoundError as exc:
        return common.fail(common.EXIT_INPUT, str(exc))
    if not vault.is_dir():
        return common.fail(common.EXIT_INPUT, f"vault path is not a directory: {vault}")

    report, analyze_dir, whisper = build_report(vault)
    print_table(report)
    ok = not report.required_failures
    common.emit({
        "ok": ok,
        "required_failures": report.required_failures,
        "warnings": report.warnings,
        "analyze_dir": str(analyze_dir) if analyze_dir else None,
        "whisper_key": whisper,
        "vault": str(vault),
        "checks": report.checks,
    })
    return common.EXIT_OK if ok else common.EXIT_MISSING


if __name__ == "__main__":
    sys.exit(main())
