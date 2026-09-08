# FilmHub 开发计划 v2

## 1. 产品定位

FilmHub 是一个以“每一卷胶片”为核心单位的个人胶片拍摄记录与展示网站。

它不是器材管理工具，也不是摄影资产管理系统。

核心用途只有三件事：

1. 记录每一卷胶片的拍摄信息。
2. 记录这卷胶片的冲洗与扫描信息。
3. 以接近真实胶片 / 底片的视觉方式展示整卷照片。

核心对象只有：

```text
Film Roll
一卷实际拍摄过的胶片
```

其他信息：

```text
胶片
相机
镜头
```

只是创建胶卷时可复用的文本选项，不作为独立资产管理对象。

---

# 2. 核心导航

新版导航精简为：

```text
胶卷档案
器材库
统计
设置
```

首页 Logo 点击返回 `/`。

不再存在：

```text
/films
/cameras
/lenses
```

也不再为这些对象设计独立管理页面。

---

# 3. 页面结构

V1 控制在以下页面：

```text
/
胶卷档案首页

/rolls/new
新增胶卷

/rolls/[id]
胶卷详情

/rolls/[id]/edit
编辑胶卷

/library
器材库

/stats
统计

/settings
设置
```

核心页面实际只有：

```text
首页
胶卷详情
新增 / 编辑胶卷
器材库
```

---

# 4. 数据模型调整

## 4.1 FilmRoll

这是系统核心表。

```text
film_rolls
```

字段建议：

```text
id

roll_number
title
description

film_stock_id
camera_id

shot_iso

started_at
finished_at

location

status

expected_frames
actual_frames

cover_photo_id

created_at
updated_at
```

状态：

```text
shooting
finished
developed
scanned
archived
```

UI 中文：

```text
拍摄中
已拍完
已冲洗
已扫描
已归档
```

---

# 5. 器材库重新定义

原方案中的：

```text
FilmStock
Camera
Lens
```

仍然可以保留数据库表。

但它们不再拥有复杂业务字段。

它们仅仅是：

> 可复用文字条目。

因此模型极度简化。

---

## 5.1 FilmStock

```text
film_stocks

id
name
created_at
```

例如：

```text
Kodak Portra 400
Kodak Gold 200
Fujifilm C200
Ilford HP5+
```

第一版不记录：

```text
厂家
ISO
冲洗工艺
胶片类型
规格
包装图
库存
数量
购买价格
保质期
```

这些属于“器材 / 库存管理”，不是 FilmHub 的目标。

如果 Roll 自己需要这些信息，可以存在 Roll 上。

---

## 5.2 Camera

```text
cameras

id
name
created_at
```

例如：

```text
Leica M6
Nikon FM2
Contax T2
Olympus OM-1
```

不做：

```text
序列号
购买价格
购买日期
状态
资产价值
维修记录
```

---

## 5.3 Lens

```text
lenses

id
name
created_at
```

例如：

```text
35mm F2
50mm F2
28mm F2.8
Summicron-M 35mm F2 ASPH.
```

仍然支持一卷绑定多个镜头。

关系：

```text
film_roll_lenses
```

```text
roll_id
lens_id
```

---

# 6. 器材库 `/library`

这是唯一管理：

```text
胶片
相机
镜头
```

的页面。

页面定位不是“器材管理”。

而是：

> 维护创建胶卷时可以快速选择的文字条目。

UI：

```text
器材库

在一个地方维护你已有的胶片、相机和镜头条目。


胶片                    + 添加胶片

Kodak Portra 400
Kodak Gold 200
Fujifilm C200
Ilford HP5+


相机                    + 添加相机

Leica M6
Nikon FM2
Contax T2


镜头                    + 添加镜头

35mm F2
50mm F2
28mm F2.8
```

每个条目最多只有：

```text
名称
...
```

点击 `...`：

```text
重命名
删除
```

底部可以统一提供：

```text
添加新的器材条目

类别
[ 胶片 ▼ ]

名称
[ Kodak Ektar 100 ]

[ 添加 ]
```

---

# 7. Development 冲洗记录

冲洗仍然是 Roll 的子对象。

```text
developments
```

字段：

```text
id
roll_id

method
lab_name
process

developer
temperature_c
development_time_sec

push_pull

developed_at

cost
currency

notes
```

不过前端默认只展示最常用字段：

```text
冲洗方式
冲洗店
冲洗工艺
日期
Push / Pull
备注
```

高级字段：

```text
药水
温度
时间
```

放在：

```text
更多信息
```

里。

---

# 8. Scan 扫描记录

```text
scans
```

字段：

