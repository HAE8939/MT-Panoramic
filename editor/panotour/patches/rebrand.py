# -*- coding: utf-8 -*-
"""项目化 · 阶段4：把编辑器从上游 PanoPath 改头换面为我们自己的 MT-Panoramic。

前置：必须在 localize.py → localize2.py → localize3.py 之后运行（部分规则匹配的是汉化后的中文串）。
定位：纯身份/署名替换，不改任何选择器、id、类名、数据结构与逻辑。

刻意不动的东西（改了会出事或没意义）：
  1. tool.js 里 localStorage 键 'panopath-style-presets-v1' / 'panopath-autosave-v1'
     —— 改名等于让浏览器里已有的样式预设和自动保存历史凭空消失，且用户不可见。
  2. docker-compose.yml / .github/workflows/docker-image.yml 里的 panopath 服务名、
     panopath_data 卷名、illerin/panopath 镜像名 —— 那些指向真实存在的远端产物与数据卷，
     改名只会让卷数据变成孤儿。我们也不走 Docker 部署。
  3. 设置面板的版本徽标 v0.5.20 —— 保留为「引擎版本」，是重放补丁时判断上游基线的依据。
  4. project.json 的 exportedWith 里保留 "based on PanoPath ... MIT"，README.txt 保留引擎署名，
     README.md 保留上游链接与致谢 —— MIT 义务与可追溯性都靠这几处。

升级 PanoPath 的正确姿势（与前三阶段一致）：
  git stash / 丢弃工作区 → git pull → 依次重跑 localize 三脚本 → 再跑本脚本 → git diff --shortstat 核对。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 从脚本自身位置相对推导：panotour/patches/ -> 项目根 -> MT-Panoramic（引擎目录，原 PanoPath）
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MT-Panoramic"))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
F_HTML = os.path.join(BASE, "public", "index.html")
F_TOOL = os.path.join(BASE, "public", "js", "tool.js")
F_SRV = os.path.join(BASE, "server", "index.js")
F_PKG = os.path.join(BASE, "package.json")
F_LOCK = os.path.join(BASE, "package-lock.json")
F_README = os.path.join(BASE, "README.md")

# 产品 logo：唯一真源在我们这一层（随根仓库纳管），脚本负责把它装配成两种形态
F_LOGO_SRC = os.path.join(ROOT, "panotour", "assets", "mt-panoramic.svg")
F_LOGO_OUT = os.path.join(BASE, "public", "img", "mt-panoramic.svg")
LOGO_ACCENT = "#B7472A"   # favicon 形态无法继承 currentColor，写死强调色

# ── 身份常量（以后改名/改版本只动这里）────────────────────────────────
TOOL_NAME = "MT-Panoramic"
TOOL_SLUG = "mt-panoramic"
TOOL_VER = "1.0"
TOOL_CN = "全景导览制作线"
UPSTREAM = "PanoPath"
UP_VER = "0.5.20"


def load(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def save(p, s):
    # 与 localize 三脚本一致：平台默认换行（Windows 下写 CRLF）。
    # 索引里由 core.autocrlf 归一为 LF，故工作区换行符差异不影响 git diff 计数。
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def apply(path, rules, tag):
    if not os.path.exists(path):
        print("× 文件不存在，跳过：%s" % path)
        return
    s = load(path)
    orig = s
    miss = []
    hit = 0
    for old, new in rules:
        c = s.count(old)
        if c == 0:
            miss.append(old)
        else:
            s = s.replace(old, new)
            hit += c
    if s != orig:
        save(path, s)
    print("[%s] 替换 %d 处；未命中 %d 条（未命中 = 已应用过或上游改行）" % (tag, hit, len(miss)))
    for m in miss:
        print("    MISS %r" % m[:70])


# ── 产品 logo 装配 ───────────────────────────────────────────────────
# 源图形由两条多边形笔画构成，笔画仅约 5 单位（在 20px 高度下折算 ~1.1px，属发丝线）。
# 加粗不改图形本身、也不放大尺寸：给它描一圈与自身同色的边，让笔画整体变厚。
LOGO_STROKE = 8       # 单位与 viewBox 同尺度；8 ≈ 笔画由 ~1.1px 增到 ~2.8px
LOGO_BOLD_CSS = ("fill: currentColor;\n"
                 "        stroke: currentColor;\n"
                 "        stroke-width: %d;\n"
                 "        stroke-linejoin: round;" % LOGO_STROKE)


def bolden(s):
    """把 .cls-1 的 fill 规则扩成 fill + 同色描边。源资产保持原样不动，加粗只发生在装配环节。"""
    if "fill: currentColor;" in s:
        return s.replace("fill: currentColor;", LOGO_BOLD_CSS, 1)
    if "fill:currentColor" in s:
        return s.replace("fill:currentColor", LOGO_BOLD_CSS, 1)
    sys.exit("× logo 源文件的填色写法与预期不符，请检查：%s" % F_LOGO_SRC)


def logo_inline_mark():
    """页头用内联形态：源 SVG 的 fill 是 currentColor，只有内联才会继承 .logo 的文字色
    （作为 <img src> 引用时 currentColor 退化成黑色，压在暗底顶栏上会看不见）。"""
    if not os.path.exists(F_LOGO_SRC):
        sys.exit("× 找不到产品 logo 源文件：%s" % F_LOGO_SRC)
    s = bolden(load(F_LOGO_SRC))
    i = s.find("<svg ")
    if i < 0:
        sys.exit("× logo 源文件里没有 <svg> 标签：%s" % F_LOGO_SRC)
    s = s[i:]
    j = s.find(">")
    return s[:j] + ' width="21" height="20" style="vertical-align:-3px"' + s[j:]


def install_logo_asset():
    """标签页图标形态：favicon 由浏览器独立渲染、不继承颜色，所以把 currentColor 写死成强调色。"""
    if not os.path.exists(F_LOGO_SRC):
        sys.exit("× 找不到产品 logo 源文件：%s" % F_LOGO_SRC)
    os.makedirs(os.path.dirname(F_LOGO_OUT), exist_ok=True)
    s = bolden(load(F_LOGO_SRC)).replace("currentColor", LOGO_ACCENT)
    save(F_LOGO_OUT, s)
    print("[logo] 已装配：内联页头 + favicon（描边加粗 %d 单位，源资产未改）" % LOGO_STROKE)


MARK = logo_inline_mark()

# ── 编辑器 UI ─────────────────────────────────────────────────────────
HTML = [
    ('<html lang="en">', '<html lang="zh-CN">'),
    # 标题与 favicon 合成一条规则：favicon 是「在 viewport 行后插入」，若锚点行本身不被消耗，
    # 重放第二次就会插出两条 <link rel="icon">（2026-09-26 幂等自检实测到）。
    # 与紧随其后的 <title> 合并后，锚点必被替换掉，重放自然幂等。
    ('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
     '  <title>%s</title>' % UPSTREAM,
     '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
     '  <link rel="icon" type="image/svg+xml" href="img/%s.svg">\n'
     '  <title>%s · %s</title>' % (TOOL_SLUG, TOOL_NAME, TOOL_CN)),
    # 外来文字标 ◈ 换成我们自己的产品 logo（图形 + 字标）
    ('<span class="logo">◈ %s</span>' % UPSTREAM,
     '<span class="logo">%s %s</span>' % (MARK, TOOL_NAME)),
    ('从此前导出的 %s 备份 ZIP 恢复数据。' % UPSTREAM,
     '从此前导出的 %s 备份 ZIP 恢复数据。' % TOOL_NAME),
    # 又一处汉化漏网：拖放区的英文提示
    ('<br>JPG · PNG · HEIC supported</div>', '<br>支持 JPG · PNG · HEIC</div>'),
]

# ── 前端脚本（标题/下载文件名；localStorage 键见文件头说明，不改）──────
TOOL = [
    ('   %s - Tool JS' % UPSTREAM, '   %s - Tool JS' % TOOL_NAME),
    ("a.download='panopath-backup-'+ds+'.zip';",
     "a.download='%s-backup-'+ds+'.zip';" % TOOL_SLUG),
    ("'<title>%s 预览</title>" % UPSTREAM, "'<title>%s 预览</title>" % TOOL_NAME),
]

# ── 后端（提示语 / 预览页 / 导出元数据 / README 模板 / 启动日志）────────
SRV = [
    ("ZIP 中未找到 project.json。请上传导出的 %s ZIP。" % UPSTREAM,
     "ZIP 中未找到 project.json。请上传导出的 %s ZIP。" % TOOL_NAME),
    ("exportedWith: '%s by illerin v%s'," % (UPSTREAM, UP_VER),
     "exportedWith: '%s v%s (based on %s %s, MIT)'," % (TOOL_NAME, TOOL_VER, UPSTREAM, UP_VER)),
    ('attachment; filename="panopath-backup-${dateStr}.zip"',
     'attachment; filename="%s-backup-${dateStr}.zip"' % TOOL_SLUG),
    ("// Validate it's a %s backup" % UPSTREAM,
     "// Validate it's a %s backup" % TOOL_NAME),
    # 这条同时补上一处汉化漏网（原版整句英文直接抛给用户）
    ("'Not a valid %s backup ZIP.'" % UPSTREAM,
     "'不是有效的 %s 备份 ZIP。'" % TOOL_NAME),
    ('  <title>%s 预览</title>' % UPSTREAM,
     '  <title>%s 预览</title>' % TOOL_NAME),
    ("    '%s by illerin',\n    '===================',\n    `版本：      ${APP_VERSION}`," % UPSTREAM,
     "    '%s %s',\n    '=====================',\n    `引擎版本：  %s ${APP_VERSION}`," % (TOOL_NAME, TOOL_CN, UPSTREAM)),
    ("它无法再导入 %s 进行后续编辑。" % UPSTREAM,
     "它无法再导入 %s 进行后续编辑。" % TOOL_NAME),
    ("把该 ZIP 导回 %s 继续编辑。" % UPSTREAM,
     "把该 ZIP 导回 %s 继续编辑。" % TOOL_NAME),
    ("console.log(`%s Local Tool running on http://localhost:${PORT}`)" % UPSTREAM,
     "console.log(`%s 编辑器已启动： http://localhost:${PORT}`)" % TOOL_NAME),
]

PKG = [
    ('"name": "panopath",', '"name": "%s",' % TOOL_SLUG),
    ('"description": "Self-hosted PanoPath panorama tour builder",',
     '"description": "%s %s（基于 %s / MIT）",' % (TOOL_NAME, TOOL_CN, UPSTREAM)),
]

LOCK = [
    ('"name": "panopath",', '"name": "%s",' % TOOL_SLUG),
]

README = """# %s · %s

