#!/usr/bin/env node
// Browser-based Outlook Web inbox scraper (read-only).
//
// Opens a persistent Chromium profile, navigates to the Outlook Web inbox
// (or a search-results view when --query is given), scrolls the virtualized
// message list back far enough to cover --hours-back, filters out noise rows
// (GitHub / automated senders, per filters.json), then opens each remaining
// conversation in the reading pane and extracts its messages.
//
// Grounded on real OWA DOM (see debug_row_probe.js):
//   - each list row is [role="option"] with a stable data-convid attribute
//   - the sender's email lives in a span[title="<email>"] inside the row
//   - the row time span's title holds a FULL date, locale-formatted
//     (e.g. "Mié 8 Jul 2026 19:52" in Spanish) — parsed for both es/en
//   - unread rows have aria-label starting "No leído" / "Unread"
//
// Output: JSON array of conversation objects on stdout:
//   {
//     convId       : Outlook conversation id (stable row key)
//     subject      : row subject
//     rowSender    : sender display name(s) from the list row
//     senderEmails : email addresses found in the row (usually the sender)
//     rowTimeIso   : parsed ISO timestamp or null
//     preview      : row preview snippet
//     isUnread     : from row aria-label
//     participants : email addresses spotted in the opened conversation
//     messages     : [ { author, authorEmail, time, body } ] best-effort
//     paneText     : full innerText of the reading pane (authoritative
//                    fallback — always present, capped)
//   }
//
// Only the Inbox is scraped, so Junk is excluded by construction.
//
// Usage:
//   node fetch_emails.js --hours-back 24 [--query "acosta outage"]
//     [--profile-dir <path>] [--timeout-ms 60000] [--max 25]
//     [--headed] [--debug] [--no-filter]
//
// Exit codes: 0 ok · 1 usage · 2 not logged in · 3 navigation/scrape error

'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const SKILL_DIR = path.resolve(__dirname, '..');
const BODY_CAP = 15000;
const PANE_CAP = 40000;

function log(...args) { console.error('[fetch-emails]', ...args); }
function die(code, msg) { log(msg); process.exit(code); }

function parseArgs(argv) {
  const out = {
    hoursBack: 24,
    query: null,
    profileDir: path.join(SKILL_DIR, '.browser-profile'),
    timeoutMs: 60000,
    max: 25,
    headless: true,
    debug: false,
    filter: true,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    switch (a) {
      case '--hours-back':  out.hoursBack = Number(next()); break;
      case '--query':       out.query = next(); break;
      case '--profile-dir': out.profileDir = next(); break;
      case '--timeout-ms':  out.timeoutMs = Number(next()); break;
      case '--max':         out.max = Number(next()); break;
      case '--headed':      out.headless = false; break;
      case '--debug':       out.debug = true; break;
      case '--no-filter':   out.filter = false; break;
      default: die(1, `unknown argument: ${a}`);
    }
  }
  return out;
}

function loadFilters() {
  const p = path.join(SKILL_DIR, 'filters.json');
  const empty = { names: [], emails: [], subjects: [] };
  if (!fs.existsSync(p)) return empty;
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
    return {
      names: (raw.excludeRowSenderNames || []).map((s) => s.toLowerCase()),
      emails: (raw.excludeSenderEmailPatterns || []).map((s) => new RegExp(s, 'i')),
      subjects: (raw.excludeSubjectPatterns || []).map((s) => new RegExp(s, 'i')),
    };
  } catch (e) {
    log(`WARN: could not parse filters.json (${e.message}); running unfiltered`);
    return empty;
  }
}

// Month abbreviations, English + Spanish (OWA localizes the date titles).
const MONTHS = {
  jan: 0, ene: 0, feb: 1, mar: 2, apr: 3, abr: 3, may: 4, jun: 5, jul: 6,
  aug: 7, ago: 7, sep: 8, oct: 9, nov: 10, dic: 11, dec: 11,
};

