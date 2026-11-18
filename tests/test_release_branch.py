"""Exercise the exact release gate against temporary Git histories, without GitHub writes."""
import subprocess
from pathlib import Path
import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/release.yml'

@pytest.mark.parametrize('case,allowed', [
    ('main', True), ('ancestor', True), ('develop', False), ('missing-main', False),
])
def test_release_commit_must_belong_to_main(tmp_path, case, allowed):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path, stderr=subprocess.DEVNULL, text=True).strip()
    git('init', '-b', 'main')
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    git('commit', '--allow-empty', '-m', 'base')
    base = git('rev-parse', 'HEAD')
    git('commit', '--allow-empty', '-m', 'stable')
    git('remote', 'add', 'origin', str(tmp_path))
    if case == 'ancestor':
        git('checkout', '--detach', base)
    elif case == 'develop':
        git('checkout', '-b', 'develop')
        git('commit', '--allow-empty', '-m', 'not integrated')
    elif case == 'missing-main':
        git('branch', '-m', 'develop')
    git('tag', '-a', 'v0.2.0', '-m', 'local test')
    git('checkout', '--detach', 'v0.2.0')
    workflow = WORKFLOW.read_text()
    step = workflow.split('      - name: Verify release commit belongs to main\n', 1)[1].split('      - ', 1)[0]
    script = '\n'.join(line[10:] for line in step.split('        run: |\n', 1)[1].splitlines())
    result = subprocess.run(['bash', '-eo', 'pipefail', '-c', script], cwd=tmp_path, capture_output=True, text=True)
    assert (result.returncode == 0) == allowed, result.stdout + result.stderr
    if case == 'develop':
        assert 'no está integrado en main' in result.stdout
    assert workflow.index('Verify release commit') < workflow.index('Package tracked source only')
    assert 'fetch-depth: 0' in workflow
