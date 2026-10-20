# MT-Panoramic

全景导览制作与项目展示，由两个清晰分离的部分组成：

- [`editor/`](editor/README.md) — 全景编辑器：场景编辑、导览制作、浏览器预览与网页导出。
- [`catalog/`](catalog/README.md) — 项目归纳页：独立静态站点，统一收录已发布的全景项目，支持搜索、类型筛选与点击浏览。

## 编辑器

在 `editor/` 文件夹安装和启动：

```powershell
cd editor
npm install
python -m pip install -r requirements.txt
npm start
```

打开 <http://localhost:3199>。制作完成后，导出目录可放入 `catalog/projects/<项目编号>/`，再登记到 `catalog/data/projects.json`。

## 新项目一键上线（推荐流程）

把「切片 → 托管版 → 收录 → 封面 → 登记」五步手工活合成一条命令（spec 的 `publish` 块声明项目编号/名称/分类/封面取景，写法见 `scripts/publish-project.mjs` 头部注释）：

```powershell
node scripts/publish-project.mjs --spec <tour_spec.json> --deploy --bucket gsyz-web --ossutil "C:\ossutil.exe"
```

不带 `--deploy` 只做本地收录，核对后再单独跑部署。已收录过、只差重传时用 `--skip-build` 跳过切片。

## 项目归纳页

本地预览：

```powershell
python -m http.server 8125 --directory catalog
```

打开 <http://localhost:8125>。线上发布在官网隐藏路由 <https://gsyzdesign.com/pano>（OSS 网站桶 `pano/` 前缀，不需要服务器端程序）：

```powershell
node scripts/deploy-catalog.mjs --bucket gsyz-web --dry-run
node scripts/deploy-catalog.mjs --bucket gsyz-web --ossutil "C:\ossutil.exe"
```

部署默认**增量**：脚本按内容 MD5 比对 `scripts/.deploy-manifest.json`（上次成功上传的清单），只传新增/变化的对象——上线新项目时老项目的几千个瓦片自动跳过，零改动重跑仅秒级。`--full` 强制全量；清单被删或不可信时退回全量重传一次即可重建。只上传不删除；HTML/JSON/CSS/JS 为 no-cache，收录新项目后重跑即生效。细节见 [`catalog/README.md`](catalog/README.md) 的「部署」。

项目归纳页的完整字段说明、发布方式和视觉系统参考见 [`catalog/README.md`](catalog/README.md)。
