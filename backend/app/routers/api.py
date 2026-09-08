from tempfile import SpooledTemporaryFile

from fastapi import APIRouter, Body, File, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse

from ..schemas.validation import Problem
from ..services.archive_service import ArchiveService
from ..services.backup_service import BackupService, MAX_BACKUP_BYTES
from ..services.image_service import PhotoService

router = APIRouter(prefix='/api')


@router.get('/health')
def health(request: Request):
    with request.app.state.db.connect() as conn:
        conn.execute('SELECT 1')
    return {'status': 'ok', 'version': 1}


@router.get('/library')
def library(request: Request):
    return ArchiveService(request.app.state.db).library()


@router.post('/library/{kind}', status_code=201)
def create_library(kind: str, request: Request, data: dict = Body(...)):
    return ArchiveService(request.app.state.db).save_library(kind, data)


@router.put('/library/{kind}/{ident}')
def edit_library(kind: str, ident: int, request: Request, data: dict = Body(...)):
    return ArchiveService(request.app.state.db).save_library(kind, data, ident)


@router.delete('/library/{kind}/{ident}', status_code=204)
def delete_library(kind: str, ident: int, request: Request):
    ArchiveService(request.app.state.db).delete_library(kind, ident)
    return Response(status_code=204)


@router.get('/rolls')
def rolls(request: Request, q: str = Query('', max_length=200), status: str = '', year: int | None = Query(None, ge=1, le=9999)):
    return ArchiveService(request.app.state.db).rolls(q, status, year)


@router.post('/rolls', status_code=201)
def create_roll(request: Request, data: dict = Body(...)):
    return ArchiveService(request.app.state.db).save_roll(data)


@router.get('/rolls/{ident}')
def roll(ident: int, request: Request):
    return ArchiveService(request.app.state.db).roll(ident)


@router.put('/rolls/{ident}')
def edit_roll(ident: int, request: Request, data: dict = Body(...)):
    return ArchiveService(request.app.state.db).save_roll(data, ident)


@router.delete('/rolls/{ident}', status_code=204)
def delete_roll(ident: int, request: Request):
    ArchiveService(request.app.state.db).delete_roll(ident)
    return Response(status_code=204)


@router.get('/rolls/{ident}/development')
@router.get('/rolls/{ident}/scan')
def record(ident: int, request: Request):
    key = request.url.path.rsplit('/', 1)[-1]
    return ArchiveService(request.app.state.db).roll(ident)[key]


@router.post('/rolls/{ident}/development', status_code=201)
@router.put('/rolls/{ident}/development')
@router.post('/rolls/{ident}/scan', status_code=201)
@router.put('/rolls/{ident}/scan')
def save_record(ident: int, request: Request, data: dict = Body(...)):
    table = 'developments' if request.url.path.endswith('/development') else 'scans'
    return ArchiveService(request.app.state.db).save_record(ident, table, data)


@router.delete('/rolls/{ident}/development', status_code=204)
@router.delete('/rolls/{ident}/scan', status_code=204)
def delete_record(ident: int, request: Request):
    table = 'developments' if request.url.path.endswith('/development') else 'scans'
    ArchiveService(request.app.state.db).delete_record(ident, table)
    return Response(status_code=204)


@router.get('/rolls/{ident}/photos')
def photos(ident: int, request: Request):
    return ArchiveService(request.app.state.db).roll(ident)['photos']


@router.post('/rolls/{ident}/photos', status_code=201)
def upload_photos(ident: int, request: Request, files: list[UploadFile] = File(...)):
    try:
        return PhotoService(request.app.state.db).upload(ident, [(f.filename or 'photo', f.content_type, f.file) for f in files])
    finally:
        for file in files:
            file.file.close()


@router.put('/rolls/{ident}/photos/reorder', status_code=204)
def reorder(ident: int, request: Request, data: dict = Body(...)):
    if set(data) != {'photo_ids'}:
        raise Problem('请提供完整的 photo_ids 排序列表')
    PhotoService(request.app.state.db).reorder(ident, data['photo_ids'])
    return Response(status_code=204)


@router.put('/rolls/{ident}/cover/{photo_id}', status_code=204)
def cover(ident: int, photo_id: int, request: Request):
    PhotoService(request.app.state.db).cover(ident, photo_id)
    return Response(status_code=204)


@router.put('/photos/{ident}')
def edit_photo(ident: int, request: Request, data: dict = Body(...)):
    return PhotoService(request.app.state.db).edit(ident, data)


@router.delete('/photos/{ident}', status_code=204)
def delete_photo(ident: int, request: Request):
    PhotoService(request.app.state.db).delete(ident)
    return Response(status_code=204)


@router.get('/stats')
def stats(request: Request):
    return ArchiveService(request.app.state.db).stats()


@router.get('/backups')
def backups(request: Request):
    return BackupService(request.app.state.db).list()


@router.post('/backups', status_code=201)
def create_backup(request: Request):
    return BackupService(request.app.state.db).create()


@router.get('/backups/{name}')
def download_backup(name: str, request: Request):
    return FileResponse(BackupService(request.app.state.db).path(name), media_type='application/zip', filename=name)


@router.post('/restore')
def restore(request: Request, file: UploadFile = File(...), confirm: str = Query('')):
    try:
        if confirm != 'restore':
            raise Problem('恢复将替换现有档案，请先确认', 409)
        with SpooledTemporaryFile(max_size=1024 * 1024) as temporary:
            total = 0
            while chunk := file.file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_BACKUP_BYTES:
                    raise Problem('备份不能超过 4 GB', 413)
                temporary.write(chunk)
            temporary.seek(0)
            return BackupService(request.app.state.db).restore(temporary)
    finally:
        file.file.close()