```text
id
roll_id

method

lab_name
scanner_model

resolution_width
resolution_height

file_format

scanned_at

cost
currency

notes
```

常用 UI：

```text
扫描方式
扫描设备
扫描店
分辨率
扫描日期
备注
```

例如：

```text
Noritsu HS-1800
6048 × 4011
JPEG
```

---

# 9. Photo 模型

```text
roll_photos
```

字段：

```text
id

roll_id

frame_number

file_path
thumbnail_path

original_filename

width
height
file_size

caption

is_cover
is_favorite

sort_order

created_at
```

首版不做逐张曝光信息。

即暂时没有：

```text
f/2
1/250
焦距
测光
曝光补偿
```

V2 再增加。

---

# 10. 图片存储结构

推荐：

```text
uploads/
  rolls/
    000036/
      originals/
        uuid-01.jpg
        uuid-02.jpg
        uuid-03.jpg

      thumbnails/
        uuid-01.webp
        uuid-02.webp
        uuid-03.webp
```

图片上传后：

1. 检查 MIME。
2. 保存原图。
3. Pillow 修正 Orientation。
4. 获取宽高。
5. 生成 WebP Thumbnail。
6. 数据库创建 Photo。
7. 根据文件名生成初始顺序。
8. 用户可以重新排序。

---

# 11. 最重要的新视觉组件：Film Frame

新版 UI 中，“有孔片基”不是装饰性细节。

它应该成为整个产品最核心的视觉语言。

前端创建统一组件：

```text
<FilmFrame />
```

使用场景：

```text
首页 Roll Cover
Roll Hero
整卷总览
单张展示
```

---

# 12. FilmFrame 组件设计

建议纯 CSS 实现，不要给每张照片额外生成边框图片。

结构：

```text
FilmFrame
 ├── top film edge
 │    □ □ □ □ □ □
 │
 ├── image
 │
 └── bottom film edge
      □ □ □ □ □ □
```

视觉：

```text
┌─□─□─□─□─□─□─□─□─□─┐
│                     │
│        PHOTO        │
│                     │
└─□─□─□─□─□─□─□─□─□─┘
```

边框颜色：

```text
#151515
```

孔：

```text
cream / page background
```

顶部或底部可以增加极弱文字：

```text
KODAK PORTRA 400
36
36A
```

但不要过度模拟真实胶片。

重点是视觉辨识度，不是物理还原。

---

# 13. FilmFrame 实现方式

推荐：

```text
CSS background
+
repeating-linear-gradient
```

或：

```text
::before
::after
```

生成 sprocket holes。

不要：

```text
每张图使用 PNG frame
```

原因：

* 响应式困难
* 比例困难
* Retina 清晰度问题
* 主题不好调整

建议：

```text
FilmFrame
```

支持：

```text
variant="card"
variant="hero"
variant="thumbnail"
variant="photo"
```

---

# 14. 首页 `/`

首页就是：

```text
胶卷档案
```

不做传统 Dashboard。

结构：

```text
胶卷档案

用胶片，记录生活的温度。

[ 搜索胶卷、地点或关键词... ]  [+ 新增胶卷]


全部
拍摄中
已拍完
已冲扫
收藏
```

然后：

```text
3 columns desktop
2 columns tablet
1 column mobile
```

---

# 15. 首页 RollCard

每一卷：

```text
┌─□─□─□─□─□─□─□─────┐
│                    │
│      COVER         │
│                    │
└─□─□─□─□─□─□─□─────┘

ROLL 036

Kodak Portra 400

上海
Leica M6

2026.09
```

重点：

封面本身必须放在：

```text
FilmFrame
```

里面。

不是普通：

```text
rounded-lg image card
```

---

# 16. 首页视觉规则

不要大量圆角 Card。

摄影内容应该偏：

```text
直角
极小圆角
细边线
大留白
```

整体视觉：

```text
editorial
archive
contact sheet
darkroom
film strip
```

而不是：

```text
SaaS dashboard
```

---

# 17. Roll Detail `/rolls/[id]`

这是整个产品最核心的页面。

结构：

```text
返回

[ FILM HERO ]

ROLL 036
上海初秋

简介

基本信息

整卷总览

单张展示
```

---

# 18. Roll Hero

Hero 使用：

```text
FilmFrame variant="hero"
```

大尺寸：

```text
┌□ □ □ □ □ □ □ □ □ □ □ □┐
│                          │
│          HERO            │
│                          │
└□ □ □ □ □ □ □ □ □ □ □ □┘
```

下面：

```text
ROLL 036

上海初秋

2026.09
```

---

# 19. 基本信息

使用简单两列排版：

