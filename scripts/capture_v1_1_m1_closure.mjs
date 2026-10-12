import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const outputDir = join(root, "artifacts", "v1.1-m1-final-closure-2026-09-24");
const env = Object.fromEntries(
  (await readFile(join(root, ".env"), "utf8"))
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .map((line) => {
      const index = line.indexOf("=");
      return [line.slice(0, index).trim(), line.slice(index + 1).trim()];
    }),
);
const origin = "http://127.0.0.1:5173";
const edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const port = 19331;
const profileDir = await mkdtemp(join(tmpdir(), "v1-1-m1-edge-"));
await mkdir(outputDir, { recursive: true });

const browser = spawn(edge, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profileDir}`,
  "--window-size=1440,1000",
  "about:blank",
], { stdio: "ignore" });

const delay = (ms) => new Promise((resolveDelay) => setTimeout(resolveDelay, ms));

async function getJson(path, retries = 80) {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}${path}`);
      if (response.ok) return await response.json();
    } catch {}
    await delay(100);
  }
  throw new Error(`CDP endpoint unavailable: ${path}`);
}

const pages = await getJson("/json/list");
const pageTarget = pages.find((item) => item.type === "page");
if (!pageTarget) throw new Error("No Edge page target");
const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
await new Promise((resolveOpen, rejectOpen) => {
  socket.addEventListener("open", resolveOpen, { once: true });
  socket.addEventListener("error", rejectOpen, { once: true });
});

let commandId = 0;
const pending = new Map();
const browserErrors = [];
const httpErrors = [];
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolveCommand, rejectCommand } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) rejectCommand(new Error(message.error.message));
    else resolveCommand(message.result);
  }
  if (message.method === "Runtime.exceptionThrown") browserErrors.push(message.params.exceptionDetails.text);
  if (message.method === "Log.entryAdded" && message.params.entry.level === "error") browserErrors.push(message.params.entry.text);
  if (message.method === "Network.responseReceived" && [403, 404].includes(message.params.response.status)) {
    httpErrors.push(`${message.params.response.status} ${message.params.response.url}`);
  }
});

