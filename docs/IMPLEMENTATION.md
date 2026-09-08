# FilmHub 开发与验收记录

更新日期：2026-09-08。

依据 `PLAN_v1.md`（文内标题为「开发计划 v2」）从空项目实施。代码范围覆盖 Task 0–19；下面的「已实现」表示代码与配置已落地，不等于 GitHub Actions 或目标设备人工验收已通过。

## 任务对应

| 计划任务 | 已实现内容 | 主要入口 |
| --- | --- | --- |
| 0 初始化 | Next.js、FastAPI、SQLite 默认值、环境模板、健康检查、Docker | `frontend/`、`backend/app/main.py`、`.env.example` |
| 1 数据模型 | FilmRoll、三类文字器材、多镜头关联、冲扫与照片表 | `backend/app/models/schema.sql` |
| 2 器材 API | 列表、创建、改名、删除、同名和引用保护 | `backend/app/services/archive_service.py` |
| 3 器材 UI | 单一 `/library` 三分区、名称编辑、新增对话框 | `frontend/src/app/library/page.tsx` |
| 4 胶卷 CRUD | 新建、编辑、删除、自动/自定编号、浏览器草稿、即时添加器材 | `frontend/src/components/roll/RollForm.tsx` |
| 5 首页档案 | 关键词搜索、状态、年份及收藏筛选 | `frontend/src/app/page.tsx` |
| 6 FilmFrame | CSS 有孔片基，card/hero/thumbnail/photo 四种变体 | `frontend/src/components/film/FilmFrame.tsx` |
| 7 首页 Film UI | 片基封面、胶卷编号与拍摄信息，档案式排版 | `frontend/src/components/roll/RollCard.tsx` |
| 8 冲洗与扫描 | 单卷记录 CRUD、常用字段、可展开高级字段 | `frontend/src/components/roll/ProcessForm.tsx` |
| 9 上传管线 | 每批 40 张、真实编码校验、保留原文件、方向校正、WebP、元数据、删除 | `backend/app/services/image_service.py` |
| 10 排序 | 拖放、键盘可用的前移后移、完整顺序校验、重编号 | `frontend/src/components/photo/PhotoSorter.tsx` |
| 11 整卷总览 | 桌面六列片基缩略图与帧号 | `frontend/src/components/roll/RollContactSheet.tsx` |
| 12 单张展示 | 帧号顺序、横竖全景原比例、图注与收藏 | `frontend/src/components/roll/RollPhotoFeed.tsx` |
| 13 锚点跳转 | 总览跳转 `#photo-N`，尊重减少动态效果偏好 | `RollContactSheet.tsx`、`globals.css` |
| 14 详情组合 | Hero、标题、基本信息、冲扫、总览、单张展示 | `frontend/src/app/rolls/[id]/page.tsx` |
| 15 生命周期 | 结束拍摄、冲洗、扫描/上传、归档，自动推进且不使归档倒退 | `archive_service.py`、详情页 |
| 16 统计 | 总卷数、照片数、本年、月份、胶片/相机/镜头使用分布 | `frontend/src/app/stats/page.tsx` |
| 17 响应式 | 首页 3/2/1 列、总览 6/4/2 列、移动端全宽单张、触控排序按钮 | `frontend/src/app/globals.css` |
| 18 Docker | Compose 三服务、健康检查、三持久卷、镜像 artifact、手动 GHCR 发布 | `docker/`、`compose.yaml`、`.github/workflows/ci.yml` |
| 19 备份恢复 | ZIP 快照和图片、SHA-256、输入校验、自动安全备份、失败/中断回滚 | `backend/app/services/backup_service.py`、设置页 |

## 已执行验证

本机只使用已有工具，未安装或升级 SDK、依赖和浏览器。

- `python3 -B scripts/check.py`：Python AST、JSON、路由和 CSS 结构轻量检查通过；16 个标准库/Pillow 服务案例通过。
- 服务案例实际生成并导入 40 张 JPEG，验证自然排序、WebP 文件和编号；覆盖 JPEG EXIF 原字节保留、旋转尺寸、透明 PNG 备份恢复、批次遇到坏图回滚。
- 覆盖胶卷生命周期、搜索与筛选、器材同名/引用保护、费用及日期验证、跨卷封面拦截、删除级联、统计、备份往返、非法路径/损坏备份拒绝、替换失败回滚、启动恢复与孤立上传清理。
- 利用本机已有 Playwright Babel 解析器完成 28 个 TypeScript/TSX 文件语法解析。这不是 TypeScript 类型检查，也不是浏览器运行结果。
- 利用已有 YAML 解析器解析 `compose.yaml` 和 `.github/workflows/ci.yml`。这不是 Docker Compose 构建验证。

## 已配置、尚待执行的正式验证