```text
胶片
Kodak Portra 400

相机
Leica M6

镜头
35mm F2

拍摄时间
2026.09.03 — 2026.09.07

地点
上海

拍摄 EI
200
```

然后：

```text
冲洗
C-41 / XXX Lab / 2026.09.08

扫描
Noritsu HS-1800 / 6048 × 4011
```

不要大量 Card。

尽量使用：

```text
label
value
divider
```

---

# 20. 整卷总览

这是新版最重要的功能之一。

标题：

```text
整卷总览

36 张照片
```

桌面端：

> 每行固定 6 张。

```text
01  02  03  04  05  06
07  08  09  10  11  12
13  14  15  16  17  18
19  20  21  22  23  24
25  26  27  28  29  30
31  32  33  34  35  36
```

CSS：

```text
grid-template-columns: repeat(6, minmax(0, 1fr));
```

---

# 21. 总览照片边框

每一张依然使用小型 FilmFrame。

```text
┌□ □ □ □┐
│  IMG   │
└□ □ □ □┘

01
```

这里不能使用首页那么厚的有孔片基。

使用：

```text
FilmFrame variant="thumbnail"
```

保持紧凑。

---

# 22. 响应式总览

桌面：

```text
6 columns
```

Tablet：

```text
4 columns
```

Mobile：

```text
2 columns
```

用户要求的：

> 每行 6 张

作为桌面设计标准。

---

# 23. 单张展示

整卷总览下面必须存在：

```text
单张展示
```

每张照片单独展示。

例如：

```text
01

┌□ □ □ □ □ □ □ □ □ □┐
│                     │
│                     │
│        PHOTO        │
│                     │
│                     │
└□ □ □ □ □ □ □ □ □ □┘

上海
2026.09.03
```

然后：

```text
02

[ PHOTO ]
```

继续向下。

这是一个完整摄影项目页面。

---

# 24. 单张展示图片尺寸

照片不能强制统一比例。

支持：

```text
3:2
4:3
1:1
portrait
landscape
panorama
```

因此：

```text
FilmFrame
```

必须跟随图片 intrinsic aspect ratio。

不要：

```text
object-cover + 固定 16:9
```

除首页 Cover 外。

---

# 25. 点击总览照片

点击：

```text
Frame 12
```

建议：

平滑滚动到：

```text
#photo-12
```

对应下面的：

```text
单张展示 12
```

而不是第一版就做独立照片路由。

例如：

```text
/rolls/36#photo-12
```

这样简单很多。

---

# 26. 新增胶卷

URL：

```text
/rolls/new
```

首屏只填拍摄阶段已知的信息。

```text
胶片 *
[ Kodak Portra 400 ▼ ]

相机 *
[ Leica M6 ▼ ]

镜头
[ 35mm F2 × ]

拍摄 EI
[ 200 ]

开始日期
[ 2026-09-03 ]

地点
[ 上海 ]

标题
[ 上海初秋 ]

备注
[ ... ]

预计张数
[ 36 ]
```

按钮：

```text
保存草稿

创建胶卷
```

---

# 27. 新建器材条目

如果创建 Roll 时发现：

```text
没有 Leica M6
```

下拉菜单最后可以：

```text
+ 新增相机
```

点击弹出小 Dialog：

```text
新增相机

名称
[ Leica M6 ]

[取消] [添加]
```

同样适用于：

```text
胶片
镜头
```

添加成功后自动选中。

这能避免用户必须先去器材库。

---

# 28. Roll 生命周期

创建：

```text
拍摄中
```

结束拍摄：

```text
已拍完
```

增加冲洗信息：

```text
已冲洗
```

上传照片 / 添加 Scan：

```text
已扫描
```

最终：

```text
已归档
```

UI 可以：

```text
拍摄中
  ↓
已拍完
  ↓
已冲洗
  ↓
已扫描
```

但不要做复杂工作流引擎。

---

# 29. 图片批量上传

Roll Detail 编辑模式：

```text
上传照片

拖动照片到这里

或者

[选择照片]
```

支持：

```text
一次 36–40 张
```

必须显示：

```text
Uploading 12 / 36
```

上传完：

```text
[01]
[02]
[03]
...
```

支持拖动排序。

---

# 30. Frame Number

默认根据照片排序：

```text
01
02
03
...
36
```

而不是依赖文件名。

数据库：

```text
sort_order
frame_number
```

例如文件名：

```text
IMG_8292.jpg
```

也没关系。

---

# 31. 设置封面

在照片管理里：

```text
...
设为封面
收藏
删除
```

Cover 主要用于：

```text
首页 RollCard
详情 Hero
```

如果没有 Cover：

默认第一张。

---

# 32. 首页搜索

