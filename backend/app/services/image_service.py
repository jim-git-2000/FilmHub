import re
import warnings
from io import BytesIO
from pathlib import PurePosixPath
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from ..schemas.validation import Problem, clean
from .archive_service import advance, photo_dict, require, touch, update

MAX_IMAGE_BYTES = 50 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 80_000_000
FORMATS = {'JPEG': ('image/jpeg', 'jpg'), 'PNG': ('image/png', 'png'), 'WEBP': ('image/webp', 'webp')}


def natural_key(name):
    return [int(x) if x.isdigit() else x.casefold() for x in re.split(r'(\d+)', name)]


def safe_path(db, path):
    relative = PurePosixPath(path)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] != 'rolls':
        raise Problem('图片路径无效')
    target = (db.uploads_dir / path).resolve()
    if not target.is_relative_to(db.uploads_dir.resolve()):
        raise Problem('图片路径无效')
    return target


def remove_files(db, photo):
    for key in ('file_path', 'thumbnail_path'):
        safe_path(db, photo[key]).unlink(missing_ok=True)


def normalize(conn, roll_id):
    rows = conn.execute('SELECT id FROM roll_photos WHERE roll_id=? ORDER BY sort_order, id', (roll_id,)).fetchall()
    conn.executemany('UPDATE roll_photos SET sort_order=?, frame_number=? WHERE id=?', [(i, i + 1, row['id']) for i, row in enumerate(rows)])
    cover_id = require(conn, 'film_rolls', roll_id)['cover_photo_id']
    ids = [r['id'] for r in rows]
    if cover_id not in ids:
        cover_id = ids[0] if ids else None
    conn.execute('UPDATE roll_photos SET is_cover=(id=?) WHERE roll_id=?', (cover_id, roll_id)) if cover_id else None
    conn.execute('UPDATE film_rolls SET actual_frames=?, cover_photo_id=? WHERE id=?', (len(rows), cover_id, roll_id))
    touch(conn, roll_id)


def prepare_image(content, mime):
    if hasattr(content, 'read'):
        content = content.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise Problem('每张照片最多 50 MB，请缩小后重试', 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                fmt = source.format
                if fmt not in FORMATS or mime != FORMATS[fmt][0]:
                    raise Problem('请选择真实的 JPEG、PNG 或 WebP 照片，文件内容需与类型一致')
                source.verify()
            with Image.open(BytesIO(content)) as source:
                corrected = ImageOps.exif_transpose(source)
                corrected.load()
                if corrected.mode not in ('RGB', 'RGBA'):
                    corrected = corrected.convert('RGB')
                width, height = corrected.size
                # 原文件逐字节保留，避免 JPEG 二次压缩；方向修正用于尺寸和缩略图。
                # 原图在浏览器中通过 image-orientation: from-image 按 EXIF 展示。
                corrected.thumbnail((960, 960), Image.Resampling.LANCZOS)
                thumb = BytesIO()
                corrected.save(thumb, format='WEBP', quality=85)
                return content, thumb.getvalue(), width, height, FORMATS[fmt][1]
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise Problem('照片损坏或尺寸超过 8000 万像素，请换一张照片', 422) from None


class PhotoService:
    def __init__(self, db):
        self.db = db

    def upload(self, roll_id, files):
        if not files or len(files) > 40:
            raise Problem('每批请选择 1–40 张照片')
        created_paths = []
        with self.db.lock:
            try:
                with self.db.connect() as conn:
                    roll = require(conn, 'film_rolls', roll_id)
                    start = conn.execute('SELECT COUNT(*) FROM roll_photos WHERE roll_id=?', (roll_id,)).fetchone()[0]
                    ids = []
                    for i, (name, mime, content) in enumerate(sorted(files, key=lambda f: natural_key(f[0]))):
                        original, thumb, width, height, ext = prepare_image(content, mime)
                        token = uuid4().hex
                        folder = f"rolls/{roll['roll_number']:06}"
                        original_path, thumbnail_path = f'{folder}/originals/{token}.{ext}', f'{folder}/thumbnails/{token}.webp'
                        for path, payload in ((original_path, original), (thumbnail_path, thumb)):
                            target = safe_path(self.db, path)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            created_paths.append(target)
                            target.write_bytes(payload)
                        cursor = conn.execute('INSERT INTO roll_photos (roll_id,frame_number,file_path,thumbnail_path,original_filename,width,height,file_size,sort_order) VALUES (?,?,?,?,?,?,?,?,?)',
                                              (roll_id, start+i+1, original_path, thumbnail_path, name.replace('\\', '/').split('/')[-1][:255], width, height, len(original), start+i))
                        ids.append(cursor.lastrowid)
                    normalize(conn, roll_id)
                    advance(conn, roll_id, 'scanned')
                    return [photo_dict(require(conn, 'roll_photos', ident)) for ident in ids]
            except BaseException:
                for path in created_paths:
                    path.unlink(missing_ok=True)
                raise

    def edit(self, ident, data):
        values = clean(data, {'caption': ('text', 0, 2000), 'is_favorite': ('bool', 0, 1)})
        with self.db.connect() as conn:
            photo = require(conn, 'roll_photos', ident)
            update(conn, 'roll_photos', ident, values)
            touch(conn, photo['roll_id'])
            return photo_dict(require(conn, 'roll_photos', ident))

    def reorder(self, roll_id, ids):
        if not isinstance(ids, list) or any(type(i) is not int for i in ids):
            raise Problem('排序列表无效')
        with self.db.connect() as conn:
            require(conn, 'film_rolls', roll_id)
            current = [r[0] for r in conn.execute('SELECT id FROM roll_photos WHERE roll_id=?', (roll_id,))]
            if len(ids) != len(current) or set(ids) != set(current):
                raise Problem('照片列表已变化，请刷新后重新排序', 409)
            conn.executemany('UPDATE roll_photos SET sort_order=? WHERE id=?', [(i, ident) for i, ident in enumerate(ids)])
            normalize(conn, roll_id)

    def cover(self, roll_id, ident):
        with self.db.connect() as conn:
            require(conn, 'film_rolls', roll_id)
            photo = require(conn, 'roll_photos', ident)
            if photo['roll_id'] != roll_id:
                raise Problem('封面必须属于当前胶卷')
            conn.execute('UPDATE film_rolls SET cover_photo_id=? WHERE id=?', (ident, roll_id))
            normalize(conn, roll_id)

    def delete(self, ident):
        with self.db.lock:
            with self.db.connect() as conn:
                photo = require(conn, 'roll_photos', ident)
                conn.execute('DELETE FROM roll_photos WHERE id=?', (ident,))
                normalize(conn, photo['roll_id'])
            remove_files(self.db, photo)
