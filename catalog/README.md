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
  "category": "住宅",
  "location": "项目所在地",
  "year": 2026,
  "scenes": 10,
  "description": "庭院、门庭与室内空间的全景漫游。",
  "cover": "assets/covers/courtyard-residence.jpg",
  "href": "projects/courtyard-residence/index.html",
  "tags": ["庭院", "改造"]
}
```

`id` 只作记录识别；`category` 会自动生成筛选项；`cover` 与 `href` 都相对 `catalog/` 目录填写。封面图放入 `assets/covers/`。`href` 应指向部署目录内的导览网页；项目卡片会打开这个链接。项目数据可按需填写 `location`、`year`、`scenes`、`description` 与 `tags`。

首页笔记本全景图 `assets/panorama-hero.png` 是固定主视觉，用来表达全景浏览体验，不属于任何单独项目；项目卡片封面仍由各项目的 `cover` 字段指定。

目录当前没有收录已导出的成品，所以页面先显示清晰的空状态；编辑器里的庭院住宅示范资料用于展示页面视觉，不会伪装成已发布项目。

## 部署

把整个 `catalog/` 目录作为静态站点根目录发布，保留以下结构：

```text
catalog/
  index.html
  assets/
  data/projects.json
  projects/<项目编号>/index.html
```

添加新项目后，将更新后的 `catalog/` 重新部署。筛选和搜索在浏览器中完成，所有导览网页也以静态文件提供。

## 页面排版

目录页采用中文优先的字体栈，并为正文、辅助信息和移动端阅读分别设置字号与行距。视觉参考可以借鉴本机的 MT-Visual-Language，但页面以实际中文阅读效果为准，不强制套用其中的字号与排版规则。