// Parse the FULL date from the row time span's title, e.g.:
//   "Mié 8 Jul 2026 19:52"  ·  "Wed 7/8/2026 7:52 PM"  ·  "8 Jul 2026 19:52"
function parseFullDate(text) {
  if (!text) return null;
  const t = text.trim();

  // "<dow>? d Mon yyyy hh:mm" (es/en month names)
  let m = t.match(/(\d{1,2})\s+([A-Za-zÀ-ÿ]{3,})\.?\s+(\d{4})(?:\s+(\d{1,2}):(\d{2})\s*(AM|PM)?)?/i);
  if (m) {
    const mon = MONTHS[m[2].slice(0, 3).toLowerCase()];
    if (mon !== undefined) {
      let h = m[4] ? parseInt(m[4], 10) : 12;
      if (m[6]) {
        if (/pm/i.test(m[6]) && h !== 12) h += 12;
        if (/am/i.test(m[6]) && h === 12) h = 0;
      }
      return new Date(Number(m[3]), mon, Number(m[1]), h, m[5] ? parseInt(m[5], 10) : 0, 0, 0);
    }
  }

  // "M/D/YYYY h:mm AM" style
  m = t.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2})\s*(AM|PM)?)?/);
  if (m) {
    let h = m[4] ? parseInt(m[4], 10) : 12;
    if (m[6]) {
      if (/pm/i.test(m[6]) && h !== 12) h += 12;
      if (/am/i.test(m[6]) && h === 12) h = 0;
    }
    return new Date(Number(m[3]), Number(m[1]) - 1, Number(m[2]), h, m[5] ? parseInt(m[5], 10) : 0, 0, 0);
  }

  const parsed = Date.parse(t);
  if (!isNaN(parsed)) return new Date(parsed);
  return null;
}

async function findListbox(page, timeoutMs) {
  const candidates = [
    '[data-app-section="MessageList"] [role="listbox"]',
    '[role="listbox"][aria-label*="essage" i]',
    '[data-app-section="ConversationContainer"] [role="listbox"]',
    '[role="listbox"]',
  ];
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const sel of candidates) {
      const loc = page.locator(sel).first();
      if (await loc.count() > 0 && await loc.isVisible().catch(() => false)) {
        // Also require at least one rendered row so scraping can start.
        if (await page.locator(`${sel} [role="option"]`).count() > 0) return sel;
      }
    }
    await page.waitForTimeout(1000);
  }
  return null;
}

// Read the currently rendered rows out of the virtualized list.
// Grounded on the probed DOM: data-convid key, span[title] carrying the
// sender email and the full-date time title.
async function readRows(page, listSel) {
  return await page.evaluate((sel) => {
    const box = document.querySelector(sel);
    if (!box) return [];
    const emailRe = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    const rows = Array.from(box.querySelectorAll('[role="option"]'));
    return rows.map((r) => {
      const aria = r.getAttribute('aria-label') || '';
      const lines = (r.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);

      const titled = Array.from(r.querySelectorAll('[title]'));
      const senderEmails = [];
      let timeTitle = '';
      let timeText = '';
      for (const el of titled) {
        const title = (el.getAttribute('title') || '').trim();
        if (emailRe.test(title)) senderEmails.push(title.toLowerCase());
        // The time span: title has a full date, textContent the short form.
        if (el.tagName === 'SPAN' && /\d{4}/.test(title) && /\d{1,2}:\d{2}/.test((el.textContent || '') + title)) {
          timeTitle = title;
          timeText = (el.textContent || '').trim();
        }
      }

      // Line layout (probed): [avatar initials?, sender names, subject, time, preview]
      const timeIdx = timeText ? lines.indexOf(timeText) : -1;
      let subject = '';
      let sender = '';
      let preview = '';
      if (timeIdx > 0) {
        subject = lines[timeIdx - 1] || '';
        preview = lines[timeIdx + 1] || '';
        // Sender names: the line(s) before the subject, skipping 1–3 char
        // avatar-initials lines.
        const before = lines.slice(0, Math.max(0, timeIdx - 1))
          .filter((l) => !(l.length <= 3 && l === l.toUpperCase()));
        sender = before[before.length - 1] || '';
      } else {
        sender = lines[0] || '';
        subject = lines[1] || '';
      }

      return {
        convId: r.getAttribute('data-convid') || r.id || aria.slice(0, 120),
        aria,
        sender,
        senderEmails,
        subject,
        timeTitle,
        timeText,
        preview,
        unread: /^(no le[ií]do|unread)/i.test(aria),
      };
    });
  }, listSel);
}

// Scroll the virtualized list with real wheel events (OWA's virtual list
// ignores programmatic scrollBy on its containers).
async function wheelList(page, listSel, deltaY) {
  const box = await page.locator(listSel).first().boundingBox();
  if (!box) return;
  await page.mouse.move(box.x + box.width / 2, box.y + Math.min(box.height / 2, 300));
  await page.mouse.wheel(0, deltaY);
}

