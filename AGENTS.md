# MT-Panoramic 项目协作说明

本仓库包含两个独立部分：`editor/` 是全景编辑与网页导览制作工具；`catalog/` 是静态项目归纳页。请保持两者可分别安装、运行和部署。

## 开发约定

- 先阅读根目录 `README.md` 及对应子目录的 README。
- 编辑器依赖和启动命令见 `editor/README.md`；项目归纳页部署与项目数据格式见 `catalog/README.md`。
- 不提交 `node_modules/`、本地切片、导出缓存或原始高分辨率全景图。
- 项目归纳页数据位于 `catalog/data/projects.json`；导出的成品网页按项目编号放入 `catalog/projects/`。