搜索范围：

```text
Roll title

Film stock

Camera

Lens

Location

Notes
```

比如：

```text
Portra
上海
Leica
东京
```

---

# 33. 首页筛选

第一版：

```text
全部
拍摄中
已拍完
已冲扫
收藏
```

以及：

```text
年份
```

不需要复杂高级筛选。

---

# 34. Stats

Stats 只关注摄影记录。

例如：

```text
胶卷总数

总照片数

今年拍摄胶卷

最常使用胶片

最常使用相机

最常使用镜头
```

图表：

```text
Rolls by Month

Film usage

Camera usage
```

不做：

```text
资产价值
器材价值
购买成本统计
```

---

# 35. 前端结构

```text
frontend/src/

app/
  page.tsx

  rolls/
    new/
      page.tsx

    [id]/
      page.tsx

      edit/
        page.tsx

  library/
    page.tsx

  stats/
    page.tsx

  settings/
    page.tsx


components/

  film/
    FilmFrame.tsx
    FilmStripLabel.tsx

  roll/
    RollCard.tsx
    RollGrid.tsx
    RollHero.tsx
    RollMetadata.tsx
    RollContactSheet.tsx
    RollPhotoFeed.tsx

  photo/
    PhotoUpload.tsx
    PhotoSorter.tsx
    PhotoItem.tsx

  library/
    LibrarySection.tsx
    LibraryItem.tsx
    AddLibraryItem.tsx

  layout/
    Header.tsx

lib/
  api.ts

types/
```

---

# 36. 后端结构

```text
backend/app/

main.py
database.py

models/
  film_roll.py
  library.py
  development.py
  scan.py
  photo.py

schemas/
  film_roll.py
  library.py
  development.py
  scan.py
  photo.py

routers/
  rolls.py
  library.py
  developments.py
  scans.py
  photos.py
  stats.py

services/
  image_service.py
  storage_service.py
```

---

# 37. API

Roll：

```text
GET    /api/rolls
POST   /api/rolls

GET    /api/rolls/{id}
PUT    /api/rolls/{id}
DELETE /api/rolls/{id}
```

---

Library：

```text
GET /api/library
```

返回：

```json
{
  "films": [],
  "cameras": [],
  "lenses": []
}
```

新增：

```text
POST /api/library/films
POST /api/library/cameras
POST /api/library/lenses
```

编辑：

```text
PUT /api/library/films/{id}
PUT /api/library/cameras/{id}
PUT /api/library/lenses/{id}
```

删除：

```text
DELETE /api/library/films/{id}
DELETE /api/library/cameras/{id}
DELETE /api/library/lenses/{id}
```

---

Photos：

```text
GET
/api/rolls/{id}/photos

POST
/api/rolls/{id}/photos

PUT
/api/photos/{id}

DELETE
/api/photos/{id}
```

排序：

```text
PUT /api/rolls/{id}/photos/reorder
```

Cover：

```text
PUT /api/rolls/{id}/cover/{photo_id}
```

---

# 38. 开发任务拆分

## Task 0

项目初始化

完成：

```text
frontend
backend
docker
.env
health endpoint
```

验收：

```text
Frontend 能启动

GET /api/health
→ 200
```

---

# Task 1

数据库基础模型

实现：

```text
FilmRoll

FilmStock
Camera
Lens

FilmRollLens
```

注意：

```text
FilmStock
Camera
Lens
```

只有：

```text
id
name
created_at
```

禁止添加资产管理字段。

---

# Task 2

器材库 API

实现：

```text
GET /api/library

POST /library/*
PUT /library/*
DELETE /library/*
```

验收：

可以：

```text
新增 Kodak Portra 400
新增 Leica M6
新增 35mm F2
```

---

# Task 3

器材库 UI

实现：

```text
/library
```

三个区块：

```text
胶片
相机
镜头
```

全部为文字条目。

可以：

```text
新增
重命名
删除
```

完成后：

创建 Roll 的下拉选项可以直接使用。

---

# Task 4

FilmRoll CRUD

实现：

```text
POST /rolls

GET /rolls

GET /rolls/{id}

PUT /rolls/{id}

DELETE /rolls/{id}
```

完成：

```text
/rolls/new
```

---

# Task 5

首页 Roll Archive

实现：

```text
/
```

包含：

```text
RollGrid

RollCard

搜索

状态筛选
```

这一阶段先普通图片。

---

# Task 6

FilmFrame Component

实现整个项目最重要的视觉组件：

```text
FilmFrame
```

variant：

```text
card
hero
thumbnail
photo
```

必须使用：

```text
CSS
```

生成有孔片基。

禁止使用：

