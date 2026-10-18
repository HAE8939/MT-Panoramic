# 全景编辑器

`editor/` 包含完整的全景编辑与导览制作工具：中文编辑器引擎、切片与导出构建器、品牌包、补丁脚本和示范案例配置。

## 安装

在本目录运行：

```powershell
npm install
python -m pip install -r requirements.txt
```

需要 Node.js 20.9 或更新版本、Python 3.10 或更新版本。首次启动需联网下载 Marzipano 浏览器运行文件。

## 启动编辑器

```powershell
npm start
```

打开 <http://localhost:3199>。编辑器保存的本地工程与切片位于 `MT-Panoramic/tmp/`。

## 构建导览

```powershell
npm run build:tour -- --brand gongsheng --project "庭院住宅" --spec "示范案例/tour_spec.json"
```

构建产物写入 `panotour/dist/`。示范案例需要 10 张原始全景图；这些大文件未包含在仓库中。可以恢复原图到 `示范案例/`，或在 `tour_spec.json` 中调整图片路径。

构建后将 `_web/` 导出目录复制到本项目上一级的 `../catalog/projects/<项目编号>/`，并在 `../catalog/data/projects.json` 登记，即可出现在静态项目归纳页。完整说明见项目根目录 [`catalog/README.md`](../catalog/README.md)。

项目协作与文件管理约定见项目根目录 [`AGENTS.md`](../AGENTS.md)。
