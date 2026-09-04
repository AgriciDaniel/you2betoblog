"""Regressions reproduced during public-release review, no provider calls."""
import pytest
import contract
import pipeline
import install_plugins
import yt2b_common as common
from test_contract import make_world, SLUG


def ready(tmp_path):
    vault, run, blog = make_world(tmp_path)
    post = blog / f'{SLUG}.md'
    gate = contract.contract_gate(vault, run, blog)
    common.json_dump(blog / 'preflight-report.json', {'blocked': False, 'gates': [
        {'gate': n, 'passed': True} for n in range(1, 6)
    ] + [gate]})
    common.update_note(post, {'yt2b_status': 'reviewed'})
    common.write_note(vault / '05 Evaluations/eval.md', {
        'type': 'yt2b-evaluation', 'blog': common.wikilink(common.rel(post, vault)),
        'run': common.wikilink(common.rel(run / 'run.md', vault)),
        'rubric_pass': True, 'gates_passed': True,
    }, '# Evaluation\n')
    return vault, run, blog


def test_completion_rejects_incomplete_gate_report(tmp_path):
    vault, run, blog = ready(tmp_path)
    report = common.json_load(blog / 'preflight-report.json')
    report['gates'] = report['gates'][-1:]
    common.json_dump(blog / 'preflight-report.json', report)
    assert pipeline.completion_violations(vault, run, blog)[0]


def test_completion_revalidates_revoked_approval(tmp_path):
    vault, run, blog = ready(tmp_path)
    approval = next((vault / common.ROOMS['approvals_queue']).glob('*strategy.md'))
    common.update_note(approval, {'status': 'declined'})
    failures = pipeline.completion_violations(vault, run, blog)[0]
    assert any('strategy approval' in f for f in failures)


def test_completion_rejects_failed_gate_even_if_blocked_false(tmp_path):
    vault, run, blog = ready(tmp_path)
    report = common.json_load(blog / 'preflight-report.json')
    report['gates'][0]['passed'] = False
    common.json_dump(blog / 'preflight-report.json', report)
    assert pipeline.completion_violations(vault, run, blog)[0]


def test_completion_revalidates_site(tmp_path):
    vault, run, blog = ready(tmp_path)
    common.update_note(vault / common.SETTINGS_NOTE, {'site_url': ''})
    assert any('site_url' in f for f in pipeline.completion_violations(vault, run, blog)[0])


def test_critical_cannot_be_waived_as_high(tmp_path):
    vault, run, blog = make_world(tmp_path)
    (blog / 'review.md').write_text('### Overall Score: 95/100\n\n#### Critical\n- Unsafe content.\n\nBLOCKING: false\n')
    common.write_note(vault / common.ROOMS['approvals_queue'] / 'editorial.md', {
        'type': 'yt2b-approval', 'kind': 'editorial', 'status': 'approved',
        'run': common.wikilink(common.rel(run / 'run.md', vault)),
        'blog': common.wikilink(common.rel(blog / f'{SLUG}.md', vault)),
        'selected': ['accept-high'],
    }, '# Editorial\n')
    gate = contract.contract_gate(vault, run, blog)
    assert not gate['passed']
    assert any('cannot be waived' in f for f in gate['violations'])


@pytest.mark.parametrize('video_id', ['*', '../*', '', 'short', '???????????'])
def test_cleanup_rejects_malformed_id_without_deleting(tmp_path, video_id):
    vault, run, _ = make_world(tmp_path)
    common.update_note(run / 'run.md', {'video_id': video_id})
    cache = vault / common.CACHE_DIR
    cache.mkdir(parents=True)
    file = cache / 'unrelatedVideo.mp4'
    file.write_bytes(b'test')
    with pytest.raises(ValueError, match='invalid video_id'):
        pipeline.cleanup_video_cache(vault, run, False)
    assert file.exists()


@pytest.mark.parametrize('url', ['http://192.168.1.1', 'http://[::1]', 'https://foo.example.com', 'http://localhost.', 'http://host.local', 'http://[', 'https://user:password' + chr(64) + 'brandsite.dev'])
def test_site_rejects_local_reserved_and_malformed_urls(url):
    assert not contract.valid_site_url(url)


def test_already_installed_rss_rejects_unsafe_data(tmp_path):
    vault = tmp_path / 'vault'
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'main.js').write_text('safe bundle')
    target = vault / '.obsidian/plugins/rss-dashboard'
    target.mkdir(parents=True)
    (target / 'main.js').write_text('safe bundle')
    (target / 'data.json').write_text('{"articleSaving":{"defaultTemplate":"{{title}}"}}')
    entry = {'id': 'rss-dashboard', 'files': {'main.js': install_plugins.sha256(source / 'main.js')}}
    with pytest.raises(RuntimeError, match='unsafe save template'):
        install_plugins.install_one(vault, source, entry, replace=False)


def test_failed_external_preflight_cannot_reuse_green_report(tmp_path):
    from test_deliver_contract import run_gates
    vault, run, blog = ready(tmp_path)
    scripts = tmp_path / 'failed-scripts'
    scripts.mkdir()
    (scripts / 'blog_preflight.py').write_text('raise SystemExit(1)\n')
    code, result = run_gates(vault, run, blog, scripts)
    assert code != 0 and result['blocked']
    assert common.json_load(blog / 'preflight-report.json')['blocked']


def test_readme_checks_actual_image_references(tmp_path):
    import release_check
    (tmp_path / 'README.md').write_text('![new image](docs/images/new%20image.png)\n')
    assert release_check.readme_images(tmp_path) == ['docs/images/new%20image.png']


def test_broken_internal_symlink_fails(tmp_path):
    import release_check
    link = tmp_path / 'broken'
    link.symlink_to(tmp_path / 'missing')
    assert release_check.check_symlinks(tmp_path, [link]) == ['broken']
