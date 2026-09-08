# FilmHub

以每一卷胶片为单位，记录拍摄、冲洗与扫描，并用有孔片基、整卷总览和原比例单张展示留住照片。

实现范围见 [产品计划](docs/PLAN_v1.md) 和 [开发与验收记录](docs/IMPLEMENTATION.md)。代码已覆盖计划 Task 0–19；当前工作区完成轻量验证，正式构建、HTTP 集成及浏览器验收待 GitHub Actions 执行，不代表已经通过发布验收。

## 使用流程

1. 在「器材库」添加常用胶片、相机、镜头；也可以在新建胶卷时直接添加并选中。
2. 点击「新增胶卷」，选择胶片和相机，填写 EI、开始日期、地点、标题等。一卷支持多个镜头。编号默认递增，也可在创建时指定 `36`；创建后编号固定。
3. 拍完后结束拍摄，或编辑结束日期；在详情页补录冲洗和扫描。药水、温度、时间与费用放在「更多信息」。
4. 打开「上传 / 管理照片」，一次选择或拖入最多 40 张照片。进度显示实际处理张数，失败项可以单独重试。
5. 拖动照片排序，也可使用前移 / 后移按钮；设置封面、收藏、图注，或删除照片。顺序保存后自动更新帧号。总览可直接跳转到对应的单张展示。
6. 在「设置」生成完整备份并下载；需要时选择备份，确认替换后同步恢复数据和图片。

首页可搜索编号、标题、胶片、相机、镜头、地点和备注，按状态、年份或收藏筛选。「已冲扫」包含已冲洗、已扫描和已归档；「收藏」显示至少有一张收藏照片的胶卷。没有指定封面时自动使用第一张照片。

草稿仅存于当前浏览器，不占胶卷编号，也不进入统计或服务器备份。统计中的「今年拍摄」和月份以开始日期为准；没有开始日期的胶卷仍计入总数，并按创建年份在首页筛选。

## 下载与启动

开发环境不需要在本机安装。将源码同步到 GitHub 后，工作流会完成依赖还原、正式测试和构建；全部通过后提供 `filmhub-linux-amd64` artifact，内含 API、Web、Nginx 三个镜像及部署文件。`browser-acceptance` artifact 包含浏览器报告和截图。

在装有 Docker 与 Compose 的 Linux AMD64 目标环境中，下载并解压 artifact，进入解压目录：

```bash
docker load -i filmhub-images.tar.gz
docker compose up -d --no-build
```

浏览器打开 `http://localhost:3080`。无需 `.env` 或手工设置数据库。Compose 默认只绑定 `127.0.0.1`，API 和图片通过同源网关访问。远程服务器可以通过 SSH 转发使用：

```bash
ssh -L 3080:127.0.0.1:3080 user@server
```

V1 是单人档案，没有登录及多账户功能。需要局域网或公网入口时，应在现有访问控制的反向代理后接入；不直接改为公开匿名编辑入口。

`.env.example` 提供端口和镜像配置。要调整端口，可复制为 `.env` 并修改 `FILMHUB_PORT`。不要把密钥写进配置或提交到仓库。

常用命令：

```bash
docker compose ps
docker compose logs --tail=100 api web gateway
docker compose stop
docker compose up -d --no-build
```

部署只通过 Compose 完成，不自动部署、不依赖 `git push`。人工验收通过后才作为发布依据。

## GHCR 镜像

GitHub Actions 的手动运行入口提供 `publish_images` 开关，默认关闭。勾选后，工作流仍先执行全部测试和打包，再将同一批镜像发布为：

```text
ghcr.io/<owner>/<repository>-api:<commit-sha>
ghcr.io/<owner>/<repository>-web:<commit-sha>
```

下载部署配置后，在 `.env` 中设置：

```dotenv
FILMHUB_IMAGE=ghcr.io/<owner>/<repository>
FILMHUB_TAG=<commit-sha>
FILMHUB_PORT=3080
```

在目标设备登录 GHCR（私有镜像需要）并执行：

```bash
docker compose pull
docker compose up -d --no-build
```

发布镜像不会连接目标设备或自动部署。

## 持久化与照片

Compose 使用三个独立命名卷：

| 卷 | 容器路径 | 内容 |
| --- | --- | --- |
| `data` | `/data` | SQLite 数据库和恢复事务标记 |
| `uploads` | `/uploads` | 上传原文件及 WebP 缩略图 |
| `backups` | `/backups` | 完整 ZIP 备份、恢复前自动备份 |

图片目录示例：

```text
/uploads/rolls/000036/
  originals/<uuid>.jpg
  thumbnails/<uuid>.webp
```

支持 JPEG、PNG、WebP，不支持 RAW；每张最多 50 MB、8000 万像素。服务检查声明 MIME 与实际编码，完整保留原文件，避免 JPEG 二次压缩。Pillow 修正 EXIF 方向后计算显示宽高，并生成最长边 960 像素的 WebP 缩略图；浏览器按 EXIF 显示原图。首页封面允许裁切，其余展示保留原比例。

批量导入按文件名自然排序，例如 `2.jpg` 在 `10.jpg` 前。浏览器逐张提交，控制内存并显示进度；HTTP API 同时支持单次请求 40 张。整批 API 上传遇到坏图会回滚该批次。浏览器已成功的文件保留，重试失败照片会追加在末尾，可再拖动调整。帧号始终来自保存后的顺序。

