import {test, expect, Page} from '@playwright/test';
import {deflateSync} from 'node:zlib';

function png(width: number, height: number) {
  function crc(bytes: Buffer) {let value = 0xffffffff; for (const byte of bytes) {value ^= byte; for (let bit = 0; bit < 8; bit++) value = (value >>> 1) ^ ((value & 1) ? 0xedb88320 : 0);} return (value ^ 0xffffffff) >>> 0;}
  function chunk(name: string, content: Buffer) {const type = Buffer.from(name), length = Buffer.alloc(4), checksum = Buffer.alloc(4); length.writeUInt32BE(content.length); checksum.writeUInt32BE(crc(Buffer.concat([type, content]))); return Buffer.concat([length, type, content, checksum]);}
  const header = Buffer.alloc(13); header.writeUInt32BE(width); header.writeUInt32BE(height, 4); header[8] = 8; header[9] = 2;
  const data = Buffer.alloc(height * (1 + width * 3));
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {const i = y * (1 + width * 3) + 1 + x * 3; data[i] = 50 + x % 130; data[i + 1] = 80 + y % 100; data[i + 2] = 100;}
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk('IHDR', header), chunk('IDAT', deflateSync(data)), chunk('IEND', Buffer.alloc(0))]);
}
async function addItem(page: Page, kind: string, name: string) {
  await page.getByRole('button', {name: `添加${kind}`, exact: false}).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('名称', {exact: true}).fill(name);
  await dialog.getByRole('button', {name: '添加', exact: true}).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByText(name, {exact: true})).toBeVisible();
}

