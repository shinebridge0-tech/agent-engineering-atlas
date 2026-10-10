import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'e2e',use:{baseURL:'http://127.0.0.1:18765',browserName:'chromium'},workers:1,reporter:'list',outputDir:'../.local/playwright-results'});
