import math
from datetime import date


class Problem(Exception):
    def __init__(self, message, status=422):
        self.message, self.status = message, status
        super().__init__(message)


STATUSES = ['shooting', 'finished', 'developed', 'scanned', 'archived']


def clean(data, fields):
    unknown = set(data) - set(fields)
    if unknown:
        raise Problem('不支持的字段：' + ', '.join(sorted(unknown)))
    result = {}
    for key, value in data.items():
        kind, minimum, maximum = fields[key]
        if kind == 'text':
            if not isinstance(value, str) or len(value) > maximum:
                raise Problem(f'{key} 需要不超过 {maximum} 字的文字')
            result[key] = value.strip()
        elif kind == 'date':
            if value in ('', None):
                result[key] = None
            else:
                try:
                    result[key] = date.fromisoformat(value).isoformat()
                except (ValueError, TypeError):
                    raise Problem(f'{key} 日期格式应为 YYYY-MM-DD') from None
        elif kind == 'bool':
            if not isinstance(value, bool):
                raise Problem(f'{key} 必须是布尔值')
            result[key] = int(value)
        else:
            if value is None and minimum is None:
                result[key] = None
                continue
            expected = int if kind == 'int' else (int, float)
            if isinstance(value, bool) or not isinstance(value, expected) or (isinstance(value, float) and not math.isfinite(value)):
                raise Problem(f'{key} 必须是有效数字')
            if value < (minimum if minimum is not None else 0) or value > maximum:
                raise Problem(f'{key} 超出允许范围')
            result[key] = value
    return result


ROLL_FIELDS = {
    **{key: ('text', 0, 200) for key in ('title', 'location')},
    'description': ('text', 0, 10000), 'status': ('text', 0, 20),
    **{key: ('int', 1, 2147483647) for key in ('roll_number', 'film_stock_id', 'camera_id')},
    'shot_iso': ('int', None, 102400), 'expected_frames': ('int', 1, 1000),
    'started_at': ('date', 0, 0), 'finished_at': ('date', 0, 0),
}
RECORD_FIELDS = {
    'developments': {
        **{key: ('text', 0, 200) for key in ('method', 'lab_name', 'process', 'developer', 'currency')},
        'temperature_c': ('float', None, 100), 'development_time_sec': ('int', None, 86400),
        'push_pull': ('float', -10, 10), 'developed_at': ('date', 0, 0),
        'cost': ('float', None, 1000000), 'notes': ('text', 0, 10000),
    },
    'scans': {
        **{key: ('text', 0, 200) for key in ('method', 'lab_name', 'scanner_model', 'file_format', 'currency')},
        **{key: ('int', None, 100000) for key in ('resolution_width', 'resolution_height')},
        'scanned_at': ('date', 0, 0), 'cost': ('float', None, 1000000), 'notes': ('text', 0, 10000),
    },
}
