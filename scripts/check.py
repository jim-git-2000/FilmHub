"""不还原依赖的本地结构、语法和核心服务轻量检查。"""
import ast
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for path in [*(root / 'backend').rglob('*.py'), *(root / 'scripts').rglob('*.py')]:
    ast.parse(path.read_text(), filename=str(path))
for path in (root / 'frontend/package.json', root / 'frontend/tsconfig.json'):
    json.loads(path.read_text())
required = ['app/page.tsx', 'app/rolls/new/page.tsx', 'app/rolls/[id]/page.tsx', 'app/rolls/[id]/edit/page.tsx', 'app/library/page.tsx', 'app/stats/page.tsx', 'app/settings/page.tsx']
for relative in required:
    assert (root / 'frontend/src' / relative).is_file(), relative
css = (root / 'frontend/src/app/globals.css').read_text()
assert css.count('{') == css.count('}')
assert 'repeat(6,minmax(0,1fr))' in css
assert 'repeat(4,minmax(0,1fr))' in css
assert 'repeat(2,minmax(0,1fr))' in css
print('Python 语法、JSON、路由和 CSS 结构检查通过。', flush=True)
result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_services.py', '-v'], cwd=root / 'backend')
sys.exit(result.returncode)
