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

## 项目归纳页

本地预览：

```powershell
python -m http.server 8125 --directory catalog
```

打开 <http://localhost:8125>。部署时将 `catalog/` 文件夹作为静态站点根目录上传；全景网页和项目清单都会一并发布，不需要服务器端程序。

项目归纳页的完整字段说明、发布方式和视觉系统参考见 [`catalog/README.md`](catalog/README.md)。
