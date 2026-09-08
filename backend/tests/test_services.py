"""核心验收案例；仅依赖标准库和 Pillow，可作为本地轻量验证。"""
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.database import Database
from app.schemas.validation import Problem
from app.services.archive_service import ArchiveService
from app.services.backup_service import BackupService, recover_restore, write_journal
from app.services.image_service import PhotoService, prepare_image


def jpeg(width=90, height=60, orientation=None):
    image = Image.new('RGB', (width, height), '#73654a')
    out = BytesIO()
    exif = Image.Exif()
    if orientation:
        exif[274] = orientation
    image.save(out, 'JPEG', exif=exif)
    return out.getvalue()


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.db = Database(root / 'data', root / 'uploads', root / 'backups')
        self.archive = ArchiveService(self.db)
        self.photos = PhotoService(self.db)
        self.backups = BackupService(self.db)
        self.film = self.archive.save_library('films', {'name': 'Kodak Portra 400'})
        self.camera = self.archive.save_library('cameras', {'name': 'Leica M6'})
        self.lens = self.archive.save_library('lenses', {'name': '35mm F2'})
        self.payload = {'roll_number': 36, 'film_stock_id': self.film['id'], 'camera_id': self.camera['id'], 'lens_ids': [self.lens['id']], 'title': '上海初秋', 'shot_iso': 200, 'location': '上海', 'started_at': '2026-09-03'}
        self.roll = self.archive.save_roll(self.payload)

    def tearDown(self):
        self.temporary.cleanup()

    def upload(self, count=3, roll_id=None):
        return self.photos.upload(roll_id or self.roll['id'], [(f'img-{i}.jpg', 'image/jpeg', jpeg()) for i in range(count, 0, -1)])

    def test_complete_mvp_lifecycle_40_photos(self):
        ident = self.roll['id']
        self.assertEqual(self.roll['status'], 'shooting')
        self.assertEqual(self.archive.save_roll({'finished_at': '2026-09-07'}, ident)['status'], 'finished')
        self.archive.save_record(ident, 'developments', {'process': 'C-41', 'push_pull': 1, 'developed_at': '2026-09-08'})
        self.assertEqual(self.archive.roll(ident)['status'], 'developed')
        self.archive.save_record(ident, 'scans', {'scanner_model': 'Noritsu HS-1800', 'resolution_width': 6048, 'resolution_height': 4011})
        photos = self.upload(40)
        roll = self.archive.roll(ident)
        self.assertEqual(roll['status'], 'scanned')
        self.assertEqual(roll['actual_frames'], 40)
        self.assertEqual(photos[1]['original_filename'], 'img-2.jpg')
        self.assertEqual([p['frame_number'] for p in roll['photos']], list(range(1, 41)))
        self.assertEqual(sum(p['is_cover'] for p in photos), 1)
        for photo in photos:
            with Image.open(self.db.uploads_dir / photo['thumbnail_path']) as thumb:
                self.assertEqual(thumb.format, 'WEBP')
        self.archive.save_roll({'status': 'archived'}, ident)
        self.upload(1)
        self.assertEqual(self.archive.roll(ident)['status'], 'archived')

    def test_library_minimal_unique_and_referenced_delete(self):
        self.assertEqual(set(self.film), {'id', 'name', 'created_at'})
        with self.assertRaises(Problem):
            self.archive.save_library('films', {'name': ' kodak portra 400 '})
        for kind, item in [('films', self.film), ('cameras', self.camera), ('lenses', self.lens)]:
            with self.assertRaises(Problem) as caught:
                self.archive.delete_library(kind, item['id'])
            self.assertEqual(caught.exception.status, 409)
        self.archive.save_library('films', {'name': 'Kodak Gold 200'}, self.film['id'])
        self.assertEqual(self.archive.roll(self.roll['id'])['film_stock'], 'Kodak Gold 200')
        with self.assertRaises(Problem):
            self.archive.save_library('bad', {'name': 'x'})
        with self.assertRaises(Problem):
            self.archive.save_library('films', {'name': '   '})

    def test_roll_validation_and_transaction(self):
        for payload in [{'camera_id': 9999}, {'film_stock_id': True}, {'shot_iso': -20}, {'shot_iso': 0}, {'shot_iso': 10**400}, {'lens_ids': [10**400]}, {'lens_ids': [1, 1]}, {'finished_at': '2026-09-01'}, {'started_at': 'bad'}, {'status': 'broken'}, {'roll_number': 50}, {'description': None}, {'inventory': 1}]:
            with self.subTest(payload=payload), self.assertRaises(Problem):
                self.archive.save_roll(payload, self.roll['id'])
        self.assertEqual(self.archive.roll(self.roll['id']), self.roll)
        with self.assertRaises(Problem):
            self.archive.save_roll(self.payload)
        self.assertEqual(len(self.archive.rolls()), 1)
        second = self.archive.save_roll({k: v for k, v in self.payload.items() if k != 'roll_number'})
        self.assertEqual(second['roll_number'], 37)

    def test_search_every_supported_field_and_filters(self):
        for q in ['Portra', '上海', 'Leica', '35mm', '初秋', '36']:
            self.assertEqual(len(self.archive.rolls(q)), 1)
        self.archive.save_roll({'description': '东京的回忆'}, self.roll['id'])
        self.assertEqual(len(self.archive.rolls('东京')), 1)
        self.assertEqual(self.archive.rolls(year=2025), [])
        self.assertEqual(len(self.archive.rolls(year=2026)), 1)
        self.assertEqual(self.archive.rolls(status='processed'), [])
        photo = self.upload(1)[0]
        self.photos.edit(photo['id'], {'is_favorite': True, 'caption': '黄昏'})
        self.assertEqual(len(self.archive.rolls(status='processed')), 1)
        self.assertEqual(len(self.archive.rolls(status='favorite')), 1)
        self.photos.edit(photo['id'], {'is_favorite': False})
        self.assertEqual(self.archive.rolls(status='favorite'), [])

    def test_orientation_mime_and_corrupt_upload_rollback(self):
        source = jpeg(90, 60, 6)
        original, thumb, width, height, ext = prepare_image(source, 'image/jpeg')
        self.assertEqual((width, height, ext), (60, 90, 'jpg'))
        self.assertEqual(original, source)
        with Image.open(BytesIO(thumb)) as image:
            self.assertNotIn(274, image.getexif())
            self.assertEqual(image.size, (60, 90))
        with self.assertRaises(Problem):
            prepare_image(jpeg(), 'image/png')
        with self.assertRaises(Problem):
            self.photos.upload(self.roll['id'], [('a.jpg', 'image/jpeg', jpeg()), ('b.jpg', 'image/jpeg', b'bad')])
        self.assertEqual(self.archive.roll(self.roll['id'])['photos'], [])
        self.assertEqual([p for p in self.db.uploads_dir.rglob('*') if p.is_file()], [])

    def test_reorder_cover_delete_normalize(self):
        photos = self.upload()
        ids = [p['id'] for p in photos]
        self.photos.reorder(self.roll['id'], list(reversed(ids)))
        self.photos.cover(self.roll['id'], ids[1])
        actual = self.archive.roll(self.roll['id'])['photos']
        self.assertEqual([p['id'] for p in actual], list(reversed(ids)))
        self.assertEqual([p['frame_number'] for p in actual], [1, 2, 3])
        with self.assertRaises(Problem):
            self.photos.reorder(self.roll['id'], [ids[0], ids[0], ids[1]])
        self.photos.delete(ids[1])
        roll = self.archive.roll(self.roll['id'])
        self.assertEqual(roll['cover_photo_id'], ids[2])
        self.assertEqual(roll['actual_frames'], 2)
        self.assertFalse((self.db.uploads_dir / photos[1]['file_path']).exists())
        for photo in roll['photos']:
            self.photos.delete(photo['id'])
        self.assertIsNone(self.archive.roll(self.roll['id'])['cover'])

    def test_cover_cannot_reference_other_roll(self):
        photo = self.upload(1)[0]
        second = self.archive.save_roll({k: v for k, v in self.payload.items() if k != 'roll_number'})
        with self.assertRaises(Problem):
            self.photos.cover(second['id'], photo['id'])

    def test_delete_roll_cascades_and_preserves_library(self):
        self.upload()
        self.archive.save_record(self.roll['id'], 'developments', {'notes': 'test'})
        self.archive.delete_roll(self.roll['id'])
        self.assertEqual(self.archive.rolls(), [])
        with self.db.connect() as conn:
            for table in ('roll_photos', 'film_roll_lenses', 'developments'):
                self.assertEqual(conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)
        self.assertEqual(len(self.archive.library()['films']), 1)
        self.assertEqual([p for p in self.db.uploads_dir.rglob('*') if p.is_file()], [])
        self.archive.delete_library('films', self.film['id'])

    def test_stats_and_multiple_lenses(self):
        lens = self.archive.save_library('lenses', {'name': '50mm F2'})
        self.archive.save_roll({'lens_ids': [self.lens['id'], lens['id']]}, self.roll['id'])
        self.upload()
        stats = self.archive.stats()
        self.assertEqual((stats['total_rolls'], stats['total_photos']), (1, 3))
        self.assertEqual(len(stats['lenses']), 2)
        self.assertEqual(stats['films'][0]['name'], 'Kodak Portra 400')

    def test_backup_restore_roundtrip_including_images(self):
        self.upload()
        self.archive.save_record(self.roll['id'], 'scans', {'scanner_model': 'HS-1800'})
        original = self.archive.roll(self.roll['id'])
        backup = self.backups.create()
        self.archive.delete_roll(self.roll['id'])
        result = self.backups.restore(self.backups.path(backup['name']))
        self.assertTrue(result['restored'])
        self.assertEqual(self.archive.roll(self.roll['id']), original)
        self.assertEqual(len(self.backups.list()), 2)
        for photo in original['photos']:
            self.assertTrue((self.db.uploads_dir / photo['file_path']).is_file())
        self.assertFalse((self.db.data_dir / '.restore.json').exists())

    def test_backup_preserves_exif_original_and_png(self):
        png = BytesIO()
        Image.new('RGBA', (70, 100), '#ffffff80').save(png, 'PNG')
        source = jpeg(90, 60, 6)
        photos = self.photos.upload(self.roll['id'], [('a.jpg', 'image/jpeg', source), ('b.png', 'image/png', png.getvalue())])
        backup = self.backups.create()
        self.archive.delete_roll(self.roll['id'])
        self.backups.restore(self.backups.path(backup['name']))
        self.assertEqual((self.db.uploads_dir / photos[0]['file_path']).read_bytes(), source)
        self.assertEqual(self.archive.roll(self.roll['id'])['photos'][0]['width'], 60)

    def test_startup_cleans_only_unreferenced_images(self):
        photo = self.upload(1)[0]
        orphan = self.db.uploads_dir / 'rolls/000036/originals/uncommitted.jpg'
        orphan.write_bytes(jpeg())
        Database(self.db.data_dir, self.db.uploads_dir, self.db.backups_dir)
        self.assertFalse(orphan.exists())
        self.assertTrue((self.db.uploads_dir / photo['file_path']).exists())

    def test_restore_corrupt_or_traversal_backup_keeps_original(self):
        photo = self.upload(1)[0]
        backup = self.backups.create()
        with zipfile.ZipFile(self.backups.path(backup['name'])) as archive:
            content = {name: archive.read(name) for name in archive.namelist()}
        for change in ('corrupt', 'traversal', 'missing'):
            entries = dict(content)
            if change == 'corrupt':
                entries['filmhub.sqlite3'] = b'corrupt'
            elif change == 'traversal':
                entries['../escaped'] = b'danger'
                manifest = json.loads(entries['manifest.json'])
                manifest['files']['../escaped'] = hashlib.sha256(b'danger').hexdigest()
                entries['manifest.json'] = json.dumps(manifest).encode()
            else:
                del entries['uploads/' + photo['file_path']]
            stream = BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                for name, data in entries.items():
                    archive.writestr(name, data)
            stream.seek(0)
            with self.subTest(change=change), self.assertRaises(Problem):
                self.backups.restore(stream)
            self.assertEqual(self.archive.roll(self.roll['id'])['actual_frames'], 1)
            self.assertTrue((self.db.uploads_dir / photo['file_path']).is_file())

    def test_restore_swap_failure_rolls_back(self):
        import os
        self.upload(1)
        backup = self.backups.create()
        self.archive.save_roll({'title': '需要保留的当前记录'}, self.roll['id'])
        real_replace = os.replace
        def failing_replace(source, target):
            if Path(source).name == '.restore-new.sqlite3':
                raise OSError('simulated disk failure')
            return real_replace(source, target)
        with patch('app.services.backup_service.os.replace', side_effect=failing_replace), self.assertRaises(OSError):
            self.backups.restore(self.backups.path(backup['name']))
        self.assertEqual(self.archive.roll(self.roll['id'])['title'], '需要保留的当前记录')
        self.assertEqual(self.archive.roll(self.roll['id'])['actual_frames'], 1)

    def test_startup_recovers_interrupted_restore(self):
        import os
        import shutil
        self.upload(1)
        shutil.copy2(self.db.path, self.db.data_dir / '.restore-old.sqlite3')
        write_journal(self.db.data_dir / '.restore.json', {'committed': False, 'had_images': True})
        os.replace(self.db.uploads_dir / 'rolls', self.db.uploads_dir / '.restore-old')
        (self.db.uploads_dir / 'rolls').mkdir()
        self.archive.save_roll({'title': '不完整恢复'}, self.roll['id'])
        reopened = Database(self.db.data_dir, self.db.uploads_dir, self.db.backups_dir)
        self.assertEqual(ArchiveService(reopened).roll(self.roll['id'])['title'], '上海初秋')
        self.assertTrue(any((self.db.uploads_dir / 'rolls').rglob('*.jpg')))

    def test_record_update_delete_and_lifecycle_floor(self):
        ident = self.roll['id']
        self.archive.save_record(ident, 'developments', {'developer': 'D-76', 'temperature_c': 20, 'development_time_sec': 600, 'cost': 20})
        self.archive.save_record(ident, 'developments', {'notes': '1+1'})
        self.assertEqual(self.archive.roll(ident)['development']['developer'], 'D-76')
        self.assertEqual(self.archive.save_roll({'status': 'shooting'}, ident)['status'], 'developed')
        for bad in ({'cost': -1}, {'temperature_c': float('nan')}, {'method': 'unknown'}, {'currency': '人民币'}):
            with self.assertRaises(Problem):
                self.archive.save_record(ident, 'developments', bad)
        self.archive.delete_record(ident, 'developments')
        self.assertIsNone(self.archive.roll(ident)['development'])
        self.assertEqual(self.archive.roll(ident)['status'], 'developed')


if __name__ == '__main__':
    unittest.main()
