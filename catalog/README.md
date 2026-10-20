# 项目归纳页

`catalog/` 是独立的静态站点，与全景编辑器分开放置。它使用纯 HTML、CSS、JavaScript 和 JSON，不依赖数据库或服务端；可以单独部署到任意静态网页托管服务。

## 本地预览

在项目根目录运行：

```powershell
python -m http.server 8125 --directory catalog
```

然后打开 <http://localhost:8125>。浏览器会读取 `data/projects.json`，因此需要通过 HTTP 服务预览，不要直接双击 `index.html`。

## 收录一个已完成项目

1. 在编辑器中导出完整导览网页。
2. 将 `_web/` 目录中的所有文件复制到 `catalog/projects/<项目编号>/`，确保入口文件位于该目录的 `index.html`。
3. 在 `data/projects.json` 的 `projects` 数组中添加记录：

```json
{
  "id": "courtyard-residence",
  "title": "庭院住宅",
  "category": "全景效果",
  "location": "项目所在地",
  "year": 2026,
  "scenes": 10,
  "description": "庭院、门庭与室内空间的全景漫游。",
  "cover": "assets/covers/courtyard-residence.jpg",
  "href": "projects/courtyard-residence/index.html",
  "tags": ["庭院", "改造"]
}
```

`id` 只作记录识别；`cover` 与 `href` 都相对 `catalog/` 目录填写。封面图放入 `assets/covers/`。`href` 应指向部署目录内的导览网页；项目卡片会打开这个链接。项目数据可按需填写 `location`、`year`、`scenes`、`description` 与 `tags`。

`category` 使用站点固定三分类（2026-10-20 定）：**量房记录**（量房阶段拍摄的现场全景）、**水电记录**（施工过程中水电阶段拍摄的现场全景）、**全景效果**（设计阶段或完工阶段的全景呈现）。这四个筛选项（含「全部」）始终展示，hover 有释义；数据里出现体系外的新分类时会自动追加到筛选行末尾。同一项目在不同阶段多次拍摄时，按每次导出各登记一条记录、分别归类。

首页笔记本全景图 `assets/panorama-hero.png` 是固定主视觉，用来表达全景浏览体验，不属于任何单独项目；项目卡片封面仍由各项目的 `cover` 字段指定。页头页脚与浏览器标签的品牌（logo、名称、favicon）跟随主站「共生营造空间设计」，资源在 `assets/logo-dark.svg` 与 `assets/favicon*`，取自主站仓库 `public/`；主站换标时需同步覆盖这三处文件。页尾 CTA 与导航的「前往主站」指向 `/cn`。

目录当前收录：`仁恒·夹城里`（量房初始阶段，20 景，无平面图，导览内用「☰ 场景」菜单切换）。编辑器里的庭院住宅示范资料用于展示页面视觉，不会伪装成已发布项目。

## 部署

归纳页发布在官网的隐藏路由 **https://gsyzdesign.com/pano**（阿里云 OSS 网站桶 `gsyz-web` 的 `pano/` 前缀下）。它不进官网导航、不进 sitemap，仅通过直接网址访问；按 2026-10-20 口径不在 robots.txt 屏蔽。官网仓库不需要任何改动，两边完全独立。

上传用根目录的 `scripts/deploy-catalog.mjs`（与官网仓库的 deploy-oss-web.mjs 同一套机制，只上传不删除）：

```powershell
node scripts/deploy-catalog.mjs --bucket gsyz-web --dry-run
node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\ossutil.exe"
```

部署默认**增量**：脚本在 `scripts/.deploy-manifest.json` 记录每个对象上次成功上传的内容 MD5 与缓存策略，重跑时只上传内容变化（或远端从未传过）的对象——上线新项目时老项目成千上万个瓦片全部跳过，零改动重跑仅秒级。该清单是本地缓存、被 gitignore，删掉即退回全量重建；若怀疑线上与仓库不一致（如有人绕过脚本直接改过 OSS），用 `--full` 强制全量重传一次。清单只在全部对象上传成功时才落盘，中途失败不会留下"半新不旧"的错误基线。

上传结构保持：

```text
pano/
  index.html          （另上传一份无扩展名 key `pano`，保证不带斜杠也能访问）
  assets/
  data/projects.json
  projects/<项目编号>/index.html
```

无扩展名入口（`/pano`、`/pano/projects/<编号>`）不带尾斜杠，相对路径会被浏览器解析到域名根而 404；因此脚本上传各 `index.html` 时会自动注入 `<base href="/pano/…">`（按所在目录），注入只发生在上传内容里，仓库文件与本地预览不受影响。

缓存策略：HTML、JSON、CSS、JS 一律 no-cache，收录新项目后重跑脚本立即生效，不需要刷新 CDN；图片/视频等二进制素材走 30 天长缓存。若日后**原地更新**某项目的大图素材（同名 key），CDN 可能最多 30 天返回旧图，届时在 CDN 控制台刷新对应目录，或改用新文件名。删除项目后 OSS 上的旧文件不会被脚本清理，需手动下线。

## 页面排版

目录页采用中文优先的字体栈，并为正文、辅助信息和移动端阅读分别设置字号与行距。视觉参考可以借鉴本机的 MT-Visual-Language，但页面以实际中文阅读效果为准，不强制套用其中的字号与排版规则。
