import logging


def clean_orphan_images(db):
    """清理上次进程中断时已写文件但尚未提交记录的照片。"""
    with db.connect() as conn:
        referenced = {value for row in conn.execute('SELECT file_path,thumbnail_path FROM roll_photos') for value in row}
    root = db.uploads_dir / 'rolls'
    if not root.exists():
        return
    for file in root.rglob('*'):
        if file.is_file() and file.relative_to(db.uploads_dir).as_posix() not in referenced:
            try:
                file.unlink()
            except OSError:
                logging.warning('Unable to clean orphan image: %s', file)