async function scrollListBack(page, listSel, cutoff, debug) {
  const seen = new Map();
  let stable = 0;
  let prevSize = -1;

  for (let round = 0; round < 60; round++) {
    const rows = await readRows(page, listSel);
    for (const r of rows) if (!seen.has(r.convId)) seen.set(r.convId, r);

    const times = rows.map((r) => parseFullDate(r.timeTitle)).filter(Boolean);
    const oldest = times.length ? Math.min(...times.map((d) => d.getTime())) : null;
    if (debug) log(`scroll round ${round}: rendered=${rows.length} total=${seen.size} oldest=${oldest && new Date(oldest).toISOString()}`);

    if (oldest !== null && oldest < cutoff.getTime()) break;

    if (seen.size === prevSize) {
      stable++;
      if (stable >= 3) break;
    } else {
      stable = 0;
      prevSize = seen.size;
    }

    await wheelList(page, listSel, 800);
    await page.waitForTimeout(700);
  }
  // Scroll back to the top so openRow starts from the newest rows.
  await wheelList(page, listSel, -100000);
  await page.waitForTimeout(500);
  return Array.from(seen.values());
}

async function expandConversation(page, debug) {
  // OWA collapses older messages / quoted history. Click expanders — but
  // ONLY inside the visible reading pane: a page-wide locator also matches
  // "expand conversation" buttons on message-list rows, and clicking those
  // silently switches the pane to a different conversation.
  const paneRoot = page.locator(
    ':is([data-app-section="ConversationReadingPaneContainer"], [data-app-section="ReadingPaneContainer"], [data-app-section="ItemReadingPaneContainer"]):visible',
  ).first();
  if (await paneRoot.count() === 0) {
    if (debug) log('no visible reading pane container; skipping expansion');
    return;
  }
  const expanders = [
    'button:has-text("See more messages")',
    'button:has-text("Ver más mensajes")',
    'button:has-text("Show message history")',
    'button:has-text("Mostrar el historial de mensajes")',
    'div[role="button"][aria-label*="xpand" i]',
    'button[aria-label*="xpand" i]',
    'button[aria-label*="istorial" i]',
  ];
  for (const sel of expanders) {
    let els = [];
    try { els = await paneRoot.locator(sel).all(); } catch (_) { /* skip */ }
    for (const el of els.slice(0, 10)) {
      try {
        await el.click({ timeout: 700 });
        await page.waitForTimeout(300);
      } catch (_) { /* ignore */ }
    }
  }
  if (debug) log('expanded conversation (best effort)');
}

async function extractConversation(page) {
  return await page.evaluate(({ BODY_CAP, PANE_CAP, resolverSrc }) => {
    const main = new Function(`return (${resolverSrc})()`)();
    if (!main) return { paneText: '', participants: [], messages: [] };

    const paneText = (main.innerText || '').slice(0, PANE_CAP);

    const emails = new Set();
    const emailRe = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
    for (const el of main.querySelectorAll('[title], [aria-label]')) {
      const s = (el.getAttribute('title') || '') + ' ' + (el.getAttribute('aria-label') || '');
      for (const m of s.match(emailRe) || []) emails.add(m.toLowerCase());
    }
    for (const m of paneText.match(emailRe) || []) emails.add(m.toLowerCase());

    const bodyNodes = Array.from(main.querySelectorAll(
      '[id^="UniqueMessageBody"], div[aria-label="Message body" i], div[aria-label*="uerpo del mensaje" i], .allowTextSelection[role="document"]',
    ));
    const messages = bodyNodes.map((b) => {
      let card = b;
      for (let i = 0; i < 8 && card.parentElement; i++) {
        card = card.parentElement;
        if (card.querySelector('[data-testid="SentReceivedSavedTime"], span[title*="@"]')) break;
      }
      const timeEl = card.querySelector('[data-testid="SentReceivedSavedTime"]');
      const authorEl = card.querySelector('span[title*="@"], [aria-label*="@"]');
      return {
        author: authorEl ? (authorEl.textContent || '').trim() : null,
        authorEmail: authorEl ? ((authorEl.getAttribute('title') || authorEl.getAttribute('aria-label') || '').match(emailRe) || [null])[0] : null,
        time: timeEl ? (timeEl.textContent || '').trim() : null,
        body: (b.innerText || '').trim().slice(0, BODY_CAP),
      };
    }).filter((m) => m.body);

    return { paneText, participants: Array.from(emails), messages };
  }, { BODY_CAP, PANE_CAP, resolverSrc: RESOLVE_PANE_SRC });
}