function send(method, params = {}) {
  commandId += 1;
  const id = commandId;
  return new Promise((resolveCommand, rejectCommand) => {
    pending.set(id, { resolveCommand, rejectCommand });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function navigate(url) {
  await send("Page.navigate", { url });
  for (let index = 0; index < 100; index += 1) {
    const ready = await evaluate("document.readyState");
    if (ready === "complete") break;
    await delay(100);
  }
  await delay(700);
}

async function setViewport(width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  await delay(150);
}

async function login(username, password) {
  const response = await fetch(`${origin}/api/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(`Login failed for ${username}: ${response.status}`);
  return (await response.json()).access_token;
}

async function useToken(token) {
  await navigate(`${origin}/login`);
  await evaluate(`localStorage.setItem("access_token", ${JSON.stringify(token)})`);
  await navigate(`${origin}/`);
}

async function screenshot(filename) {
  await evaluate("window.scrollTo(0, 0)");
  await delay(150);
  const result = await send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  await writeFile(join(outputDir, filename), Buffer.from(result.data, "base64"));
}

async function chooseProject(label) {
  const selected = await evaluate(`(async () => {
    const select = document.querySelector('[data-dashboard="project-manager"] .el-select__wrapper');
    if (!select) return false;
    select.click();
    await new Promise((resolve) => setTimeout(resolve, 500));
    const option = [...document.querySelectorAll('.el-select-dropdown__item')].find((node) => node.textContent.trim() === ${JSON.stringify(label)});
    if (!option) return false;
    option.click();
    return true;
  })()`);
  if (!selected) throw new Error(`Project selector option not found: ${label}`);
  await delay(1200);
}

async function responsiveChecks(role) {
  const results = [];
  for (const [width, height] of [[1440, 1000], [1366, 768], [1280, 1000], [1024, 1000], [979, 1000]]) {
    await setViewport(width, height);
    const metrics = await evaluate(`({
      innerWidth: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      headerVisible: !!document.querySelector('.header'),
      sidebarVisible: !!document.querySelector('.aside'),
      dashboard: document.querySelector('[data-dashboard]')?.getAttribute('data-dashboard') || null
    })`);
    results.push({ role, width, height, ...metrics, noHorizontalOverflow: metrics.documentWidth <= metrics.innerWidth && metrics.bodyWidth <= metrics.innerWidth });
  }
  return results;
}

async function menuLabels() {
  return evaluate(`[...document.querySelectorAll('.el-menu-item')].map((item) => item.textContent.trim())`);
}

async function routeRedirects(paths) {
  const checks = [];
  for (const path of paths) {
    await navigate(`${origin}${path}`);
    checks.push({ requested: path, actual: await evaluate("location.pathname") });
  }
  await navigate(`${origin}/`);
  return checks;
}

await send("Page.enable");
await send("Runtime.enable");
await send("Log.enable");
await send("Network.enable");
await setViewport(1440, 1000);

const password = env.DASHBOARD_DEMO_PASSWORD || "change_me";
const accounts = {
  admin: [env.INITIAL_ADMIN_USERNAME || "admin", env.INITIAL_ADMIN_PASSWORD || "change_me"],
  boss: ["demo_boss", password],
  pm: ["demo_pm_a", password],
  memberFull: ["demo_member_a", password],
  memberEmpty: ["demo_member_b", password],
};
const report = { screenshots: [], responsive: [], menus: {}, routes: {}, consoleErrors: {}, httpErrors: {} };

for (const [key, [username, accountPassword]] of Object.entries(accounts)) {
  const token = await login(username, accountPassword);
  browserErrors.length = 0;
  httpErrors.length = 0;
  await setViewport(1440, 1000);
  await useToken(token);
  report.menus[key] = await menuLabels();

  if (key === "admin") {
    await screenshot("admin-dashboard-final.png");
    report.screenshots.push("admin-dashboard-final.png");
    report.routes[key] = [];
  } else if (key === "boss") {
    await screenshot("boss-dashboard-final.png");
    report.screenshots.push("boss-dashboard-final.png");
    report.routes[key] = await routeRedirects(["/users", "/settings"]);
  } else if (key === "pm") {
    await chooseProject("Demo Alpha");
    await screenshot("pm-dashboard-project-a-final.png");
    await chooseProject("企业协同 Demo Beta");
    await screenshot("pm-dashboard-project-b-final.png");
    report.screenshots.push("pm-dashboard-project-a-final.png", "pm-dashboard-project-b-final.png");
    report.routes[key] = await routeRedirects(["/recurring-expenses", "/employees", "/users", "/audit-logs", "/settings"]);
  } else if (key === "memberFull") {
    await screenshot("member-dashboard-full-final.png");
    report.screenshots.push("member-dashboard-full-final.png");
    report.routes[key] = await routeRedirects(["/recurring-expenses", "/employees", "/users", "/audit-logs", "/settings"]);
  } else {
    await screenshot("member-dashboard-empty-final.png");
    report.screenshots.push("member-dashboard-empty-final.png");
    report.routes[key] = await routeRedirects(["/recurring-expenses", "/employees", "/users", "/audit-logs", "/settings"]);
  }

  report.responsive.push(...await responsiveChecks(key));
  report.consoleErrors[key] = [...browserErrors];
  report.httpErrors[key] = [...httpErrors];
}

await writeFile(join(outputDir, "browser-verification.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
socket.close();
browser.kill();
await Promise.race([
  new Promise((resolveExit) => browser.once("exit", resolveExit)),
  delay(1500),
]);
await delay(250);
try {
  await rm(profileDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
} catch (error) {
  console.warn(`Temporary browser profile cleanup deferred: ${error.code || error.message}`);
}
process.exit(0);
