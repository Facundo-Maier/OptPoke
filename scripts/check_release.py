import os
import re
import tomllib
from pathlib import Path

version = tomllib.loads(Path('pyproject.toml').read_text())['project']['version']
tag = os.environ['RELEASE_TAG']
assert re.fullmatch(r'v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', tag), 'Use vMAJOR.MINOR.PATCH'
assert tag == 'v' + version, 'Tag and pyproject.toml disagree'
assert f'## {version} ' in Path('CHANGELOG.md').read_text(), 'Missing changelog entry'
print('Release version verified:', tag)
