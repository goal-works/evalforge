import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const baseURL = process.env.EVALFORGE_CAPTURE_URL ?? "http://127.0.0.1:3010";
const outputDirectory = path.resolve(
  process.env.EVALFORGE_CAPTURE_OUTPUT ?? "../../public/projects/evalforge",
);

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });

await page.goto(baseURL, { waitUntil: "networkidle" });
await page.screenshot({ path: path.join(outputDirectory, "dashboard.png"), fullPage: true });

await page.goto(`${baseURL}/benchmarks`, { waitUntil: "networkidle" });
await page.locator(".benchmark-card").first().click();
await page.waitForLoadState("networkidle");
await page.screenshot({ path: path.join(outputDirectory, "benchmark-detail.png"), fullPage: true });

await page.goto(`${baseURL}/runs`, { waitUntil: "networkidle" });
await page.locator(".run-id").first().click();
await page.waitForLoadState("networkidle");
await page.locator("summary").first().click();
await page.screenshot({ path: path.join(outputDirectory, "run-detail.png"), fullPage: true });

await browser.close();
console.log(`Captured EvalForge portfolio evidence in ${outputDirectory}`);
