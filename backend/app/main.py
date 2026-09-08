import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import Database
from .routers.api import router
from .schemas.validation import Problem


class RequestGuard:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        if scope['method'] in ('POST', 'PUT', 'PATCH', 'DELETE') and headers.get(b'x-filmhub-request') != b'1':
            return await JSONResponse({'detail': '请从 FilmHub 页面执行此操作'}, 403)(scope, receive, send)
        limit = (4 * 1024**3 + 1024**2) if scope['path'] == '/api/restore' else (2 * 1024**3 + 1024**2) if scope['path'].endswith('/photos') else 1024**2
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await JSONResponse({'detail': '请求长度无效'}, 400)(scope, receive, send)
        if length > limit:
            return await JSONResponse({'detail': '上传内容过大，请分批上传'}, 413)(scope, receive, send)
        consumed = 0
        async def limited_receive():
            nonlocal consumed
            message = await receive()
            consumed += len(message.get('body', b''))
            if consumed > limit:
                from starlette.exceptions import HTTPException
                raise HTTPException(413, '上传内容过大，请分批上传')
            return message
        async def secure_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] = [*message.get('headers', []), (b'x-content-type-options', b'nosniff'), (b'cache-control', b'no-store')]
            await send(message)
        await self.app(scope, limited_receive, secure_send)


def create_app(database=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.db = database or Database()
        # 只公开图片子目录，临时恢复数据无法通过 HTTP 读取。
        (app.state.db.uploads_dir / 'rolls').mkdir(exist_ok=True)
        app.mount('/uploads/rolls', StaticFiles(directory=app.state.db.uploads_dir / 'rolls'), name='uploads')
        yield

    app = FastAPI(title='FilmHub', version='1.0.0', lifespan=lifespan)
    app.add_middleware(RequestGuard)
    app.include_router(router)

    @app.exception_handler(Problem)
    async def problem_handler(request: Request, error: Problem):
        return JSONResponse({'detail': error.message}, error.status)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, error: RequestValidationError):
        return JSONResponse({'detail': '输入格式无效，请检查必填项、数字和文件'}, 422)

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, error: Exception):
        logging.exception('FilmHub request failed')
        return JSONResponse({'detail': '操作未完成，请重试；若持续失败，请检查存储空间及服务日志'}, 500)

    return app


app = create_app()
