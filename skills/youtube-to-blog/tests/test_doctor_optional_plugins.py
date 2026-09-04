"""Optional RSS must not prevent the core pipeline from passing its doctor."""
import json

import doctor


def run_check(tmp_path, enabled):
    (tmp_path / '_system').mkdir()
    (tmp_path / '.obsidian').mkdir()
    (tmp_path / '_system/plugin-lock.json').write_text(json.dumps({
        'obsidian_plugins': [{'id': plugin_id, 'files': {}} for plugin_id in
                             ('writing-studio', 'youtubetoblog-home', 'rss-dashboard')],
    }))
    (tmp_path / '.obsidian/community-plugins.json').write_text(json.dumps(enabled))
    report = doctor.Report()
    doctor.check_obsidian_plugin_integrity(report, tmp_path)
    return report


def test_disabled_optional_rss_does_not_block_core(tmp_path):
    report = run_check(tmp_path, ['writing-studio', 'youtubetoblog-home'])
    assert not report.required_failures
    rss = next(row for row in report.checks if 'rss-dashboard' in row['name'])
    assert rss['status'] == 'info' and not rss['required']


def test_enabled_rss_still_requires_safe_data(tmp_path):
    report = run_check(tmp_path, ['writing-studio', 'youtubetoblog-home', 'rss-dashboard'])
    assert 'obsidian plugin rss-dashboard integrity' in report.required_failures
