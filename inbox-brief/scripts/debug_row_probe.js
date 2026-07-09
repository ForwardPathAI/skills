#!/usr/bin/env node
// Debug helper: dump the DOM structure of the first few inbox list rows so
// selector heuristics in fetch_emails.js can be grounded on the real OWA
// markup (which varies by locale and A/B ring).

'use strict';

const path = require('path');
const { chromium } = require('playwright');

const SKILL_DIR = path.resolve(__dirname, '..');

(async () => {
  const ctx = await chromium.launchPersistentContext(
    path.join(SKILL_DIR, '.browser-profile'),
    { headless: true, viewport: { width: 1600, height: 1000 }, args: ['--disable-blink-features=AutomationControlled'] },
  );
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto('https://outlook.office.com/mail/inbox/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);

  const info = await page.evaluate(() => {
    const box = document.querySelector('[data-app-section="MessageList"] [role="listbox"]')
      || document.querySelector('[role="listbox"]');
    if (!box) return { error: 'no listbox' };
    const rows = Array.from(box.querySelectorAll('[role="option"]')).slice(0, 4);
    return rows.map((r) => ({
      id: r.id,
      aria: r.getAttribute('aria-label'),
      dataConvId: r.getAttribute('data-convid'),
      attrs: Array.from(r.attributes).map((a) => `${a.name}=${a.value.slice(0, 60)}`),
      titles: Array.from(r.querySelectorAll('[title]')).map((el) => ({
        tag: el.tagName, title: el.getAttribute('title')?.slice(0, 100), text: el.textContent?.slice(0, 60),
      })),
      spans: Array.from(r.querySelectorAll('span')).slice(0, 25).map((s) => ({
        cls: (s.className || '').toString().slice(0, 40), text: (s.textContent || '').slice(0, 70),
      })),
      innerTextLines: (r.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean),
    }));
  });

  console.log(JSON.stringify(info, null, 2));
  await ctx.close();
})();
