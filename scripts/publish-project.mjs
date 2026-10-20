#!/usr/bin/env node
/**
 * publish-project.mjs —— 把一个全景项目从素材一步推到可上线状态。
 *
 * 取代手工五步（build:tour 切片 → --slim-from 托管版 → 拷 _web 到 catalog/projects/<id>
 * → 从某景裁封面 → 改 data/projects.json）。构建产物落 editor/panotour/dist，
 * 收录物落 catalog/，之后你再单独跑 deploy-catalog.mjs 上线（本脚本默认不自动部署）。
 *
 * 用法：
 *   node scripts/publish-project.mjs --spec editor/示范案例/tour_spec.json
 *   node scripts/publish-project.mjs --spec <spec> --brand gongsheng --skip-build
 *   node scripts/publish-project.mjs --spec <spec> --deploy --bucket gsyz-web --ossutil "C:\\ossutil.exe"
 *
 * spec 沿用 tour_spec.json（project / plan / scenes），再加一个 publish 块：
 *   "publish": {
 *     "id": "renheng-jiachengli",        // 必填：项目编号，决定 catalog/projects/<id>/ 与封面名
 *     "title": "仁恒·夹城里",             // 必填：归纳页标题（不填则用 spec.project）
 *     "category": "量房记录",              // 选填：站点三分类之一（量房记录/水电记录/全景效果），体系外新分类会自动追加筛选
 *     "location": "", "year": 2026, "description": "", "tags": [],
 *     "cover": { "scene": 3, "yaw": 10, "pitch": 0, "fov": 75 }  // 选填：用第几景裁封面（scene=1基序号或场景名）
 *   }
 *
 * --skip-build：dist 里已有本项目的托管版，跳过切片与派生，只做收录+封面+登记（省几分钟）。
 * publish.cover 省略时：若已存在 catalog/assets/covers/<id>.jpg 就沿用，否则跳过封面并提示。
 */
import { readdir, readFile, writeFile, stat, cp, mkdir, rm } from "node:fs/promises";
import { spawn, spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EDITOR = path.join(ROOT, "editor");
const DIST = path.join(EDITOR, "panotour", "dist");
const BUILD_PY = path.join(EDITOR, "panotour", "build_tour.py");
const COVER_PY = path.join(ROOT, "scripts", "cover_crop.py");
const DEPLOY_JS = path.join(ROOT, "scripts", "deploy-catalog.mjs");
const CATALOG = path.join(ROOT, "catalog");
const PROJECTS_JSON = path.join(CATALOG, "data", "projects.json");
const COVERS_DIR = path.join(CATALOG, "assets", "covers");

const args = process.argv.slice(2);
const arg = (n, fb) => { const i = args.indexOf(`--${n}`); return i >= 0 && args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : fb; };
const flag = (n) => args.includes(`--${n}`);

const SPEC_ARG = arg("spec", "");
if (!SPEC_ARG) die("必须 --spec <tour_spec.json>");
const BRAND = arg("brand", "gongsheng");
const SKIP_BUILD = flag("skip-build");
const DO_DEPLOY = flag("deploy");

function die(msg) { console.error("× " + msg); process.exit(2); }
const t0 = Date.now();
const step = (m) => console.log(`\n▶ ${m}`);
function run(cmd, argv, cwd) {
  return new Promise((resolve, reject) => {
    const c = spawn(cmd, argv, { cwd, stdio: "inherit", shell: false });
    c.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`${path.basename(cmd)} 退出码 ${code}`))));
    c.on("error", reject);
  });
}
// Git-Bash 的 python 常是 PATH 外的 shim，Node 直连 spawn 找不到；
// 解析策略：用 bash `command -v` 探测（bash 的 PATH 与我们一致或更宽），
// 再用 Windows 已知安装位置兜底；每个候选用 `-c pass` 真跑一遍验证。
let PY = arg("python", "");
function tryRun(cmd, argv) {
  return new Promise((resolve) => {
    const c = spawn(cmd, argv, { cwd: ROOT, stdio: "ignore", shell: false });
    c.on("close", (code) => resolve(code === 0));
    c.on("error", () => resolve(false));
  });
}
async function resolvePython() {
  if (PY) return PY;
  const found = [];
  try {
    const r = spawnSync("bash", ["-lc", "for c in python py python3; do command -v \"$c\" 2>/dev/null; done"]);
    if (!r.error && r.stdout) found.push(...r.stdout.toString().split(/\r?\n/).map((s) => s.trim()).filter(Boolean));
  } catch { /* bash 不可用时静默走兜底 */ }
  found.push(
    "C:\\Users\\huaiw\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
    "D:\\DevTools\\Python\\python.exe",
  );
  for (const cand of found) {
    // Git-Bash 路径 (/c/...) 转 Windows 绝对路径，Node 直连才认
    const win = /^\/\w\//.test(cand) ? cand.replace(/^\/(\w)\//, (_, d) => d.toUpperCase() + ":\\").replace(/\//g, "\\") : cand;
    if (await tryRun(win, ["-c", "pass"])) return (PY = win);
  }
  die("找不到可用的 Python 解释器，可用 --python 指定绝对路径");
}
async function py(argv) { return run(await resolvePython(), argv, ROOT); }

