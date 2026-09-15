/**
 * TalentMail 全套 UI 无头回归
 * 用法: LOGIN_USER=... LOGIN_PASS=... node ui-suite.js
 */
const { chromium } = require('playwright-core');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:13000';
const USER = process.env.LOGIN_USER;
const PASS = process.env.LOGIN_PASS;

const results = [];
const ok = (name, extra = '') => { results.push({ name, ok: true, extra }); console.log('PASS', name, extra); };
const fail = (name, extra = '') => { results.push({ name, ok: false, extra }); console.log('FAIL', name, extra); };

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1000);
  await page.locator('input:not([type=password]):not([type=hidden])').first().fill(USER);
  await page.locator('input[type=password]').first().fill(PASS);
  await page.locator('button').filter({ hasText: /登录/ }).first().click();
  await page.waitForURL(u => !String(u).includes('/login'), { timeout: 30000 });
  await page.waitForTimeout(800);
}

async function run() {
  if (!USER || !PASS) throw new Error('need LOGIN_USER LOGIN_PASS');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage();
  const pageErrors = [];
  page.on('pageerror', e => {
    const s = String(e);
    if (!s.includes('WebSocket')) pageErrors.push(s);
  });

  // 0. public developers page no auth
  await page.goto(`${BASE}/developers`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);
  const devText = await page.locator('body').innerText();
  if (devText.includes('开发者门户') || devText.includes('Developer Portal')) ok('developers-public');
  else fail('developers-public', devText.slice(0, 120));

  await login(page);
  ok('login');

  const routes = [
    { path: '/', name: 'mail-home', expect: /收件箱|写邮件|Mail/ },
    { path: '/contacts', name: 'contacts', expect: /通讯录|Contacts|新建/ },
    { path: '/drive', name: 'drive', expect: /云盘|Drive|上传/ },
    { path: '/calendar', name: 'calendar-month', expect: /日历|Calendar|月/ },
    { path: '/pool', name: 'pool', expect: /账号池|Temp|创建/ },
    { path: '/settings', name: 'settings', expect: /设置|Settings|账号/ },
    { path: '/workflows', name: 'workflows', expect: /工作流|Workflow/ },
  ];

  for (const r of routes) {
    try {
      await page.goto(BASE + r.path, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(1500);
      const text = await page.locator('main, body').first().innerText();
      if (r.expect.test(text) && text.length > 80) ok(r.name, `len=${text.length}`);
      else fail(r.name, `len=${text.length} snip=${text.slice(0, 80).replace(/\n/g, ' ')}`);
    } catch (e) {
      fail(r.name, String(e).slice(0, 120));
    }
  }

  // calendar week view (regression)
  try {
    await page.goto(`${BASE}/calendar`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    await page.locator('button', { hasText: /^周$/ }).first().click();
    await page.waitForTimeout(1200);
    const t = await page.locator('main, body').first().innerText();
    const hasGrid = await page.locator('.grid-cols-7').count();
    if (t.includes('–') && hasGrid > 0 && t.length > 100) ok('calendar-week', `grid=${hasGrid}`);
    else fail('calendar-week', `len=${t.length} grid=${hasGrid}`);
  } catch (e) {
    fail('calendar-week', String(e).slice(0, 120));
  }

  // settings tabs
  try {
    await page.goto(`${BASE}/settings`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const tabNames = ['账号信息', '外观主题', '登录与安全', 'API 密钥', '系统工作流'];
    let hit = 0;
    for (const name of tabNames) {
      const btn = page.locator('button', { hasText: name }).first();
      if (await btn.count()) {
        await btn.click();
        await page.waitForTimeout(700);
        const body = await page.locator('main, body').first().innerText();
        if (body.length > 100) hit++;
      }
    }
    if (hit >= 4) ok('settings-tabs', `hit=${hit}`);
    else fail('settings-tabs', `hit=${hit}`);
  } catch (e) {
    fail('settings-tabs', String(e).slice(0, 120));
  }

  // compose panel open
  try {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const compose = page.locator('button', { hasText: /写邮件|Compose/ }).first();
    await compose.click();
    await page.waitForTimeout(1000);
    const body = await page.locator('body').innerText();
    if (/发送|Send|主题|Subject|收件人|To/.test(body)) ok('compose-open');
    else fail('compose-open', body.slice(0, 100).replace(/\n/g, ' '));
  } catch (e) {
    fail('compose-open', String(e).slice(0, 120));
  }

  // week/month toggle both ways
  try {
    await page.goto(`${BASE}/calendar`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    await page.locator('button', { hasText: /^周$/ }).first().click();
    await page.waitForTimeout(800);
    await page.locator('button', { hasText: /^月$/ }).first().click();
    await page.waitForTimeout(800);
    const t = await page.locator('main, body').first().innerText();
    if (t.length > 100) ok('calendar-toggle');
    else fail('calendar-toggle', 'empty');
  } catch (e) {
    fail('calendar-toggle', String(e).slice(0, 120));
  }

  // sidebar add buttons full width
  try {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    const widths = await page.evaluate(() => {
      const pick = (label) => {
        const btn = Array.from(document.querySelectorAll('button,a')).find(el => el.textContent.trim().includes(label));
        return btn ? Math.round(btn.getBoundingClientRect().width) : 0;
      };
      return { addTag: pick('添加标签'), addExt: pick('添加其他邮箱'), inbox: pick('收件箱') };
    });
    if (widths.addTag > 200 && widths.addExt > 200) ok('sidebar-hit', JSON.stringify(widths));
    else fail('sidebar-hit', JSON.stringify(widths));
  } catch (e) {
    fail('sidebar-hit', String(e).slice(0, 120));
  }

  // attach profile SSO card
  try {
    await page.goto(`${BASE}/settings`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);
    const profile = page.locator('button', { hasText: '账号信息' }).first();
    if (await profile.count()) { await profile.click(); await page.waitForTimeout(800); }
    const body = await page.locator('main, body').first().innerText();
    if (/认证中心|Auth Center|关联/.test(body)) ok('profile-sso-card');
    else fail('profile-sso-card', body.slice(0, 100).replace(/\n/g, ' '));
  } catch (e) {
    fail('profile-sso-card', String(e).slice(0, 120));
  }

  // app passwords section
  try {
    const sec = page.locator('button', { hasText: '登录与安全' }).first();
    if (await sec.count()) { await sec.click(); await page.waitForTimeout(900); }
    const body = await page.locator('main, body').first().innerText();
    if (/应用专用密码|App Password/.test(body)) ok('app-passwords-ui');
    else fail('app-passwords-ui', body.slice(0, 100).replace(/\n/g, ' '));
  } catch (e) {
    fail('app-passwords-ui', String(e).slice(0, 120));
  }

  const uncaught = pageErrors.filter(e => !/ResizeObserver|Loading chunk/.test(e));
  if (uncaught.length === 0) ok('no-pageerror');
  else fail('no-pageerror', uncaught.slice(0, 3).join(' | ').slice(0, 200));

  const passed = results.filter(r => r.ok).length;
  const failed = results.filter(r => !r.ok).length;
  console.log('\n=== SUMMARY ===');
  console.log(`passed=${passed} failed=${failed} total=${results.length}`);
  for (const r of results.filter(x => !x.ok)) console.log('  FAIL:', r.name, r.extra);
  await browser.close();
  process.exit(failed ? 1 : 0);
}

run().catch(e => { console.error('FATAL', e); process.exit(2); });
