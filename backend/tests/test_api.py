"""正式 HTTP 集成测试由 GitHub Actions 还原依赖后执行。"""
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.database import Database
from app.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = Database(root / 'data', root / 'uploads', root / 'backups')
        self.client = TestClient(create_app(self.db), headers={'X-FilmHub-Request': '1'})
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def create_roll(self):
        film = self.client.post('/api/library/films', json={'name': 'Portra 400'}).json()
        camera = self.client.post('/api/library/cameras', json={'name': 'M6'}).json()
        response = self.client.post('/api/rolls', json={'film_stock_id': film['id'], 'camera_id': camera['id'], 'roll_number': 36})
        self.assertEqual(response.status_code, 201)
        return response.json()['id']

    def test_health_errors_and_request_guard(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        self.assertEqual(self.client.post('/api/library/films', json={'name': 'test'}, headers={'X-FilmHub-Request': ''}).status_code, 403)
        self.assertEqual(self.client.post('/api/rolls', json=[]).status_code, 422)
        self.assertEqual(self.client.get('/api/rolls/999').status_code, 404)
        self.assertEqual(self.client.get('/api/rolls?year=abc').status_code, 422)
        self.assertEqual(self.client.post('/api/library/films', json={'name': 'a'}, headers={'Content-Length': str(2 * 1024**2)}).status_code, 413)

    def test_40_file_upload_download_and_backup_restore(self):
        ident = self.create_roll()
        output = BytesIO()
        Image.new('RGB', (120, 80), '#ada579').save(output, 'JPEG')
        files = [('files', (f'photo-{i}.jpg', output.getvalue(), 'image/jpeg')) for i in range(40, 0, -1)]
        response = self.client.post(f'/api/rolls/{ident}/photos', files=files)
        self.assertEqual(response.status_code, 201, response.text)
        photos = response.json()
        self.assertEqual(len(photos), 40)
        self.assertEqual(self.client.get(photos[0]['thumbnail_url']).headers['content-type'], 'image/webp')
        self.assertEqual(self.client.get(photos[0]['url']).status_code, 200)
        backup = self.client.post('/api/backups').json()
        payload = self.client.get('/api/backups/' + backup['name']).content
        self.assertEqual(self.client.delete(f'/api/rolls/{ident}').status_code, 204)
        self.assertEqual(self.client.get(photos[0]['url']).status_code, 404)
        self.assertEqual(self.client.post('/api/restore', files={'file': ('backup.zip', payload)}).status_code, 409)
        restore = self.client.post('/api/restore?confirm=restore', files={'file': ('backup.zip', payload)})
        self.assertEqual(restore.status_code, 200, restore.text)
        self.assertEqual(self.client.get(f'/api/rolls/{ident}').json()['actual_frames'], 40)
        self.assertEqual(self.client.get(photos[0]['url']).status_code, 200)
        self.assertEqual(self.client.get('/uploads/.restore-old/anything').status_code, 404)

    def test_records_sorting_and_library_conflict(self):
        ident = self.create_roll()
        self.assertEqual(self.client.put(f'/api/rolls/{ident}/development', json={'process': 'C-41'}).status_code, 200)
        self.assertEqual(self.client.get(f'/api/rolls/{ident}/development').json()['process'], 'C-41')
        self.assertEqual(self.client.delete(f'/api/rolls/{ident}/development').status_code, 204)
        self.assertEqual(self.client.put(f'/api/rolls/{ident}/photos/reorder', json={'photo_ids': []}).status_code, 204)
        self.assertEqual(self.client.put(f'/api/rolls/{ident}/photos/reorder', json={'photo_ids': [1]}).status_code, 409)
        self.assertEqual(self.client.delete('/api/library/films/1').status_code, 409)


if __name__ == '__main__':
    unittest.main()
