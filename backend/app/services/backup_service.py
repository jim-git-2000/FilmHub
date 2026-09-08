import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import uuid4

from PIL import Image

from ..schemas.validation import Problem

MAX_BACKUP_BYTES = 4 * 1024**3
MAX_EXPANDED_BYTES = 20 * 1024**3


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_journal(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as out:
        json.dump(value, out)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, path)


def recover_restore(db):
    journal = db.data_dir / '.restore.json'
    old_db = db.data_dir / '.restore-old.sqlite3'
    old_images = db.uploads_dir / '.restore-old'
    new_images = db.uploads_dir / '.restore-new'
    current_images = db.uploads_dir / 'rolls'
    if journal.exists():
        state = json.loads(journal.read_text())
        if not state['committed']:
            if old_db.exists():
                os.replace(old_db, db.path)
            if old_images.exists():
                if current_images.exists():
                    shutil.rmtree(current_images)
                os.replace(old_images, current_images)
            elif not state['had_images'] and current_images.exists():
                shutil.rmtree(current_images)
        journal.unlink()
    old_db.unlink(missing_ok=True)
    (db.data_dir / '.restore-new.sqlite3').unlink(missing_ok=True)
    for folder in (old_images, new_images):
        if folder.exists():
            shutil.rmtree(folder)


