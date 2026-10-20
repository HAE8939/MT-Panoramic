/**
 * 把 catalog/（项目归纳页）部署到阿里云 OSS 网站桶的 pano/ 前缀下。
 *
 * 线上地址：https://gsyzdesign.com/pano （隐藏路由：不进导航、不进 sitemap，
 * 仅通过直接网址访问；按用户 2026-10-20 口径，robots.txt 不屏蔽）。
 *
 * 与 Website 仓库 scripts/deploy-oss-web.mjs 同一套机制，两点差异：
 * 1. 上传源是本仓库的 catalog/，目标 key 带 pano/ 前缀；
 * 2. 缓存策略更激进地保新鲜：HTML 与 json/css/js 一律 no-cache
 *    （归纳页的清单、脚本、样式都要改完即生效，且体积只有 KB 级），
 *    只有图片/视频等二进制走 30 天长缓存。
 *    若日后原地更新某项目的大图素材，同名 key 会被 CDN 缓存最多 30 天，
 *    届时需在 CDN 控制台刷新对应目录，或改用新文件名。
 *
 * 与主站脚本一样只上传、不删除：OSS 上多出来的旧对象不会被清理，
 * 删除项目后如需下线对应文件，请到 OSS 控制台手动处理。
 *
 * 每个 index.html 会额外上传一份无扩展名 key（pano、pano/projects/<编号>），
 * 让 /pano、/pano/projects/<编号> 命中真实对象，不依赖任何回源改写规则。
 * 无扩展名 URL 有个副作用：文档 URL 不带尾斜杠时，页面里的相对路径
 * （assets/…、data/…）会被浏览器解析到域名根下而 404（netlog 实测）。
 * 因此上传 index.html 时会注入 <base href="/pano/">（子目录页对应各自前缀），
 * 该注入只发生在上传内容里，仓库内文件与 `python -m http.server` 本地预览不受影响。
 *
 * 增量上传（默认开启）：维护一份内容清单 scripts/.deploy-manifest.json，
 * 记录每个 OSS 对象上次上传时的内容 MD5 与缓存/类型策略。再次部署时，
 * 只有「本地内容变了」或「策略变了」或「远端从未传过」的对象才会真正上传，
 * 其余全部跳过。这样上线第 2、3……个项目时，已发布项目的海量切片瓦片
 * 不再重传，通常只剩新项目的瓦片 + 几个 HTML/JSON 入口，秒级到十几秒完成。
 * --full 强制全量重传（忽略清单）；--manifest <path> 自定义清单位置。
 * 清单是本地部署状态、可安全删除（删了就退回全量传一次）；已加入 .gitignore。
 *
 * 用法：
 *   node scripts/deploy-catalog.mjs --bucket gsyz-web --dry-run
 *   node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\ossutil.exe"
 *   node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\ossutil.exe" --full
 */
import { readdir, readFile, writeFile, mkdtemp, rm, mkdir, rename } from "node:fs/promises";
import { tmpdir } from "node:os";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CATALOG = path.join(ROOT, "catalog");
const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const BUCKET = arg("bucket", "");
const PREFIX = arg("prefix", "pano");
const OSSUTIL = arg("ossutil", "ossutil");
const DRY = args.includes("--dry-run");
const FULL = args.includes("--full");
const MANIFEST_PATH = path.resolve(ROOT, arg("manifest", "scripts/.deploy-manifest.json"));

if (!BUCKET && !DRY) { console.error("必须指定 --bucket <网站桶名>，如 gsyz-web"); process.exit(2); }
if (PREFIX.startsWith("/") || PREFIX.endsWith("/") || !PREFIX) {
  console.error("prefix 不能以斜杠开头或结尾"); process.exit(2);
}

const MIME = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".gif": "image/gif", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2",
  ".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject", ".txt": "text/plain; charset=utf-8", ".xml": "application/xml; charset=utf-8",
  ".mp4": "video/mp4", ".webm": "video/webm", ".md": "text/plain; charset=utf-8",
};

async function walk(dir, base = "") {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const rel = base ? `${base}/${entry.name}` : entry.name;
    if (entry.isDirectory()) out.push(...await walk(path.join(dir, entry.name), rel));
    else out.push(rel);
  }
  return out;
}

