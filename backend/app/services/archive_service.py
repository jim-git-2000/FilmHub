import sqlite3
from datetime import date

from ..schemas.validation import Problem, ROLL_FIELDS, RECORD_FIELDS, STATUSES, clean

LIBRARY = {'films': 'film_stocks', 'cameras': 'cameras', 'lenses': 'lenses'}


def require(conn, table, ident):
    if type(ident) is not int or ident < 1 or ident > 9223372036854775807:
        raise Problem('记录编号无效')
    row = conn.execute(f'SELECT * FROM {table} WHERE id=?', (ident,)).fetchone()
    if row is None:
        raise Problem('记录不存在或已被删除', 404)
    return dict(row)


def update(conn, table, ident, values):
    if values:
        conn.execute(f'UPDATE {table} SET ' + ','.join(f'{k}=?' for k in values) + ' WHERE id=?', (*values.values(), ident))


def advance(conn, roll_id, status):
    current = require(conn, 'film_rolls', roll_id)['status']
    if STATUSES.index(current) < STATUSES.index(status):
        conn.execute('UPDATE film_rolls SET status=? WHERE id=?', (status, roll_id))
    touch(conn, roll_id)


def touch(conn, roll_id):
    conn.execute("UPDATE film_rolls SET updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?", (roll_id,))


def photo_dict(row):
    result = dict(row)
    result['is_cover'] = bool(result['is_cover'])
    result['is_favorite'] = bool(result['is_favorite'])
    result['url'] = '/uploads/' + result['file_path']
    result['thumbnail_url'] = '/uploads/' + result['thumbnail_path']
    return result


def roll_dict(conn, row, detail=False):
    roll = dict(row)
    roll['film_stock'] = require(conn, 'film_stocks', roll['film_stock_id'])['name']
    roll['camera'] = require(conn, 'cameras', roll['camera_id'])['name']
    roll['lenses'] = [dict(r) for r in conn.execute('SELECT l.* FROM lenses l JOIN film_roll_lenses rl ON rl.lens_id=l.id WHERE rl.roll_id=? ORDER BY l.name', (roll['id'],))]
    cover = conn.execute('SELECT * FROM roll_photos WHERE roll_id=? ORDER BY is_cover DESC, sort_order LIMIT 1', (roll['id'],)).fetchone()
    roll['cover'] = photo_dict(cover) if cover else None
    roll['is_favorite'] = bool(conn.execute('SELECT 1 FROM roll_photos WHERE roll_id=? AND is_favorite=1 LIMIT 1', (roll['id'],)).fetchone())
    if detail:
        roll['photos'] = [photo_dict(r) for r in conn.execute('SELECT * FROM roll_photos WHERE roll_id=? ORDER BY sort_order', (roll['id'],))]
        for table, key in (('developments', 'development'), ('scans', 'scan')):
            record = conn.execute(f'SELECT * FROM {table} WHERE roll_id=?', (roll['id'],)).fetchone()
            roll[key] = dict(record) if record else None
    return roll


