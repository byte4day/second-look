#!/usr/bin/env node
/**
 * Agent-led accessibility / older-adult proxy session.
 * Keyboard-only nav, 200% zoom, high contrast, axe on key routes.
 */
import { chromium } from 'playwright-core'
import { writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import axeCore from 'axe-core'

const __dirname = dirname(fileURLToPath(import.meta.url))
const BASE = process.env.A11Y_BASE || 'http://127.0.0.1:5173'
const outPath = resolve(__dirname, '../../docs/a11y-session-latest.json')

const routes = ['/', '/check', '/practise', '/help', '/family', '/scams-near-me', '/settings']

async function injectAxe(page) {
  await page.addScriptTag({ content: axeCore.source })
}

async function runAxe(page) {
  return page.evaluate(async () => {
    // eslint-disable-next-line no-undef
    const results = await axe.run(document, {
      rules: {
        'color-contrast': { enabled: true },
      },
    })
    return {
      violations: results.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.length,
        help: v.help,
      })),
    }
  })
}

async function main() {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  })
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })
  const report = {
    date: new Date().toISOString().slice(0, 10),
    base: BASE,
    mode: 'agent_proxy_older_adult',
    notes: [],
    routes: {},
  }

  // Keyboard: skip link + tab to first primary control on Home
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' })
  await page.keyboard.press('Tab')
  const skipFocused = await page.evaluate(() => document.activeElement?.textContent?.trim() || '')
  report.notes.push(`Skip/focus first Tab landed on: "${skipFocused}"`)

  for (const route of routes) {
    await page.goto(BASE + route, { waitUntil: 'domcontentloaded', timeout: 20000 })
    await page.waitForTimeout(400)
    await injectAxe(page)
    const axe = await runAxe(page)
    const h1 = await page.locator('h1').first().textContent().catch(() => null)
    const main = await page.locator('#main-content').count()
    report.routes[route] = {
      h1: h1?.trim() || null,
      hasMain: main === 1,
      axeViolations: axe.violations,
    }
  }

  // 200% zoom on Check
  await page.goto(BASE + '/check', { waitUntil: 'domcontentloaded' })
  await page.evaluate(() => {
    document.body.style.zoom = '2'
  })
  await page.waitForTimeout(200)
  const overflowX = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
  )
  report.notes.push(`Check at ~200% zoom horizontal overflow: ${overflowX}`)
  await page.evaluate(() => {
    document.body.style.zoom = '1'
  })

  // High contrast + extra-large text via settings prefs
  await page.goto(BASE + '/settings', { waitUntil: 'domcontentloaded' })
  const high = page.getByLabel(/high contrast/i).or(page.getByText(/high contrast/i))
  if (await high.count()) {
    await high.first().click({ force: true }).catch(() => {})
  }
  const xl = page.getByText(/extra large/i)
  if (await xl.count()) {
    await xl.first().click({ force: true }).catch(() => {})
  }
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' })
  const attrs = await page.evaluate(() => ({
    contrast: document.documentElement.getAttribute('data-contrast'),
    text: document.documentElement.getAttribute('data-text-size'),
  }))
  report.notes.push(`Prefs after settings: contrast=${attrs.contrast} text=${attrs.text}`)

  // Screen-reader-ish: ensure risk/status regions exist after a canned check via API-less UI sample fill
  await page.goto(BASE + '/check', { waitUntil: 'domcontentloaded' })
  const sample = page.getByRole('button', { name: /use a scam text/i })
  if (await sample.count()) {
    await sample.click()
    const value = await page.locator('#message').inputValue()
    report.notes.push(`Sample scam filled textarea (${value.length} chars)`)
  }

  writeFileSync(outPath, JSON.stringify(report, null, 2))
  const bad = Object.values(report.routes).flatMap((r) => r.axeViolations)
  console.log(JSON.stringify({ outPath, routes: routes.length, axeIssues: bad.length, notes: report.notes }, null, 2))
  if (bad.some((v) => v.impact === 'critical' || v.impact === 'serious')) {
    process.exitCode = 1
  }
  await browser.close()
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