```text
静态 PNG 边框
```

验收：

不同图片比例不会破坏边框。

---

# Task 7

首页 Film UI

RollCard 改造为：

```text
FilmFrame
+
metadata
```

实现设计稿首页。

桌面：

```text
3 columns
```

---

# Task 8

Development + Scan

完成：

```text
developments
scans
```

CRUD + Roll Detail 编辑能力。

---

# Task 9

Photo Upload Pipeline

完成：

```text
批量上传

图片存储

thumbnail

metadata

删除
```

验收：

一次上传：

```text
40 JPEG
```

不报错。

---

# Task 10

照片排序

实现：

```text
drag and drop
```

保存：

```text
sort_order
```

自动维护：

```text
frame_number
```

---

# Task 11

Roll Contact Sheet

实现：

```text
RollContactSheet
```

桌面：

```text
repeat(6, 1fr)
```

显示：

```text
01–36
```

每张：

```text
FilmFrame variant="thumbnail"
```

验收：

36 张：

```text
6 × 6
```

---

# Task 12

Roll Photo Feed

实现：

```text
单张展示
```

按 Frame 顺序：

```text
01
PHOTO

02
PHOTO

03
PHOTO
```

图片：

```text
FilmFrame variant="photo"
```

保持原比例。

---

# Task 13

Contact Sheet Anchor Navigation

点击：

```text
Frame 12
```

滚动到：

```text
#photo-12
```

不新建照片详情路由。

---

# Task 14

Roll Detail UI

最终组合：

```text
Hero

Title

Metadata

Development

Scan

Contact Sheet

Photo Feed
```

完成整个核心体验。

---

# Task 15

Roll Lifecycle

实现：

```text
拍摄中
已拍完
已冲洗
已扫描
已归档
```

根据用户操作更新。

---

# Task 16

Stats

实现：

```text
总胶卷
总照片

按月份
按胶片
按相机
按镜头
```

---

# Task 17

Responsive

重点：

首页：

```text
Desktop 3 columns
Tablet 2
Mobile 1
```

Contact Sheet：

```text
Desktop 6
Tablet 4
Mobile 2
```

单张展示：

Mobile：

```text
100% width
```

---

# Task 18

Docker / Deployment

复用 CameraHub 的技术路线：

```text
Docker

Docker Compose

GHCR

SQLite persistence

uploads persistence
```

Volumes：

```text
/data
/uploads
/backups
```

---

# Task 19

Backup / Restore

备份：

```text
SQLite

uploads
```

打包：

```text
backup-YYYYMMDD-HHMM.zip
```

恢复时：

```text
数据库
+
图片
```

必须同步恢复。

---

# 39. MVP 验收标准

V1 完成时必须可以完成完整流程：

第一步：

```text
器材库
```

添加：

```text
Kodak Portra 400
Leica M6
35mm F2
```

第二步：

创建：

```text
ROLL 036
```

填写：

```text
Portra 400
Leica M6
35mm F2
EI 200
上海
```

第三步：

拍完以后添加：

```text
结束日期
```

第四步：

添加：

```text
冲洗
扫描
```

第五步：

上传：

```text
36 张照片
```

第六步：

首页：

以：

```text
有孔片基 RollCard
```

显示这一卷。

第七步：

进入详情：

看到：

```text
Film Hero

胶片信息

冲洗

扫描

6 张 / 行 Contact Sheet

全部单张照片展示
```

这就是 V1 完成。

---

# 40. 明确不做

V1 不做：

```text
器材资产管理

库存

胶卷库存

价格管理

相机购买记录

镜头价格

维修

用户注册

多人账户

社交

评论

点赞

地图

天气

AI

照片识别

逐张曝光参数

RAW

在线修图

胶片模拟

扫描反相

OCR

手机 App
```

---

# 41. 产品设计原则

第一：

```text
Roll > Gear
```

整个系统围绕：

```text
一卷胶片
```

而不是器材。

第二：

```text
Archive > Dashboard
```

首页首先是摄影档案。

第三：

```text
Photo Presentation > Admin UI
```

Roll Detail 应该像摄影作品页。

第四：

```text
FilmFrame
```

是整个产品的视觉识别。

第五：

```text
Contact Sheet + Photo Feed
```

是详情页两个不可删除的核心模块。

最终页面核心关系：

```text
胶卷档案
    │
    ├── Roll Card
    │      └── Film Border
    │
    └── Roll Detail
           │
           ├── Hero
           │     └── Film Border
           │
           ├── Metadata
           │
           ├── 整卷总览
           │     └── 6 Photos / Row
           │
           └── 单张展示
                 └── Film Border
```