class ArchiveService:
    def __init__(self, db):
        self.db = db

    def library(self):
        with self.db.connect() as conn:
            return {kind: [dict(r) for r in conn.execute(f'SELECT * FROM {table} ORDER BY name COLLATE NOCASE')] for kind, table in LIBRARY.items()}

    def save_library(self, kind, data, ident=None):
        if kind not in LIBRARY:
            raise Problem('器材类别不存在', 404)
        values = clean(data, {'name': ('text', 0, 200)})
        if not values.get('name'):
            raise Problem('请输入名称')
        with self.db.connect() as conn:
            if ident is not None:
                require(conn, LIBRARY[kind], ident)
            try:
                if ident is None:
                    ident = conn.execute(f'INSERT INTO {LIBRARY[kind]} (name) VALUES (?)', (values['name'],)).lastrowid
                else:
                    update(conn, LIBRARY[kind], ident, values)
            except sqlite3.IntegrityError:
                raise Problem('已有同名条目，请直接选择或换一个名称', 409) from None
            return require(conn, LIBRARY[kind], ident)

    def delete_library(self, kind, ident):
        if kind not in LIBRARY:
            raise Problem('器材类别不存在', 404)
        with self.db.connect() as conn:
            require(conn, LIBRARY[kind], ident)
            try:
                conn.execute(f'DELETE FROM {LIBRARY[kind]} WHERE id=?', (ident,))
            except sqlite3.IntegrityError:
                raise Problem('该条目正在被胶卷使用，请先编辑相关胶卷', 409) from None

    def rolls(self, query='', status='', year=None):
        query = query.strip()
        if status and status not in [*STATUSES, 'processed', 'favorite']:
            raise Problem('筛选状态无效')
        with self.db.connect() as conn:
            rows = conn.execute('SELECT * FROM film_rolls ORDER BY COALESCE(started_at, substr(created_at,1,10)) DESC, roll_number DESC')
            result = []
            for row in rows:
                roll = roll_dict(conn, row)
                if status == 'processed' and roll['status'] not in ('developed', 'scanned', 'archived'):
                    continue
                if status == 'favorite' and not roll['is_favorite']:
                    continue
                if status in STATUSES and roll['status'] != status:
                    continue
                if year and (roll['started_at'] or roll['created_at'])[:4] != str(year):
                    continue
                haystack = ' '.join([str(roll['roll_number']), roll['title'], roll['description'], roll['location'], roll['film_stock'], roll['camera'], *[l['name'] for l in roll['lenses']]])
                if query.casefold() not in haystack.casefold():
                    continue
                result.append(roll)
            return result

    def roll(self, ident):
        with self.db.connect() as conn:
            return roll_dict(conn, require(conn, 'film_rolls', ident), True)

    def save_roll(self, data, ident=None):
        data = dict(data)
        lens_ids = data.pop('lens_ids', None)
        if lens_ids is not None and (not isinstance(lens_ids, list) or any(type(x) is not int or x < 1 for x in lens_ids) or len(set(lens_ids)) != len(lens_ids)):
            raise Problem('镜头列表无效')
        values = clean(data, ROLL_FIELDS)
        if values.get('shot_iso') is not None and values['shot_iso'] < 1:
            raise Problem('拍摄 EI 必须大于零')
        with self.db.connect() as conn:
            current = require(conn, 'film_rolls', ident) if ident else {}
            merged = {**current, **values}
            if not merged.get('film_stock_id') or not merged.get('camera_id'):
                raise Problem('请选择胶片和相机')
            for field, table in [('film_stock_id', 'film_stocks'), ('camera_id', 'cameras')]:
                require(conn, table, merged[field])
            for lens_id in lens_ids or []:
                require(conn, 'lenses', lens_id)
            if merged.get('started_at') and merged.get('finished_at') and merged['finished_at'] < merged['started_at']:
                raise Problem('结束日期不能早于开始日期')
            if 'status' in values and values['status'] not in STATUSES:
                raise Problem('胶卷状态无效')
            # 编号同时用于文件目录，创建后保持稳定。
            if ident and 'roll_number' in values and values['roll_number'] != current['roll_number']:
                raise Problem('胶卷编号创建后不可修改')
            try:
                if ident:
                    update(conn, 'film_rolls', ident, values)
                else:
                    values.setdefault('roll_number', conn.execute('SELECT COALESCE(MAX(roll_number),0)+1 FROM film_rolls').fetchone()[0])
                    ident = conn.execute(f"INSERT INTO film_rolls ({','.join(values)}) VALUES ({','.join('?' for _ in values)})", tuple(values.values())).lastrowid
            except sqlite3.IntegrityError:
                raise Problem('胶卷编号已存在，请使用其他编号', 409) from None
            if lens_ids is not None:
                conn.execute('DELETE FROM film_roll_lenses WHERE roll_id=?', (ident,))
                conn.executemany('INSERT INTO film_roll_lenses VALUES (?,?)', [(ident, lens) for lens in lens_ids])
            minimum = 'finished' if merged.get('finished_at') else 'shooting'
            if conn.execute('SELECT 1 FROM developments WHERE roll_id=?', (ident,)).fetchone():
                minimum = 'developed'
            if conn.execute('SELECT 1 FROM scans WHERE roll_id=?', (ident,)).fetchone() or conn.execute('SELECT 1 FROM roll_photos WHERE roll_id=?', (ident,)).fetchone():
                minimum = 'scanned'
            advance(conn, ident, minimum)
            return roll_dict(conn, require(conn, 'film_rolls', ident), True)

    def delete_roll(self, ident):
        from .image_service import remove_files
        with self.db.lock:
            with self.db.connect() as conn:
                require(conn, 'film_rolls', ident)
                files = [dict(r) for r in conn.execute('SELECT * FROM roll_photos WHERE roll_id=?', (ident,))]
                conn.execute('DELETE FROM film_rolls WHERE id=?', (ident,))
            for photo in files:
                remove_files(self.db, photo)

    def save_record(self, ident, table, data):
        values = clean(data, RECORD_FIELDS[table])
        if any(values.get(key) is not None and values[key] < 1 for key in ('resolution_width', 'resolution_height')):
            raise Problem('扫描分辨率必须大于零')
        if 'method' in values and values['method'] not in ('lab', 'self'):
            raise Problem('请选择送店或自助')
        if 'currency' in values and (len(values['currency']) != 3 or not values['currency'].isascii() or not values['currency'].isalpha()):
            raise Problem('币种应为三位字母，例如 CNY')
        with self.db.connect() as conn:
            require(conn, 'film_rolls', ident)
            conn.execute(f'INSERT OR IGNORE INTO {table} (roll_id) VALUES (?)', (ident,))
            record_id = conn.execute(f'SELECT id FROM {table} WHERE roll_id=?', (ident,)).fetchone()[0]
            update(conn, table, record_id, values)
            advance(conn, ident, 'developed' if table == 'developments' else 'scanned')
            return require(conn, table, record_id)

    def delete_record(self, ident, table):
        with self.db.connect() as conn:
            require(conn, 'film_rolls', ident)
            conn.execute(f'DELETE FROM {table} WHERE roll_id=?', (ident,))
            touch(conn, ident)

    def stats(self):
        rolls = self.rolls()
        def usage(key):
            counts = {}
            for roll in rolls:
                names = [l['name'] for l in roll['lenses']] if key == 'lenses' else [roll[key]]
                for name in names:
                    counts[name] = counts.get(name, 0) + 1
            return [{'name': k, 'count': v} for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
        year = str(date.today().year)
        return {
            'total_rolls': len(rolls), 'total_photos': sum(r['actual_frames'] for r in rolls),
            'this_year': sum(bool(r['started_at'] and r['started_at'].startswith(year)) for r in rolls),
            'year': int(year),
            'months': [{'name': f'{i:02}', 'count': sum(bool(r['started_at'] and r['started_at'].startswith(f'{year}-{i:02}')) for r in rolls)} for i in range(1, 13)],
            'films': usage('film_stock'), 'cameras': usage('camera'), 'lenses': usage('lenses'),
            'years': sorted({(r['started_at'] or r['created_at'])[:4] for r in rolls}, reverse=True),
        }