// Scroll the list until the row with convId is rendered; return its locator.
async function locateRow(page, listSel, convId, debug) {
  const rowSel = `${listSel} [role="option"][data-convid=${JSON.stringify(convId)}]`;
  // Start from the top of the list each time (virtualized rows come and go).
  await wheelList(page, listSel, -100000);
  await page.waitForTimeout(400);
  for (let attempt = 0; attempt < 20; attempt++) {
    const loc = page.locator(rowSel).first();
    if (await loc.count() > 0) {
      await loc.scrollIntoViewIfNeeded().catch(() => {});
      return loc;
    }
    await wheelList(page, listSel, 700);
    await page.waitForTimeout(400);
  }
  if (debug) log(`row not found after scrolling: ${convId}`);
  return null;
}

// Key used to confirm the reading pane actually shows the clicked row:
// the subject minus any "..." truncation, whitespace-normalized.
function subjectKey(subject) {
  const s = (subject || '').split('...')[0].replace(/\s+/g, ' ').trim();
  return s.slice(0, 40);
}

// Resolve the reading-pane element in browser context. Constraints learned
// the hard way:
//   - OWA keeps MULTIPLE reading-pane containers in the DOM (recently opened
//     conversations stay as hidden cached panes) — must pick the VISIBLE one.
//   - [role="main"] contains the message list too, so any subject check
//     against it passes vacuously — must exclude the list subtree.
// Injected as a plain function argument into each evaluate call.
function resolvePaneInBrowser() {
  const list = document.querySelector('[data-app-section="MessageList"]');
  const visible = (e) => {
    const r = e.getBoundingClientRect();
    return r.width > 100 && r.height > 100;
  };
  const cands = Array.from(document.querySelectorAll(
    '[data-app-section="ConversationReadingPaneContainer"], [data-app-section="ReadingPaneContainer"], [data-app-section="ItemReadingPaneContainer"]',
  )).filter((e) => visible(e) && (!list || !e.contains(list)));
  if (cands.length) {
    // Most text wins (a stale-but-visible shell would be near-empty).
    return cands.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
  }
  const main = document.querySelector('[role="main"]');
  if (main && (!list || !main.contains(list))) return main;
  return null;
}
const RESOLVE_PANE_SRC = resolvePaneInBrowser.toString();

async function paneShows(page, key) {
  return await page.evaluate(({ k, resolverSrc }) => {
    const pane = new Function(`return (${resolverSrc})()`)();
    if (!pane) return false;
    const text = (pane.innerText || '').replace(/\s+/g, ' ');
    return k.length > 0 && text.includes(k) && text.length > 200;
  }, { k: key, resolverSrc: RESOLVE_PANE_SRC });
}

// Click the row and wait until the reading pane shows THIS conversation.
// Guards against the stale-pane failure mode where a click doesn't switch
// the pane and we'd silently extract the previous conversation.
async function openRow(page, listSel, row, debug) {
  const key = subjectKey(row.subject);
  for (let attempt = 0; attempt < 3; attempt++) {
    const loc = await locateRow(page, listSel, row.convId, debug);
    if (!loc) return false;
    try {
      if (attempt === 0) {
        await loc.click({ timeout: 5000 });
      } else {
        // Retry via keyboard — more reliable on collapsed conversation rows.
        await loc.click({ timeout: 5000 });
        await page.keyboard.press('Enter');
      }
    } catch (e) {
      if (debug) log(`click failed (attempt ${attempt}): ${e.message}`);
      continue;
    }
    for (let w = 0; w < 10; w++) {
      await page.waitForTimeout(1000);
      if (await paneShows(page, key)) return true;
    }
    if (debug) log(`pane did not show "${key}" after attempt ${attempt}`);
  }
  return false;
}

