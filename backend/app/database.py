import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, data_dir=None, uploads_dir=None, backups_dir=None):
        root = Path(__file__).resolve().parents[2] / 'var'
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', root / 'data'))
        self.uploads_dir = Path(uploads_dir or os.getenv('UPLOADS_DIR', root / 'uploads'))
        self.backups_dir = Path(backups_dir or os.getenv('BACKUPS_DIR', root / 'backups'))
        self.path = self.data_dir / 'filmhub.sqlite3'
        self.lock = threading.RLock()
        for path in (self.data_dir, self.uploads_dir, self.backups_dir):
            path.mkdir(parents=True, exist_ok=True)
        # 未完成的恢复必须先回滚，再打开正式数据库。
        from .services.backup_service import recover_restore
        recover_restore(self)
        with self.connect() as conn:
            if conn.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
                raise RuntimeError('数据库版本不受支持，请使用匹配的 FilmHub 镜像')
            conn.executescript((Path(__file__).parent / 'models/schema.sql').read_text())
        from .services.storage_service import clean_orphan_images
        clean_orphan_images(self)

    @contextmanager
    def connect(self):
        with self.lock:
            conn = sqlite3.connect(self.path, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            try:
                with conn:
                    yield conn
            finally:
                conn.close()