删除胶卷会级联删除冲扫与照片记录，并清理对应文件；正在被引用的器材不能删除。启动时清理仅写入文件、尚未提交数据库的中断上传。`/uploads/rolls/` 是应用专用目录，不用于手工存放其他文件。

## 备份与恢复

「设置 → 生成完整备份」会得到 `backup-YYYYMMDD-HHMMSS-随机后缀.zip`。文件名时间为 UTC，并用后缀防止同秒备份互相覆盖。

备份包含：

- SQLite 一致性快照。
- 数据库引用的全部原图和缩略图。
- 版本及 SHA-256 文件清单。

生成和恢复时会短暂阻塞其他档案读写。恢复要求 ZIP 不超过 4 GB，展开后不超过 20 GB；恢复前检查路径、文件清单、校验和、表结构、外键、照片数量、排序、封面及图片编码。数据库和图片必须同时存在且匹配。

用户确认后，先备份当前档案，再替换数据库和图片。替换失败会回滚；若进程中断，下次启动会根据恢复标记回滚未完成的替换。该机制针对进程中断，不承诺硬件损坏或底层存储未持久化时的恢复能力。备份应下载到其他设备保存。

恢复不会删除备份卷中的旧备份。若需要回到恢复前的状态，下载系统提示的自动备份，再次通过设置页恢复。不要单独复制一个正在使用的 SQLite 文件作为整站备份，也不要分别恢复不同时间点的数据库和图片。

运行数据由 Docker 卷持久化，容器重建不会清空档案。`docker compose down -v` 会删除这些卷，不是正常更新或停止命令。

## 本地开发与验证

技术栈：Next.js App Router / React / TypeScript / 原生 CSS；FastAPI / Python `sqlite3` / Pillow。没有 ORM、器材资产字段、注册、社交或 AI 功能。Next.js 选用 `15.5.24`，对应官方维护分支的 [2026 年 8 月安全更新](https://nextjs.org/blog/august-2026-security-release)。

目录约定见 [AGENTS.md](AGENTS.md)。正式依赖还原、类型检查、构建、集成与浏览器测试统一由 [.github/workflows/ci.yml](.github/workflows/ci.yml) 执行。本地不为验证安装或升级环境。

已有 Python 和 Pillow 时可执行轻量检查：

```bash
python3 -B scripts/check.py
```

如果开发环境已经具有项目依赖，可以分别启动 API 与前端：

```bash
# backend 目录
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
# frontend 目录
npm run dev
```

访问 `http://localhost:3000`；Next.js 将 API 和图片代理到 `127.0.0.1:8000`。本地数据默认保存在 `backend/var/`，已由忽略规则排除。生产上传和备份由 Nginx 直接代理 API，不经过前端开发代理。

后端固定单 worker，各写入、备份和恢复使用同一进程锁；不要增加 worker 或多个 API 副本共同写入相同持久卷。没有通过修改 CI 来绕过本机环境缺失。

CI 首次生成前端 `package-lock.json` 和 Python 已解析版本清单，并把它们随 artifact 提供；容器打包使用这批经过验证的依赖版本。后续需要固定仓库级锁文件时，可将 CI 生成的前端锁文件纳入版本控制。不同次 CI 在没有仓库锁文件时可能解析到不同的兼容依赖。

## API 约定

健康检查为 `GET /api/health`，正常返回 `{"status":"ok","version":1}`。

所有写请求必须携带 `X-FilmHub-Request: 1`；浏览器客户端自动发送，以阻止跨站表单写入。该标头不是身份认证。错误使用中文 `detail`，不存在返回 404，引用/编号冲突返回 409，输入不合法返回 422，上传过大返回 413。

| 路径 | 方法 | 用途 |
| --- | --- | --- |
| `/api/library` | GET | 胶片、相机、镜头列表 |
| `/api/library/{films\|cameras\|lenses}` | POST | 新增文字条目 |
| `/api/library/{kind}/{id}` | PUT / DELETE | 重命名、删除 |
| `/api/rolls` | GET / POST | 搜索筛选、创建胶卷 |
| `/api/rolls/{id}` | GET / PUT / DELETE | 胶卷详情与修改 |
| `/api/rolls/{id}/development` | GET / POST / PUT / DELETE | 单卷冲洗记录 |
| `/api/rolls/{id}/scan` | GET / POST / PUT / DELETE | 单卷扫描记录 |
| `/api/rolls/{id}/photos` | GET / POST | 照片列表、multipart 批量上传，字段 `files` |
| `/api/rolls/{id}/photos/reorder` | PUT | 提交完整 `photo_ids` 数组 |
| `/api/rolls/{id}/cover/{photo_id}` | PUT | 设置本卷封面 |
| `/api/photos/{id}` | PUT / DELETE | 图注、收藏、删除 |
| `/api/stats` | GET | 摄影统计 |
| `/api/backups` | GET / POST | 列出、创建备份 |
| `/api/backups/{name}` | GET | 下载备份 |
| `/api/restore?confirm=restore` | POST | multipart 字段 `file`，确认恢复 |

每卷保留一条当前冲洗记录和一条当前扫描记录，重复保存更新同一条记录。自动状态只前进；删除冲扫记录或照片不会自动退回。用户可在编辑页调整状态，但不能低于现存冲洗、扫描和照片所对应的阶段。归档后补录不改变已归档状态。
