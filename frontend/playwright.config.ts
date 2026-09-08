import {defineConfig, devices} from '@playwright/test';
import path from 'node:path';
export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1, timeout: 180_000,
  expect: {timeout: 15_000}, retries: 0,
  reporter: [['list'], ['html', {open: 'never'}]],
  use: {baseURL: 'http://127.0.0.1:3000', trace: 'retain-on-failure', screenshot: 'only-on-failure'},
  projects: [{name: 'chromium', use: {...devices['Desktop Chrome'], viewport: {width: 1440, height: 1000}}}],
  webServer: [
    {command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000', cwd: '../backend', url: 'http://127.0.0.1:8000/api/health', reuseExistingServer: false, env: {DATA_DIR: path.resolve('../backend/var/e2e/data'), UPLOADS_DIR: path.resolve('../backend/var/e2e/uploads'), BACKUPS_DIR: path.resolve('../backend/var/e2e/backups')}},
    {command: 'npm run start -- --hostname 127.0.0.1', url: 'http://127.0.0.1:3000', reuseExistingServer: false},
  ],
});
