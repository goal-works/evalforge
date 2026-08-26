import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("creates a benchmark task and inspectable evaluation run", async ({ page }) => {
  const suffix = Date.now().toString(36);
  await page.goto("/benchmarks");
  await page.getByRole("button", { name: "New benchmark" }).click();
  await page.getByLabel("Name").fill(`Browser Contract ${suffix}`);
  await page.getByLabel("Slug").fill(`browser-contract-${suffix}`);
  await page.getByLabel("Status").selectOption("Active");
  await page.getByRole("button", { name: "Create benchmark" }).click();
  await expect(page.getByRole("heading", { name: `Browser Contract ${suffix}` })).toBeVisible();

  await page.getByRole("link", { name: "Add task" }).click();
  await page.getByLabel("Name", { exact: true }).fill("Return health status");
  await page.getByLabel("Slug").fill("return-health-status");
  await page.getByLabel("Task instruction").fill("Return the exact word ok.");
  await page.getByLabel("Configuration JSON").fill('{"expected":"ok"}');
  await page.getByLabel("Metadata JSON").fill(
    '{"mock_success_output":"ok","mock_failure_output":"error"}',
  );
  await page.getByRole("button", { name: "Save task" }).click();
  await expect(page.getByRole("heading", { name: "Return health status" })).toBeVisible();

  await page.getByRole("button", { name: "Start evaluation" }).click();
  await expect(page).toHaveURL(/\/runs\//);
  await expect(page.locator(".status-completed").filter({ hasText: "Completed" })).toBeVisible();
  const taskResult = page.locator("summary").filter({ hasText: "Return health status" });
  await expect(taskResult).toBeVisible();
  await taskResult.click();
  await expect(page.getByText("Execution timeline", { exact: true })).toBeVisible();
});

test("primary product pages have no serious accessibility violations", async ({ page }) => {
  for (const path of ["/", "/benchmarks", "/runs", "/agents", "/analytics"]) {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((violation) => ["serious", "critical"].includes(violation.impact ?? "")),
    ).toEqual([]);
  }
});