> 竣工实景 / 样板间全景导览的本地制作线。
> 当前版本 v%s · 更新：2026-09-26

## 这是什么

`%s` 是**我们自己的工具名**，不是零改动的使用：它在开源编辑器 [`%s`](https://github.com/illerin/%s)（MIT）之上叠了两层自有资产——

1. `../panotour/patches/` —— 中文本地化 + 项目化替换脚本（`localize.py` → `localize2.py` → `localize3.py` → 本目录 `rebrand.py`），共 397 处文案替换加本阶段的品牌替换。全部幂等，脚本路径由自身位置推导，项目整体搬家不影响。
2. `../panotour/` —— 构建器 `build_tour.py`（切片 → 导出 → 品牌注入两级）与 `brands/` 品牌包（设计令牌 + 主题 CSS）。

上游目录仍保持为一个独立 git 仓库，我们的改动提交在本地分支 `mt-panoramic` 上（远端只有作者的 `origin`，**从不推送**）。

## 用法

```bash
# 启动编辑器（中文界面，默认端口 3199）
cd %s && PORT=3199 node server/index.js

# 完整构建一套导览
python ../panotour/build_tour.py --brand gongsheng --project "XX 竣工实景" \\
    "E:/.../pano1.jpg=客厅全景" "E:/.../pano2.jpg=主卧全景"

# 用清单 JSON 带平面图与逐景打点/视角
python ../panotour/build_tour.py --brand gongsheng --project "庭院住宅" \\
    --spec "../示范案例/tour_spec.json"
```

更多约定、已知坑与项目进度见仓库根 `../AGENTS.md`。

## 升级上游基线

```bash
cd %s
git diff --shortstat                 # 先确认当前工作区状态
git checkout -- . && git pull        # 丢弃工作区改动并取上游（补丁已有 commit 兜底）
python ../panotour/patches/localize.py
python ../panotour/patches/localize2.py
python ../panotour/patches/localize3.py
python ../panotour/patches/rebrand.py
git diff --shortstat                 # 核对替换数是否仍与预期一致
```

若上游改动了我们替换过的文案，对应脚本会打印 `MISS` 行——那是需要人工补规则的信号，不是报错。

## 许可与致谢

- 引擎：`%s` © illerin，MIT License（见 `LICENSE`）。允许商用、修改与闭源再分发，义务为保留版权声明与许可全文——故 `LICENSE` 文件与各处「based on %s」署名不得删除。
- 本目录内被打包进导出物的 `public/js/marzipano.js`（运行时从 CDN 取得，未入库）为 Google 的 **Apache License 2.0**，其文件头许可声明须原样保留。
- 导出物里的 3D 全景浏览能力同样来自 Marzipano。
""" % (TOOL_NAME, TOOL_CN, TOOL_VER, TOOL_NAME, UPSTREAM, UPSTREAM, os.path.basename(BASE), os.path.basename(BASE), UPSTREAM, UPSTREAM)


def write_readme():
    if os.path.exists(F_README):
        cur = load(F_README)
        if cur == README:
            print("[README] 已是本版本，跳过")
            return
        # 原版上游 README 已在 commit aa8861b 里，可随时 git show 取回
    save(F_README, README)
    print("[README] 已重写为 %s 自有说明（原版可 git show aa8861b:README.md 取回）" % TOOL_NAME)


# ── 部署残留体检（本项目刻意不走 Docker：2026-09-26 HAE 决定，保持简约克制）────
DEPLOY_ARTIFACTS = ["Dockerfile", "docker-compose.yml", ".github"]


def check_deploy_artifacts():
    """上游仓库自带 Dockerfile / compose / 镜像构建 CI，我们全部不需要也不使用。
    这三个已在引擎仓库的 mt-panoramic 分支上删除。此处只**检测并提示**、不代删——
    删除文件是显式动作，不该由一个每次重放的脚本悄悄替你做。"""
    back = [p for p in DEPLOY_ARTIFACTS if os.path.exists(os.path.join(BASE, p))]
    if back:
        print("[prune] 检测到无用的部署文件：%s" % "、".join(back))
        print("        本项目不使用 Docker。请把上述文件删除（走回收站，勿用 rm/del 直删）")
        print("        后在引擎仓库执行 git add -A 记录删除，再 commit。")
    else:
        print("[prune] 无 Docker 部署残留 ✓（本项目只走 `node server/index.js` + HTTP API）")


if __name__ == "__main__":
    install_logo_asset()
    apply(F_HTML, HTML, "index.html")
    apply(F_TOOL, TOOL, "tool.js")
    apply(F_SRV, SRV, "server/index.js")
    apply(F_PKG, PKG, "package.json")
    apply(F_LOCK, LOCK, "package-lock")
    write_readme()
    check_deploy_artifacts()
    print("· 完成：%s v%s（基于 %s %s）" % (TOOL_NAME, TOOL_VER, UPSTREAM, UP_VER))
