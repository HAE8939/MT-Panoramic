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
 * 每个目录页 index.html 会额外上传一份无扩展名 key（pano、pano/projects/<编号>），
 * 让 /pano、/pano/projects/<编号> 命中真实对象，不依赖任何回源改写规则。
 *
 * 用法：
 *   node scripts/deploy-catalog.mjs --bucket gsyz-web --dry-run
 *   node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\ossutil.exe"
 */
import { readdir, stat } from "node:fs/promises";
import { spawn } from "node:child_process";
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

// 组装上传清单：原文件 + 目录页的「无扩展名」副本
const plan = [];
for (const rel of files) {
  const posix = rel.split(path.sep).join("/");
  plan.push({ src: posix, key: `${PREFIX}/${posix}` });
  if (posix === "index.html" || posix.endsWith("/index.html")) {
    const dirKey = posix === "index.html"
      ? PREFIX
      : `${PREFIX}/${posix.slice(0, -"index.html".length).replace(/\/$/, "")}`;
    // 只补无扩展名的一份；不要造以 / 结尾的 key——OSS 开启静态网站托管后
    // 会用自身首页解析接管所有尾斜杠请求，同名对象被完全忽略（见 Website docs/12）。
    plan.push({ src: posix, key: dirKey });
  }
}

const target = (key) => `oss://${BUCKET}/${key}`;
const run = (argv) => new Promise((resolve, reject) => {
  const child = spawn(OSSUTIL, argv, { stdio: ["ignore", "pipe", "pipe"], shell: false });
  let err = "";
  child.stderr.on("data", (d) => { err += d.toString(); });
  child.on("close", (code) => (code === 0 ? resolve() : reject(new Error(err.slice(0, 200) || `退出码 ${code}`))));
});

console.log(`catalog/ 内 ${files.length} 个文件，加上目录页副本共 ${plan.length} 个 OSS 对象`);
console.log(`目标前缀：oss://${BUCKET}/${PREFIX}/\n`);
if (DRY) {
  plan.slice(0, 12).forEach((p) => console.log(`  ${p.src.padEnd(40)} → ${target(p.key)}`));
  console.log(`  … 共 ${plan.length} 个`);
  console.log(`\n[dry-run] 未执行。其中无扩展名副本约 ${plan.length - files.length} 个。`);
  process.exit(0);
}

let ok = 0; const failed = [];
const CONCURRENCY = 8;
let cursor = 0;
async function worker() {
  while (cursor < plan.length) {
    const item = plan[cursor++];
    const pol = policy(item.key);
    const local = path.join(CATALOG, item.src);
    const size = (await stat(local)).size;
    try {
      await run(["cp", "-f", "--content-type", pol.type, "--cache-control", pol.cache, local, target(item.key)]);
      ok += 1;
      if (ok % 20 === 0) console.log(`  已上传 ${ok}/${plan.length}`);
    } catch (err) {
      failed.push(`${item.key} :: ${err.message}`);
    }
  }
}
await Promise.all(Array.from({ length: CONCURRENCY }, worker));

console.log(`\n上传成功 ${ok} / ${plan.length}`);
if (failed.length) {
  failed.slice(0, 15).forEach((f) => console.error("  !!", f));
  process.exit(4);
}
console.log("完成。HTML/JSON/CSS/JS 为 no-cache，无需刷新 CDN 即生效。");
