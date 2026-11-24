// Real captures of the running app (http://127.0.0.1:5173) for the 60s film.
// Each state: a full-page PNG at 2x density + bounding boxes of the elements the cursor visits.
import { chromium } from '/home/byte/hackathon/frontend/node_modules/playwright-core/index.mjs'
import fs from 'node:fs'

const OUT = new URL('./cap/', import.meta.url).pathname
fs.mkdirSync(OUT, { recursive: true })
const B = 'http://127.0.0.1:5173'
const MARGARET_TEXT =
  'Metro Bank: your account has been LOCKED due to suspicious activity. Reply with the 6-digit code we just sent within 30 minutes or your account will be closed. Call 0800 000 000.'

const browser = await chromium.launch()
const ctx = await browser.newContext({
  viewport: { width: 900, height: 720 },
  deviceScaleFactor: 2,
  reducedMotion: 'reduce',
})
const page = await ctx.newPage()
const errors = []
page.on('pageerror', (e) => errors.push(String(e)))
const meta = {}

async function box(locator) {
  const b = await locator.first().boundingBox()
  const y = await page.evaluate(() => window.scrollY)
  return b ? { x: b.x, y: b.y + y, w: b.width, h: b.height } : null
}
async function shot(name, boxes = {}) {
  await page.waitForTimeout(350)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(100)
  const resolved = {}
  for (const [k, loc] of Object.entries(boxes)) resolved[k] = await box(loc)
  const h = await page.evaluate(() => document.documentElement.scrollHeight)
  await page.screenshot({ path: `${OUT}${name}.png`, fullPage: true })
  meta[name] = { height: h, boxes: resolved }
  console.log('captured', name, h)
}

// 1. Home
await page.goto(B + '/', { waitUntil: 'networkidle' })
await shot('home', { check: page.getByRole('link', { name: /check a message/i }) })

// 2. Check: Margaret types her text
await page.getByRole('link', { name: /check a message/i }).click()
await page.waitForURL(/check$/)
await shot('check_empty', { box: page.locator('#message') })
const ta = page.locator('#message')
const steps = 6
for (let i = 1; i <= steps; i++) {
  await ta.fill(MARGARET_TEXT.slice(0, Math.round((MARGARET_TEXT.length * i) / steps)))
  await shot(`check_type_${i}`, {
    box: ta,
    submit: page.getByRole('button', { name: /check this message/i }),
  })
}

// 3. Result
await page.getByRole('button', { name: /check this message/i }).click()
await page.waitForURL(/result/, { timeout: 30000 })
await page.waitForTimeout(500)
await shot('result', {
  risk: page.locator('.risk-box'),
  marks: page.locator('.message-source'),
  todo: page.getByRole('heading', { name: /what to do now/i }),
})

// 4. Practise → chat
await page.goto(B + '/practise', { waitUntil: 'networkidle' })
await shot('practise', { quick: page.getByRole('button', { name: /start the bank fraud/i }) })
await page.getByRole('button', { name: /start the bank fraud/i }).click()
await page.waitForURL(/practise\/chat/)
await page.waitForTimeout(800)
// Keep the caller voice off so the capture is silent and deterministic.
const voiceBtn = page.getByRole('button', { name: /caller voice is on/i })
if (await voiceBtn.count()) await voiceBtn.click()
const reply = page.getByLabel(/your reply/i)
await shot('chat_1', { reply, hang: page.getByRole('button', { name: /hang up/i }) })
const say = "No. I won't give you any code. I'm hanging up and calling my bank myself."
for (let i = 1; i <= 4; i++) {
  await reply.fill(say.slice(0, Math.round((say.length * i) / 4)))
  await shot(`chat_type_${i}`, { reply, send: page.getByRole('button', { name: /^send$/i }) })
}
await page.getByRole('button', { name: /^send$/i }).click()
await page.waitForTimeout(1500)
await shot('chat_2', { hang: page.getByRole('button', { name: /hang up/i }) })

// 5. Debrief
await page.getByRole('button', { name: /hang up/i }).click()
await page.waitForURL(/debrief/, { timeout: 30000 })
await page.waitForTimeout(1200)
await shot('debrief')

// 6. Help now, Family, Scams near me
await page.goto(B + '/help', { waitUntil: 'networkidle' })
await shot('help', { steps: page.locator('.numbered-steps') })
await page.goto(B + '/family', { waitUntil: 'networkidle' })
await shot('family', { text: page.getByRole('link', { name: /text someone i trust/i }) })
await page.goto(B + '/scams-near-me', { waitUntil: 'networkidle' })
await shot('scams', { chart: page.getByRole('heading', { name: /reports in the last week/i }) })

fs.writeFileSync(`${OUT}meta.json`, JSON.stringify(meta, null, 1))
console.log('errors:', errors.length ? errors.join('\n') : 'none')
await browser.close()