class BackupService:
    def __init__(self, db):
        self.db = db

    def create(self):
        with self.db.lock, tempfile.TemporaryDirectory(dir=self.db.data_dir) as temporary:
            snapshot = Path(temporary) / 'filmhub.sqlite3'
            with self.db.connect() as source, sqlite3.connect(snapshot) as target:
                source.backup(target)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
            name = f'backup-{stamp}-{uuid4().hex[:8]}.zip'
            output = self.db.backups_dir / name
            partial = output.with_suffix('.partial')
            entries = {'filmhub.sqlite3': snapshot}
            with self.db.connect() as conn:
                for row in conn.execute('SELECT file_path,thumbnail_path FROM roll_photos'):
                    for relative in row:
                        path = self.db.uploads_dir / relative
                        if not path.is_file():
                            raise Problem('部分照片文件缺失，请检查存储卷后再备份', 409)
                        entries['uploads/' + relative] = path
            manifest = {'version': 1, 'created_at': stamp, 'files': {key: digest(path) for key, path in entries.items()}}
            try:
                with zipfile.ZipFile(partial, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                    for key, path in entries.items():
                        archive.write(path, key)
                    archive.writestr('manifest.json', json.dumps(manifest))
                os.replace(partial, output)
            finally:
                partial.unlink(missing_ok=True)
            return {'name': name, 'size': output.stat().st_size}

    def list(self):
        return [{'name': path.name, 'size': path.stat().st_size} for path in sorted(self.db.backups_dir.glob('backup-*.zip'), reverse=True)]

    def path(self, name):
        if Path(name).name != name or not name.startswith('backup-') or not name.endswith('.zip'):
            raise Problem('备份文件名无效')
        path = self.db.backups_dir / name
        if not path.is_file():
            raise Problem('备份不存在', 404)
        return path

    def validate(self, archive, staging):
        infos = archive.infolist()
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)) or len(names) > 100000 or sum(i.file_size for i in infos) > MAX_EXPANDED_BYTES:
            raise Problem('备份重复、文件过多或解压后超过 20 GB')
        if 'manifest.json' not in names or archive.getinfo('manifest.json').file_size > 20 * 1024**2:
            raise Problem('缺少有效的备份清单')
        manifest = json.loads(archive.read('manifest.json'))
        if not isinstance(manifest, dict) or manifest.get('version') != 1 or not isinstance(manifest.get('files'), dict):
            raise Problem('不支持此备份版本')
        if set(names) != set(manifest['files']) | {'manifest.json'} or 'filmhub.sqlite3' not in names:
            raise Problem('备份清单与文件不一致')
        for info in infos:
            name = PurePosixPath(info.filename)
            if (name.is_absolute() or '..' in name.parts or '\\' in info.filename or
                    name.as_posix() != info.filename or (info.external_attr >> 16) & 0o170000 == 0o120000):
                raise Problem('备份包含非法路径')
            if info.filename not in ('manifest.json', 'filmhub.sqlite3') and not info.filename.startswith('uploads/rolls/'):
                raise Problem('备份包含无关文件')
            path = staging / info.filename
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, path.open('wb') as target:
                shutil.copyfileobj(source, target)
            if info.filename != 'manifest.json' and digest(path) != manifest['files'][info.filename]:
                raise Problem('备份校验失败，文件可能已损坏')
        self.validate_database(staging)

    def validate_database(self, staging):
        with sqlite3.connect(f'file:{staging / "filmhub.sqlite3"}?mode=ro', uri=True) as conn:
            if conn.execute('PRAGMA user_version').fetchone()[0] != 1 or conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
                raise Problem('备份数据库版本或完整性检查失败')
            with self.db.connect() as current:
                # 仅接受本应用的表结构，拒绝额外触发器、视图及修改后的约束。
                sql = "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
                if [tuple(r) for r in current.execute(sql)] != conn.execute(sql).fetchall():
                    raise Problem('备份数据库结构不匹配')
            required = set()
            for roll_id, roll_number, actual_frames, cover_id in conn.execute('SELECT id,roll_number,actual_frames,cover_photo_id FROM film_rolls'):
                photos = conn.execute('SELECT id,file_path,thumbnail_path,frame_number,sort_order,is_cover,width,height,file_size FROM roll_photos WHERE roll_id=? ORDER BY sort_order', (roll_id,)).fetchall()
                if actual_frames != len(photos) or (photos and cover_id not in [p[0] for p in photos]) or (not photos and cover_id is not None):
                    raise Problem('备份的照片数量或封面不一致')
                for index, (ident, original, thumb, frame, order, is_cover, width, height, file_size) in enumerate(photos):
                    if frame != index + 1 or order != index or bool(is_cover) != (ident == cover_id):
                        raise Problem('备份的照片顺序或封面不一致')
                    for relative, folder in ((original, 'originals'), (thumb, 'thumbnails')):
                        path = PurePosixPath(relative)
                        expected = f'rolls/{roll_number:06}/{folder}'
                        if path.parent.as_posix() != expected or '\\' in relative or '..' in path.parts:
                            raise Problem('备份照片路径无效')
                        target = staging / 'uploads' / relative
                        if not target.is_file():
                            raise Problem('备份缺少照片文件，无法同步恢复')
                        allowed = {'.jpg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'} if folder == 'originals' else {'.webp': 'WEBP'}
                        if path.suffix not in allowed:
                            raise Problem('备份包含不支持的图片类型')
                        with Image.open(target) as image:
                            if image.format != allowed[path.suffix]:
                                raise Problem('备份图片内容与扩展名不匹配')
                            oriented_size = image.size[::-1] if image.getexif().get(274) in (5, 6, 7, 8) else image.size
                            if folder == 'originals' and (oriented_size != (width, height) or target.stat().st_size != file_size):
                                raise Problem('备份图片尺寸或文件大小不匹配')
                        with Image.open(target) as image:
                            image.verify()
                        required.add('uploads/' + relative)
            present = {p.relative_to(staging).as_posix() for p in (staging / 'uploads').rglob('*') if p.is_file()} if (staging / 'uploads').exists() else set()
            if required != present:
                raise Problem('备份图片与数据库记录不匹配')

    def restore(self, source):
        with self.db.lock, tempfile.TemporaryDirectory(dir=self.db.data_dir) as temporary:
            recover_restore(self.db)
            staging = Path(temporary)
            try:
                with zipfile.ZipFile(source) as archive:
                    self.validate(archive, staging)
            except (zipfile.BadZipFile, KeyError, ValueError, TypeError, sqlite3.DatabaseError, RuntimeError, OSError, Image.DecompressionBombError) as error:
                raise Problem('无法读取备份，请选择完整的 FilmHub ZIP 备份') from error
            safety = self.create()
            old_db = self.db.data_dir / '.restore-old.sqlite3'
            new_db = self.db.data_dir / '.restore-new.sqlite3'
            old_images = self.db.uploads_dir / '.restore-old'
            new_images = self.db.uploads_dir / '.restore-new'
            current_images = self.db.uploads_dir / 'rolls'
            journal = self.db.data_dir / '.restore.json'
            state = {'committed': False, 'had_images': current_images.exists()}
            shutil.copy2(self.db.path, old_db)
            shutil.copy2(staging / 'filmhub.sqlite3', new_db)
            source_images = staging / 'uploads/rolls'
            if source_images.exists():
                shutil.copytree(source_images, new_images)
            else:
                new_images.mkdir()
            write_journal(journal, state)
            try:
                if current_images.exists():
                    os.replace(current_images, old_images)
                os.replace(new_images, current_images)
                os.replace(new_db, self.db.path)
                write_journal(journal, {**state, 'committed': True})
            except BaseException:
                recover_restore(self.db)
                raise
            recover_restore(self.db)
            return {'restored': True, 'safety_backup': safety['name']}