当前环境缺少 FastAPI、Uvicorn、HTTPX、项目 Node 依赖及 Docker，未为验证安装环境。工作区 `.git` 不提供有效的仓库元数据，不能查询远端或实际 Actions 运行结果；本轮没有 commit、push、镜像发布或部署。

GitHub Actions 将按以下顺序执行：

1. Python 3.12 还原依赖，执行全部服务测试和 3 个 HTTP 集成测试，覆盖健康检查、请求保护、40 文件 multipart、图片读取、冲扫 CRUD 和备份恢复。
2. Node 22 还原依赖，执行 TypeScript 严格检查与生产构建。
3. Chromium 浏览器执行完整验收：器材创建、草稿恢复、新建编号 036、结束日期、冲扫、36 张照片、封面/收藏/排序、锚点、6/4/2 列、照片比例、搜索统计、下载备份、删除整卷、恢复。
4. 额外浏览器案例覆盖新建页即时添加器材、取消对话框和网络失败后重试。
5. 在 CI 构建并启动真实 Compose 部署，经网关验证健康检查、页面、CRUD 和备份下载。
6. 输出 `filmhub-linux-amd64` 镜像包、依赖解析清单、浏览器报告/截图及容器日志。只在手动触发并勾选发布时推送 GHCR。

正式验证结果必须以第一次实际 Actions 运行结果为准。如果失败，需要按日志修复，不应直接视为交付验收通过。

## 实现决策与边界

### 首次 CI 注解修复

用户提供的 CI 注解显示前端在类型检查阶段退出：Playwright 回调参数为 `SVGElement | HTMLElement`，无法直接访问图片专属属性。现已在图片加载与比例检查中使用 `instanceof HTMLImageElement` 收窄类型；保留原有断言和正式类型检查步骤。

报告上传仅在浏览器验收步骤实际成功或失败后运行，避免类型检查失败导致测试跳过时上传不存在的报告。Actions 更新为 Node.js 24 运行时版本：checkout v5、setup-python v6、setup-node v5、upload-artifact v6、download-artifact v7，以及 Docker buildx/login v4。应用构建使用的 Node.js 仍为 22；Actions 运行时与应用版本是独立配置。版本依据各官方 `action.yml`，例如 [upload-artifact v6](https://github.com/actions/upload-artifact/blob/v6/action.yml) 和 [download-artifact v7](https://github.com/actions/download-artifact/blob/v7/action.yml)。

本次修复已通过本地 TypeScript 语法解析、YAML 与步骤引用检查和 `git diff --check`；尚未在本机还原项目依赖或执行正式类型检查，修复结果需由新一轮 CI 验证。此前的轻量语法检查无法发现这类类型错误。

### 既有实现边界

- 计划中的模型职责集中在一份显式 SQL 结构，HTTP 路由集中在 `routers/api.py`，服务按档案、图片、备份和存储分开；不为每个小表增加空模型或 ORM 抽象。
- 保留全部七个指定页面，不创建 `/films`、`/cameras`、`/lenses` 或独立照片详情路由。
- 未提供设计稿图片，视觉按计划中的 cream 纸色、深色片基、直角、小字编号、细线和留白实现；不伪造用户照片。
- 一个冲洗/扫描记录对应一卷；收藏筛选来自照片收藏。草稿为浏览器本地记录，正式胶卷必须指定胶片和相机。
- 首页封面可裁切；缩略图、Hero 和照片展示不裁切影像。缩略图修正 EXIF；原文件不重编码，原图展示按 EXIF 方向。
- 浏览器逐张请求显示进度并重试失败项；API 另支持一次 40 文件原子上传。排序保存必须包含当前所有照片，避免并发修改导致遗漏。
- SQLite 和文件一致性以单进程锁协调。上传事务失败立即清理新文件，进程中断遗留的未引用图片在下次启动清理。
- 备份恢复包含事务标记和进程中断恢复，但不代替独立设备备份，也不宣称抵御底层存储损坏。
- V1 无账户认证，默认只开放本机；没有自动部署。容器包当前目标为 Linux AMD64，ARM64 未经构建或验收。
- 仓库尚无生成的依赖锁文件。CI 会导出精确解析版本，并在同一次容器构建中复用；不同次首次解析存在版本漂移的可能。

## 人工验收

下载 Actions artifact 后按 README 启动，在实际浏览器与设备上检查：

- 添加常用器材，新建一卷，关闭并重新打开页面后记录仍在。
- 用自己的 36–40 张照片导入，尤其包括带 EXIF 旋转、竖幅、全景和较大文件；检查色彩、方向、图片清晰度与可接受的上传耗时。
- 检查桌面六列和手机两列总览，跳转帧号、拖动/按钮排序、封面与收藏。
- 下载备份，再在独立测试实例恢复；确认胶卷、冲扫记录、原图与缩略图数量一致。
- 重建容器后检查持久卷保留档案。

人工验收通过后再发布；此清单尚未勾选。