const files = (await walk(CATALOG)).filter((rel) => {
  const base = path.basename(rel);
  // 内部协作文件不上线：仓库说明与点位占位文件不该变成公开 URL。
  return base !== "README.md" && !base.startsWith(".");
});
if (!files.length) { console.error("catalog/ 内没有可上传的文件"); process.exit(3); }

/**
 * 缓存策略：文本类（HTML/JSON/CSS/JS 及无扩展名目录页）一律 no-cache，
 * 保证收录新项目后重跑脚本即全站生效，无需 CDN 刷新；二进制素材长缓存。
 */
function policy(key) {
  const ext = path.extname(key).toLowerCase();
  const isTextish = ext === ".html" || ext === ".json" || ext === ".css" || ext === ".js" || !ext;
  if (isTextish) return { type: ext === ".html" || !ext ? MIME[".html"] : MIME[ext] || "application/octet-stream", cache: "no-cache" };
  return { type: MIME[ext] || "application/octet-stream", cache: "public, max-age=2592000" };
}

// 内容解析：index.html 走「注入 <base> 的内存副本」，其余文件直接读磁盘。
// 上传对象的内容 = 解析后的内容，清单哈希也必须按这个内容算，二者才一致。
// 同一 src 可能对应两个 key（原路径 + 无扩展名副本），内容解析只做一次。
const patchedCache = new Map();
async function patchedIndexHtml(src) {
  if (!patchedCache.has(src)) {
    const dir = src === "index.html" ? "" : src.slice(0, src.length - "index.html".length);
    const baseHref = `/${PREFIX}/${dir}`.replace(/\/+$/, "") + "/";
    const html = await readFile(path.join(CATALOG, src), "utf8");
    let patched;
    if (/<base\s/i.test(html)) {
      patched = html; // 导出物自带 <base> 时尊重原值，不叠加
    } else if (/<head(\s[^>]*)?>/i.test(html)) {
      patched = html.replace(/<head(\s[^>]*)?>/i, (m) => `${m}\n  <base href="${baseHref}">`);
    } else {
      patched = `<base href="${baseHref}">\n${html}`;
    }
    patchedCache.set(src, patched);
  }
  return patchedCache.get(src);
}
async function contentOf(src) {
  return src.endsWith("index.html")
    ? Buffer.from(await patchedIndexHtml(src), "utf8")
    : await readFile(path.join(CATALOG, src));
}
const md5 = (buf) => createHash("md5").update(buf).digest("hex");

// 组装上传清单：原文件 + 目录页的「无扩展名」副本，并为每个对象解析策略与内容哈希
const plan = [];
for (const rel of files) {
  const posix = rel.split(path.sep).join("/");
  const entries = [{ src: posix, key: `${PREFIX}/${posix}` }];
  if (posix === "index.html" || posix.endsWith("/index.html")) {
    const dirKey = posix === "index.html"
      ? PREFIX
      : `${PREFIX}/${posix.slice(0, -"index.html".length).replace(/\/$/, "")}`;
    // 只补无扩展名的一份；不要造以 / 结尾的 key——OSS 开启静态网站托管后
    // 会用自身首页解析接管所有尾斜杠请求，同名对象被完全忽略（见 Website docs/12）。
    entries.push({ src: posix, key: dirKey });
  }
  for (const e of entries) {
    const pol = policy(e.key);
    plan.push({ ...e, type: pol.type, cache: pol.cache });
  }
}

const target = (key) => `oss://${BUCKET}/${key}`;
const run = (argv) => new Promise((resolve, reject) => {
  const child = spawn(OSSUTIL, argv, { stdio: ["ignore", "pipe", "pipe"], shell: false });
  let err = "";
  child.stderr.on("data", (d) => { err += d.toString(); });
  child.on("close", (code) => (code === 0 ? resolve() : reject(new Error(err.slice(0, 200) || `退出码 ${code}`))));
});

// 读取上次的部署清单（key -> {hash,type,cache}）；--full 或清单缺失则视为全量
let manifest = {};
if (!FULL) {
  try { manifest = JSON.parse(await readFile(MANIFEST_PATH, "utf8")); }
  catch { manifest = {}; }
} else { manifest = {}; }
const manifestKey = (k) => k; // 前缀已含在 key 内，桶+前缀组合天然隔离

