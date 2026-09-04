#!/usr/bin/env python3
"""Offline release checks for a shareable YouTube to Blog vault.

This script does not call a provider, publish, commit, push, or inspect ignored
personal files. It checks the repository projection, secret-shaped content,
JSON contracts, Python syntax, plugin plan, tests, and known documentation
assets. Live provider and human acceptance remain separate decisions.
"""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt2b_common as common  # noqa: E402
import install_plugins  # noqa: E402

SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "google-key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "openai-shaped-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "github-token": re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    "email-address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}


def repository_files(vault: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=str(vault), capture_output=True, check=True,
    )
    return [vault / raw.decode("utf-8") for raw in proc.stdout.split(b"\0") if raw]


def scan_sensitive(vault: Path, files: list[Path]) -> list[dict]:
    findings: list[dict] = []
    for path in files:
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    findings.append({"file": common.rel(path, vault), "line": line_no, "kind": name})
    return findings


def check_json(vault: Path, files: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in files:
        if path.suffix != ".json" or not path.is_file():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            failures.append(f"{common.rel(path, vault)}: {type(exc).__name__}")
    return failures


def check_python(files: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in files:
        if path.suffix != ".py" or not path.is_file():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError:
            failures.append(str(path))
    return failures


def check_symlinks(vault: Path, files: list[Path]) -> list[str]:
    failures: list[str] = []
    root = vault.resolve()
    for path in files:
        if path.is_symlink():
            try:
                path.resolve(strict=True).relative_to(root)
            except (OSError, ValueError):
                failures.append(path.absolute().relative_to(root).as_posix())
    return failures


def readme_images(vault: Path) -> list[str]:
    missing = []
    for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", (vault / "README.md").read_text()):
        if urlparse(target).scheme:
            continue
        path = vault / unquote(target.split("#", 1)[0])
        if not path.is_file():
            missing.append(target)
    return missing


def check_local_integrity(vault: Path) -> list[str]:
    failures = []
    lock = install_plugins.load_lock(vault)
    try:
        install_plugins.local_plugin(vault, lock[install_plugins.LOCAL])
    except (KeyError, OSError, RuntimeError) as exc:
        failures.append(str(exc))
    for plugin_id in install_plugins.PATCHED:
        entry = lock.get(plugin_id, {})
        patch = entry.get("patch") or {}
        path = vault / str(patch.get("path") or "")
        if not path.is_file() or install_plugins.sha256(path) != patch.get("sha256"):
            failures.append(plugin_id + " safety patch mismatch")
    try:
        install_plugins.verified_rss_default(vault, lock["rss-dashboard"])
    except (KeyError, OSError, RuntimeError) as exc:
        failures.append(str(exc))
    return failures


def run_check(args: list[str], cwd: Path, timeout: int = 180) -> dict:
    proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    return {"passed": proc.returncode == 0, "exit_code": proc.returncode,
            "diagnostic": (proc.stderr or proc.stdout).strip()[-2000:] if proc.returncode else ""}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--vault", help="repository vault root (default: auto-detect)")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args(argv)
    try:
        vault = Path(args.vault).expanduser().resolve() if args.vault else common.find_vault_root()
        files = repository_files(vault)
        sensitive = scan_sensitive(vault, files)
        json_failures = check_json(vault, files)
        python_failures = check_python(files)
        symlink_failures = check_symlinks(vault, files)
        plugin_plan = run_check([sys.executable, str(Path(__file__).with_name("install_plugins.py")),
                                 "--vault", str(vault), "plan"], vault)
        missing_assets = readme_images(vault)
        integrity_failures = check_local_integrity(vault)
        tests = {"passed": None, "exit_code": None, "diagnostic": "not run: skipped by request"}
        dashboard_tests = dict(tests)
        if not args.skip_tests:
            tests = run_check([sys.executable, "-m", "pytest", "-q"], vault, timeout=300)
            dashboard_tests = run_check(["node", "--test", "plugins/youtubetoblog-home/tests/home.test.cjs"], vault)
        checks = {
            "sensitive_projection": {"passed": not sensitive, "findings": sensitive},
            "json": {"passed": not json_failures, "failures": json_failures},
            "python_syntax": {"passed": not python_failures, "failures": python_failures},
            "internal_symlinks": {"passed": not symlink_failures, "failures": symlink_failures},
            "plugin_plan": plugin_plan,
            "local_plugin_integrity": {"passed": not integrity_failures, "failures": integrity_failures},
            "dashboard_tests": dashboard_tests,
            "readme_images": {"passed": not missing_assets, "missing": missing_assets},
            "tests": tests,
        }
        ok = all(check["passed"] is True for check in checks.values())
        common.emit({"ok": ok, "vault": str(vault), "files_checked": len(files), "checks": checks,
                     "not_proven": ["live provider credentials and quotas", "live provider calls",
                                    "native Obsidian behavior on another computer", "human editorial acceptance",
                                    "publishing and deployment"]})
        return common.EXIT_OK if ok else common.EXIT_FAIL
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return common.fail(common.EXIT_FAIL, str(exc))


if __name__ == "__main__":
    sys.exit(main())
