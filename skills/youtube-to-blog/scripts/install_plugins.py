#!/usr/bin/env python3
"""Reproduce and install the vault's pinned Obsidian plugin set.

The default plan is read-only. `install` writes only inside the selected
vault's .obsidian folder. Patched plugins are built from pinned upstream Git
commits, every installed bundle is checked against _system/plugin-lock.json,
and an existing plugin is moved to a timestamped backup before replacement.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402

FILES = ("manifest.json", "main.js", "styles.css")
PATCHED = ("writing-studio", "rss-dashboard")
LOCAL = "youtubetoblog-home"
CORE = ("agent-client", "writers-alembic", "writing-studio", "obsidian-image-layouts", LOCAL)
ALL = CORE + ("rss-dashboard",)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_lock(vault: Path) -> dict[str, dict]:
    data = common.json_load(vault / "_system" / "plugin-lock.json", {}) or {}
    return {str(item.get("id")): item for item in data.get("obsidian_plugins") or [] if isinstance(item, dict)}


def run_checked(args: list[str], cwd: Path, timeout: int = 600) -> None:
    proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[-4000:]
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{detail}")


def verify_files(source: Path, entry: dict) -> None:
    failures = []
    for name, expected in (entry.get("files") or {}).items():
        path = source / name
        if not path.is_file():
            failures.append(f"missing {name}")
        elif sha256(path) != expected:
            failures.append(f"hash mismatch {name}")
    if failures:
        raise RuntimeError(f"{entry.get('id')} output does not match lock: {', '.join(failures)}")


def clone_pinned(entry: dict, destination: Path) -> None:
    version = str(entry.get("version") or "")
    source = str(entry.get("source") or "")
    commit = str(entry.get("upstream_commit") or "")
    if not source.startswith("https://github.com/") or not commit:
        raise RuntimeError(f"{entry.get('id')} needs an official GitHub source and upstream_commit")
    run_checked(["git", "clone", "--depth", "1", "--branch", version, source, str(destination)], destination.parent)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(destination), text=True).strip()
    if actual != commit:
        raise RuntimeError(f"{entry.get('id')} resolved {actual}, expected {commit}")


def apply_patch(vault: Path, source: Path, entry: dict) -> None:
    patch_info = entry.get("patch") or {}
    patch = vault / str(patch_info.get("path") or "")
    if not patch.is_file() or sha256(patch) != patch_info.get("sha256"):
        raise RuntimeError(f"{entry.get('id')} patch is missing or does not match the lock")
    run_checked(["git", "apply", "--check", str(patch)], source)
    run_checked(["git", "apply", str(patch)], source)


def build_patched(vault: Path, entry: dict, work: Path) -> Path:
    source = work / str(entry["id"])
    clone_pinned(entry, source)
    if entry["id"] == "writing-studio":
        run_checked(["npm", "ci", "--ignore-scripts"], source)
        run_checked(["npm", "audit", "--omit=dev"], source)
        run_checked(["npm", "run", "build"], source)
        apply_patch(vault, source, entry)
    else:
        apply_patch(vault, source, entry)
        run_checked(["npm", "ci", "--ignore-scripts"], source)
        run_checked(["npm", "audit", "--omit=dev"], source)
        run_checked(["npm", "run", "test:unit"], source)
        run_checked(["npm", "run", "lint"], source)
        run_checked([str(source / "node_modules" / ".bin" / "tsc"), "-noEmit", "-skipLibCheck"], source)
        run_checked(["node", "esbuild.config.mjs", "production"], source)
    verify_files(source, entry)
    return source


def download_release(entry: dict, work: Path) -> Path:
    release = str(entry.get("release") or "")
    if "/releases/tag/" not in release:
        raise RuntimeError(f"{entry.get('id')} has no release URL")
    base, tag = release.split("/releases/tag/", 1)
    destination = work / str(entry["id"])
    destination.mkdir()
    for name in entry.get("files") or {}:
        url = f"{base}/releases/download/{tag}/{name}"
        request = urllib.request.Request(url, headers={"User-Agent": "you2betoblog-plugin-installer/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, (destination / name).open("wb") as handle:
            shutil.copyfileobj(response, handle)
    verify_files(destination, entry)
    return destination


def local_plugin(vault: Path, entry: dict) -> Path:
    source = vault / "plugins" / LOCAL
    verify_files(source, entry)
    return source


def rss_data_is_safe(path: Path) -> bool:
    try:
        template = json.loads(path.read_text(encoding="utf-8"))["articleSaving"]["defaultTemplate"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return all(token in template for token in ("{{titleYaml}}", "{{linkYaml}}", "{{feedTitleYaml}}",
                                                "{{authorYaml}}", "{{yt2bTagsYaml}}"))


def verified_rss_default(vault: Path, entry: dict) -> Path:
    info = entry.get("default_data") or {}
    path = vault / str(info.get("path") or "")
    if not path.is_file() or sha256(path) != info.get("sha256") or not rss_data_is_safe(path):
        raise RuntimeError("RSS default data is missing, unsafe, or does not match the lock")
    return path


def install_one(vault: Path, source: Path, entry: dict, replace: bool) -> dict:
    plugin_id = str(entry["id"])
    parent = vault / ".obsidian" / "plugins"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / plugin_id
    if target.exists() and not replace:
        verify_files(target, entry)
        if plugin_id == "rss-dashboard" and not rss_data_is_safe(target / "data.json"):
            raise RuntimeError("existing RSS data.json uses an unsafe save template")
        return {"id": plugin_id, "status": "already-current", "path": str(target)}

    staged = Path(tempfile.mkdtemp(prefix=f".{plugin_id}-", dir=parent))
    backup: Path | None = None
    try:
        for name in entry.get("files") or {}:
            shutil.copy2(source / name, staged / name)
        if target.is_dir() and (target / "data.json").is_file():
            shutil.copy2(target / "data.json", staged / "data.json")
        if plugin_id == "rss-dashboard":
            if not (staged / "data.json").is_file():
                shutil.copy2(verified_rss_default(vault, entry), staged / "data.json")
            if not rss_data_is_safe(staged / "data.json"):
                raise RuntimeError("existing RSS data.json uses an unsafe save template; update it before replacement")
        verify_files(staged, entry)
        if target.exists():
            stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
            backup = parent / f"{plugin_id}.backup-{stamp}"
            if backup.exists():
                raise RuntimeError(f"backup path already exists: {backup}")
            os.replace(target, backup)
        os.replace(staged, target)
    except Exception:
        if backup is not None and backup.exists() and not target.exists():
            os.replace(backup, target)
        if staged.exists():
            shutil.rmtree(staged)
        raise
    return {"id": plugin_id, "status": "installed", "path": str(target),
            "backup": str(backup) if backup else ""}


def enable_plugins(vault: Path, ids: tuple[str, ...]) -> None:
    path = vault / ".obsidian" / "community-plugins.json"
    try:
        current = list(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        current = []
    for plugin_id in ids:
        if plugin_id not in current:
            current.append(plugin_id)
    common.json_dump(path, current)


def plan(vault: Path, ids: tuple[str, ...], lock: dict[str, dict]) -> dict:
    items = []
    for plugin_id in ids:
        entry = lock.get(plugin_id)
        items.append({
            "id": plugin_id,
            "version": entry.get("version") if entry else None,
            "source": "vault" if plugin_id == LOCAL else (entry.get("source") if entry else None),
            "patched": plugin_id in PATCHED,
            "locked": bool(entry),
        })
    return {"ok": all(item["locked"] for item in items), "mode": "plan", "vault": str(vault), "plugins": items}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="vault root (default: auto-detect)")
    parser.add_argument("--profile", choices=("core", "all"), default="all")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    install = sub.add_parser("install")
    install.add_argument("--replace", action="store_true", help="replace an existing mismatched plugin after creating a backup")
    args = parser.parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
        lock = load_lock(vault)
        ids = CORE if args.profile == "core" else ALL
        if args.command == "plan":
            result = plan(vault, ids, lock)
            common.emit(result)
            return common.EXIT_OK if result["ok"] else common.EXIT_MISSING
        missing = [plugin_id for plugin_id in ids if plugin_id not in lock]
        if missing:
            return common.fail(common.EXIT_MISSING, f"plugin lock entries missing: {missing}")
        results = []
        with tempfile.TemporaryDirectory(prefix="you2betoblog-plugins-") as temp:
            work = Path(temp)
            for plugin_id in ids:
                entry = lock[plugin_id]
                if plugin_id == LOCAL:
                    source = local_plugin(vault, entry)
                elif plugin_id in PATCHED:
                    source = build_patched(vault, entry, work)
                else:
                    source = download_release(entry, work)
                results.append(install_one(vault, source, entry, args.replace))
        enable_plugins(vault, ids)
        common.emit({"ok": True, "mode": "install", "vault": str(vault), "plugins": results})
        return common.EXIT_OK
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return common.fail(common.EXIT_FAIL, str(exc))


if __name__ == "__main__":
    sys.exit(main())