console.log(`catalog/ 内 ${files.length} 个文件，加上目录页副本共 ${plan.length} 个 OSS 对象`);
console.log(`目标前缀：oss://${BUCKET}/${PREFIX}/`);
console.log(FULL ? "模式：全量重传（--full）" : (Object.keys(manifest).length ? "模式：增量（按内容清单跳过未变对象）" : "模式：首次，无清单 → 全量并建立清单"));

// 预计算内容哈希，算出待传集合（DRY 与实际上传共用同一判定，dry-run 才可信）
const CHUNK = 64;
for (let i = 0; i < plan.length; i += CHUNK) {
  await Promise.all(plan.slice(i, i + CHUNK).map(async (item) => {
    item.hash = md5(await contentOf(item.src));
    const prev = manifest[manifestKey(item.key)];
    item.skip = !!(prev && prev.hash === item.hash && prev.type === item.type && prev.cache === item.cache);
  }));
}
const todo = plan.filter((p) => !p.skip);
const skipped = plan.length - todo.length;
console.log(`待上传 ${todo.length} 个，跳过未变化 ${skipped} 个\n`);

if (DRY) {
  todo.slice(0, 12).forEach((p) => console.log(`  ${p.src.padEnd(40)} → ${target(p.key)}`));
  if (todo.length > 12) console.log(`  … 待上传共 ${todo.length} 个`);
  console.log(`\n[dry-run] 未执行。跳过 ${skipped} 个未变化对象；无扩展名副本约 ${plan.length - files.length} 个。`);
  process.exit(0);
}

// 只有真正要传的 index.html 才写临时文件；纯跳过的项目完全不再读改
const tmpRoot = await mkdtemp(path.join(tmpdir(), "pano-deploy-"));
const staged = new Map();
async function localFileFor(src) {
  if (!src.endsWith("index.html")) return path.join(CATALOG, src);
  if (!staged.has(src)) {
    const dest = path.join(tmpRoot, src.replace(/\//g, "__"));
    await writeFile(dest, await patchedIndexHtml(src));
    staged.set(src, dest);
  }
  return staged.get(src);
}

let ok = 0; const failed = [];
const NEW_MANIFEST = { ...manifest };
const CONCURRENCY = 8;
let cursor = 0;
async function worker() {
  while (cursor < todo.length) {
    const item = todo[cursor++];
    const local = await localFileFor(item.src);
    try {
      await run(["cp", "-f", "--content-type", item.type, "--cache-control", item.cache, local, target(item.key)]);
      ok += 1;
      NEW_MANIFEST[manifestKey(item.key)] = { hash: item.hash, type: item.type, cache: item.cache };
      if (ok % 20 === 0) console.log(`  已上传 ${ok}/${todo.length}`);
    } catch (err) {
      failed.push(`${item.key} :: ${err.message}`);
    }
  }
}
await Promise.all(Array.from({ length: CONCURRENCY }, worker));

console.log(`\n上传成功 ${ok} / ${todo.length}（本次跳过 ${skipped} 个未变化对象）`);
await rm(tmpRoot, { recursive: true, force: true });
if (failed.length) {
  failed.slice(0, 15).forEach((f) => console.error("  !!", f));
  // 有失败就不落清单，下次这些对象仍会重试（已成功写入 NEW_MANIFEST 的不丢，但保守起见整体不写，避免半成品清单）
  console.error("因存在上传失败，本次未更新部署清单，重跑将重试失败对象。");
  process.exit(4);
}
// 全部成功 → 原子写回清单
try {
  await mkdir(path.dirname(MANIFEST_PATH), { recursive: true });
  const tmpMf = MANIFEST_PATH + ".tmp";
  await writeFile(tmpMf, JSON.stringify(NEW_MANIFEST, null, 0));
  await rename(tmpMf, MANIFEST_PATH);
  console.log(`部署清单已更新：${path.relative(ROOT, MANIFEST_PATH)}（共 ${Object.keys(NEW_MANIFEST).length} 条）`);
} catch (err) {
  console.warn("! 清单写入失败（不影响本次上线，下次会退回全量）：", err.message);
}
console.log("完成。HTML/JSON/CSS/JS 为 no-cache，无需刷新 CDN 即生效。");