(async () => {
  const args = parseArgs(process.argv);
  const filters = args.filter ? loadFilters() : { names: [], emails: [], subjects: [] };
  const cutoff = new Date(Date.now() - args.hoursBack * 3600 * 1000);

  if (args.debug) {
    log('profile:', args.profileDir);
    log('cutoff: ', cutoff.toISOString());
    if (args.query) log('query:  ', args.query);
  }

  if (!fs.existsSync(args.profileDir)) {
    die(2, `profile dir does not exist: ${args.profileDir}\nRun scripts/outlook_login.sh first.`);
  }

  let ctx;
  try {
    ctx = await chromium.launchPersistentContext(args.profileDir, {
      headless: args.headless,
      viewport: { width: 1600, height: 1000 },
      args: ['--disable-blink-features=AutomationControlled'],
    });
  } catch (e) {
    die(3, `failed to launch chromium: ${e.message}`);
  }

  const page = ctx.pages()[0] || await ctx.newPage();
  page.setDefaultTimeout(args.timeoutMs);

  try {
    await page.goto('https://outlook.office.com/mail/inbox/', {
      waitUntil: 'domcontentloaded', timeout: args.timeoutMs,
    });
    await page.waitForTimeout(4000);

    if (/login\.microsoftonline\.com|login\.live\.com/.test(page.url())) {
      die(2, `redirected to login: ${page.url()}\nRun scripts/outlook_login.sh to re-authenticate.`);
    }

    if (args.query) {
      const searchSel = ['#topSearchInput', 'input[aria-label*="earch" i]', 'input[aria-label*="uscar" i]', '[role="searchbox"]'];
      let found = false;
      for (const sel of searchSel) {
        const loc = page.locator(sel).first();
        if (await loc.count() > 0 && await loc.isVisible().catch(() => false)) {
          await loc.click();
          await loc.fill(args.query);
          await page.keyboard.press('Enter');
          found = true;
          break;
        }
      }
      if (!found) die(3, 'could not find the Outlook search box');
      await page.waitForTimeout(4000);
    }

    const listSel = await findListbox(page, args.timeoutMs);
    if (!listSel) die(3, 'could not find the Outlook message list. Run with FETCH_HEADED=1 FETCH_DEBUG=1 to inspect.');
    if (args.debug) log('message list selector:', listSel);

    const allRows = await scrollListBack(page, listSel, cutoff, args.debug);
    if (args.debug) log(`collected ${allRows.length} rows total`);

    // Window filter (search mode keeps everything; window is advisory there).
    const inWindow = allRows.filter((r) => {
      const t = parseFullDate(r.timeTitle);
      r.rowTimeIso = t ? t.toISOString() : null;
      if (args.query) return true;
      if (!t) return false;
      return t.getTime() >= cutoff.getTime();
    });

    // Noise filter — sender email is available right on the row now.
    const dropped = [];
    const kept = inWindow.filter((r) => {
      const sender = (r.sender || '').toLowerCase();
      if (filters.names.some((n) => sender === n || sender.startsWith(n + ' '))) {
        dropped.push({ subject: r.subject, why: `sender name "${r.sender}"` });
        return false;
      }
      if (r.senderEmails.length && r.senderEmails.every((e) => filters.emails.some((re) => re.test(e)))) {
        dropped.push({ subject: r.subject, why: `sender email ${r.senderEmails.join(',')}` });
        return false;
      }
      if (filters.subjects.some((re) => re.test(r.subject || ''))) {
        dropped.push({ subject: r.subject, why: 'subject pattern' });
        return false;
      }
      return true;
    });

    if (args.debug) {
      log(`rows in window: ${inWindow.length}, after noise filter: ${kept.length}`);
      for (const d of dropped) log(`  dropped: "${d.subject}" (${d.why})`);
    }

    const results = [];
    for (const row of kept.slice(0, args.max)) {
      try {
        if (!(await openRow(page, listSel, row, args.debug))) {
          log(`WARN: could not open "${row.subject}" — skipping`);
          continue;
        }
        await expandConversation(page, args.debug);
        const conv = await extractConversation(page);

        results.push({
          convId: row.convId,
          subject: row.subject,
          rowSender: row.sender,
          senderEmails: row.senderEmails,
          rowTimeIso: row.rowTimeIso || null,
          preview: row.preview,
          isUnread: row.unread,
          participants: conv.participants,
          messages: conv.messages,
          paneText: conv.paneText,
        });
        if (args.debug) log(`extracted: "${row.subject}" (${conv.messages.length} structured msgs, ${conv.participants.length} participants)`);
      } catch (e) {
        log(`WARN: failed to open "${row.subject}": ${e.message}`);
      }
    }

    process.stdout.write(JSON.stringify(results));
    process.stdout.write('\n');
  } catch (e) {
    die(3, `scrape error: ${e.message}`);
  } finally {
    await ctx.close().catch(() => {});
  }
})();