test('完整胶卷流程、照片比例、响应式、备份与恢复', async ({page}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', {name: '从第一卷开始，留住光阴'})).toBeVisible();
  await page.getByRole('link', {name: '器材库', exact: true}).click();
  await addItem(page, '胶片', 'Kodak Portra 400');
  await addItem(page, '相机', 'Leica M6');
  await addItem(page, '镜头', '35mm F2');
  await page.goto('/rolls/new');
  await page.getByLabel('胶片 *', {exact: true}).selectOption({label: 'Kodak Portra 400'});
  await page.getByLabel('相机 *', {exact: true}).selectOption({label: 'Leica M6'});
  await page.getByLabel('35mm F2', {exact: true}).check();
  await page.getByLabel('拍摄 EI', {exact: true}).fill('200');
  await page.getByLabel('开始日期', {exact: true}).fill('2026-09-03');
  await page.getByLabel('地点', {exact: true}).fill('上海');
  await page.getByLabel('标题', {exact: true}).fill('上海初秋');
  await page.getByText('更多信息 · 自定义胶卷编号').click();
  await page.getByLabel('胶卷编号', {exact: true}).fill('36');
  await page.getByRole('button', {name: '保存草稿'}).click();
  await page.reload();
  await expect(page.getByLabel('标题', {exact: true})).toHaveValue('上海初秋');
  await page.getByRole('button', {name: '创建胶卷 →'}).click();
  await expect(page).toHaveURL(/\/rolls\/\d+$/);
  const rollUrl = page.url();
  await page.getByRole('link', {name: '编辑胶卷 ↗'}).click();
  await page.getByLabel('结束日期', {exact: true}).fill('2026-09-07');
  await page.getByRole('button', {name: '保存修改'}).click();
  await expect(page.locator('.roll-progress')).toContainText('已拍完');
  const development = page.locator('.process-grid > section').nth(0);
  await development.getByRole('button', {name: '添加记录', exact: false}).click();
  await page.getByLabel('冲洗工艺', {exact: true}).fill('C-41');
  await page.getByLabel('冲洗店', {exact: true}).fill('Film Lab');
  await page.getByRole('button', {name: '保存记录'}).click();
  await expect(page.locator('.roll-progress')).toContainText('已冲洗');
  await page.locator('.process-grid > section').nth(1).getByRole('button', {name: '添加记录', exact: false}).click();
  await page.getByLabel('扫描设备', {exact: true}).fill('Noritsu HS-1800');
  await page.getByLabel('分辨率 · 宽', {exact: true}).fill('6048');
  await page.getByLabel('分辨率 · 高', {exact: true}).fill('4011');
  await page.getByRole('button', {name: '保存记录'}).click();
  await expect(page.locator('.roll-progress')).toContainText('已扫描');
  await page.getByRole('button', {name: '上传 / 管理照片', exact: false}).click();
  const files = Array.from({length: 36}, (_, i) => ({name: `frame-${i + 1}.png`, mimeType: 'image/png', buffer: i === 1 ? png(80, 120) : i === 2 ? png(240, 60) : png(120, 80)}));
  await page.locator('#photo-files').setInputFiles(files);
  await expect(page.getByRole('status')).toContainText('已上传 36 / 36', {timeout: 120_000});
  await expect(page.locator('.contact-photo')).toHaveCount(36);
  await expect(page.locator('.feed-photo')).toHaveCount(36);
  await page.locator('.sort-item').nth(1).getByRole('button', {name: '设封面', exact: true}).click();
  await expect(page.locator('.sort-item').nth(1).locator('.sort-heading')).toContainText('封面');
  await page.locator('.sort-item').nth(1).getByRole('button', {name: '收藏', exact: true}).click();
  await expect(page.locator('.sort-item').nth(1).getByRole('button', {name: '取消收藏'})).toBeVisible();
  await page.getByRole('button', {name: '前移第 2 张', exact: true}).click();
  await expect(page.locator('.sort-item').first().locator('.file-name')).toHaveText('frame-2.png');
  await page.getByRole('button', {name: '收起照片管理'}).click();
  await page.getByRole('link', {name: '查看第 12 张照片', exact: true}).click();
  await expect(page).toHaveURL(/#photo-12$/);
  await expect(page.locator('#photo-12')).toBeInViewport();
  for (const [width, columns] of [[1440, 6], [900, 4], [390, 2]]) {
    await page.setViewportSize({width, height: 1000});
    await expect.poll(() => page.locator('.contact-sheet').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(columns);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const photo = page.locator('.feed-photo').first().locator('img');
    await photo.scrollIntoViewIfNeeded();
    await expect(photo).toBeVisible();
    await expect.poll(() => photo.evaluate(el => el instanceof HTMLImageElement && el.complete && el.naturalWidth > 0)).toBe(true);
    expect(await photo.evaluate(el => {
      if (!(el instanceof HTMLImageElement)) throw new Error('单张展示应包含图片元素');
      return Math.abs(el.width / el.height - el.naturalWidth / el.naturalHeight);
    })).toBeLessThan(0.02);
  }
  await page.screenshot({path: testInfo.outputPath('roll-mobile.png'), fullPage: true});
  await page.setViewportSize({width: 1440, height: 1000});
  await page.goto('/');
  await page.getByRole('button', {name: '收藏', exact: true}).click();
  await expect(page.locator('.roll-card')).toHaveCount(1);
  await page.getByRole('searchbox', {name: '搜索胶卷'}).fill('35mm');
  await expect(page.locator('.roll-card')).toHaveCount(1);
  await page.screenshot({path: testInfo.outputPath('archive-desktop.png'), fullPage: true});
  await page.goto('/stats');
  await expect(page.locator('.stat-totals')).toContainText('36');
  await page.goto('/settings');
  await page.getByRole('button', {name: '生成完整备份', exact: false}).click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', {name: '下载', exact: true}).first().click();
  const download = await downloadPromise, backupPath = testInfo.outputPath('backup.zip');
  await download.saveAs(backupPath);
  await page.goto(rollUrl);
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', {name: '删除这一卷'}).click();
  await expect(page).toHaveURL('http://127.0.0.1:3000/');
  await page.goto('/settings');
  await page.getByLabel('选择备份文件', {exact: true}).setInputFiles(backupPath);
  await page.getByLabel('我了解当前档案将被替换').check();
  await page.getByRole('button', {name: '确认恢复', exact: true}).click();
  await expect(page.locator('.notice[role="status"]')).toContainText('档案和照片已同步恢复');
  await page.goto(rollUrl);
  await expect(page.locator('.contact-photo')).toHaveCount(36);
  expect(errors).toEqual([]);
});

test('新建页即时添加器材、取消操作、网络错误可重试', async ({page}) => {
  await page.goto('/rolls/new');
  await page.getByLabel('胶片 *', {exact: true}).selectOption('__new');
  await page.getByRole('dialog').getByLabel('名称').fill('Ilford HP5+');
  await page.getByRole('dialog').getByRole('button', {name: '添加', exact: true}).click();
  await expect(page.getByLabel('胶片 *', {exact: true}).locator('option:checked')).toHaveText('Ilford HP5+');
  await page.getByLabel('相机 *', {exact: true}).selectOption('__new');
  await page.getByRole('dialog').getByRole('button', {name: '取消', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.route('**/api/rolls?**', route => route.abort());
  await page.goto('/');
  await expect(page.getByRole('alert')).toContainText('暂时无法连接档案');
  await page.unroute('**/api/rolls?**');
  await page.getByRole('button', {name: '重试', exact: true}).click();
  await expect(page.locator('.roll-card')).toHaveCount(1);
});