async function main() {
  const specPath = path.resolve(ROOT, SPEC_ARG);
  const spec = JSON.parse(await readFile(specPath, "utf8"));
  const pub = spec.publish || {};
  const id = pub.id;
  const title = pub.title || spec.project;
  if (!id) die('spec.publish.id 必填（项目编号，如 renheng-jiachengli）');
  if (!title) die("spec.project 或 publish.title 至少要有一个");
  const scenes = Array.isArray(spec.scenes) ? spec.scenes : [];
  if (!scenes.length) die("spec.scenes 为空");

  const projDir = path.join(CATALOG, "projects", id);
  const coverPath = path.join(COVERS_DIR, `${id}.jpg`);
  console.log(`项目：${title}  (id=${id})  ${scenes.length} 景  品牌=${BRAND}`);

  // 1+2) 构建完整版并派生托管版（--skip-build 时跳过，直接找现成托管版）
  if (!SKIP_BUILD) {
    step("切片并构建完整版导览");
    await py([BUILD_PY, "--brand", BRAND, "--project", title, "--spec", specPath, "--out", DIST]);
    step("派生托管版（去原图，用于发布）");
    const fullZip = await newestIn(DIST, (f) => f.includes(sanitizeLoose(title)) && f.endsWith("_全景导览.zip"));
    if (!fullZip) die(`未能在 dist 找到 ${title} 的完整版 ZIP，无法派生托管版`);
    await py([BUILD_PY, "--brand", BRAND, "--project", title, "--slim-from", fullZip, "--out", DIST]);
  } else {
    step("跳过构建（--skip-build）");
  }

  // 3) 定位托管版 _web 目录并拷进 catalog/projects/<id>/
  step("收录托管版到 catalog/projects/");
  const viewDir = await newestDir(DIST, (d) => d.endsWith("_托管版_web") && d.includes(sanitizeLoose(title)));
  if (!viewDir) die("未找到托管版 _web 目录；若确已构建，去掉 --skip-build 重跑");
  await rm(projDir, { recursive: true, force: true });
  await mkdir(projDir, { recursive: true });
  await cp(path.join(DIST, viewDir), projDir, { recursive: true });
  const idxStat = await stat(path.join(projDir, "index.html")).catch(() => null);
  if (!idxStat) die("收录后 catalog 项目目录缺少 index.html");
  console.log(`  ✓ ${path.relative(ROOT, projDir)}`);

  // 4) 封面
  if (pub.cover) {
    const sceneIdx = Number(pub.cover.scene);
    const sc = Number.isFinite(sceneIdx) ? scenes[sceneIdx - 1] : scenes.find((s) => s.name === pub.cover.scene);
    if (!sc) die(`publish.cover.scene=${pub.cover.scene} 在 scenes 里找不到（1 基序号或场景名）`);
    const specDir = path.dirname(specPath);
    const imgPath = path.isAbsolute(sc.image) ? sc.image : path.resolve(specDir, sc.image);
    step("生成 16:9 封面");
    await mkdir(COVERS_DIR, { recursive: true });
    await py([COVER_PY, imgPath, coverPath,
      "--yaw", String(pub.cover.yaw ?? 0), "--pitch", String(pub.cover.pitch ?? 0), "--fov", String(pub.cover.fov ?? 75)]);
  } else {
    const exists = await stat(coverPath).then(() => true, () => false);
    console.log(exists ? `\n· 沿用已有封面：${path.relative(ROOT, coverPath)}` : `\n! spec 未配 publish.cover 且无同名封面，归纳页将无图（可后补）`);
  }

  // 5) 登记 projects.json（按 id 去重：有则替换、无则追加）
  step("登记 data/projects.json");
  const data = JSON.parse(await readFile(PROJECTS_JSON, "utf8"));
  if (!Array.isArray(data.projects)) data.projects = [];
  const entry = {
    id, title,
    category: pub.category || "全景项目",
    location: pub.location || "",
    year: pub.year || new Date().getFullYear(),
    scenes: scenes.length,
    description: pub.description || "",
    cover: `assets/covers/${id}.jpg`,
    href: `projects/${id}/index.html`,
    tags: Array.isArray(pub.tags) ? pub.tags : [],
  };
  const i = data.projects.findIndex((p) => p && p.id === id);
  if (i >= 0) { data.projects[i] = entry; console.log(`  ✓ 更新既有记录 #${i + 1}`); }
  else { data.projects.push(entry); console.log(`  ✓ 新增记录，共 ${data.projects.length} 个项目`); }
  await writeFile(PROJECTS_JSON, JSON.stringify(data, null, 2) + "\n");

  // 6) 可选部署
  if (DO_DEPLOY) {
    step("增量部署到 OSS");
    const dv = ["--bucket", arg("bucket", ""), "--prefix", arg("prefix", "pano")];
    const oss = arg("ossutil", ""); if (oss) dv.push("--ossutil", oss);
    if (flag("full")) dv.push("--full");
    if (flag("dry-run")) dv.push("--dry-run");
    await run(process.execPath, [DEPLOY_JS, ...dv], ROOT);
  } else {
    console.log(`\n· 未部署。核对后上线：\n    node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\\ossutil.exe"`);
  }

  console.log(`\n✓ 完成，用时 ${((Date.now() - t0) / 1000).toFixed(1)}s。本地预览：python -m http.server 8125 --directory catalog`);
}

// dist 文件名带中文与符号，匹配时用宽松净化后的子串
function sanitizeLoose(s) { return String(s).replace(/[\\/:*?"<>|\s]+/g, "_"); }
async function newestIn(dir, pred) {
  const es = await readdir(dir).catch(() => []);
  let best = null, bestT = -1;
  for (const e of es) { if (!pred(e)) continue; const t = (await stat(path.join(dir, e))).mtimeMs; if (t > bestT) { bestT = t; best = e; } }
  return best ? path.join(dir, best) : null;
}
async function newestDir(dir, pred) {
  const es = await readdir(dir).catch(() => []);
  let best = null, bestT = -1;
  for (const e of es) { if (!pred(e)) continue; const s = await stat(path.join(dir, e)); if (s.isDirectory() && s.mtimeMs > bestT) { bestT = s.mtimeMs; best = e; } }
  return best;
}

main().catch((e) => { console.error("× " + (e.message || e)); process.exit(1); });
