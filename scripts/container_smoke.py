"""仅在 CI 或用户显式启动容器后运行，验证真实网关与持久服务。"""
import json
import urllib.error
import urllib.request
from io import BytesIO
import zipfile

BASE = 'http://127.0.0.1:3080'


def call(path, method='GET', data=None):
    headers = {'X-FilmHub-Request': '1'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(BASE + path, method=method, headers=headers, data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
        return json.loads(content) if 'application/json' in response.headers.get('Content-Type', '') else content


assert call('/api/health')['status'] == 'ok'
assert b'FilmHub' in call('/')
film = call('/api/library/films', 'POST', {'name': 'CI Kodak Gold 200'})
camera = call('/api/library/cameras', 'POST', {'name': 'CI Nikon FM2'})
roll = call('/api/rolls', 'POST', {'film_stock_id': film['id'], 'camera_id': camera['id'], 'title': '容器验收'})
assert call(f'/api/rolls/{roll["id"]}')['title'] == '容器验收'
assert b'FilmHub' in call(f'/rolls/{roll["id"]}')
backup = call('/api/backups', 'POST')
with zipfile.ZipFile(BytesIO(call('/api/backups/' + backup['name']))) as archive:
    assert 'filmhub.sqlite3' in archive.namelist()
    assert 'manifest.json' in archive.namelist()
call(f'/api/rolls/{roll["id"]}', 'DELETE')
call(f'/api/library/films/{film["id"]}', 'DELETE')
call(f'/api/library/cameras/{camera["id"]}', 'DELETE')
assert call('/api/stats')['total_rolls'] == 0
print('容器健康检查、页面、同源 API、CRUD 和备份下载通过。')
