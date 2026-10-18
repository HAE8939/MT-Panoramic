# -*- coding: utf-8 -*-
"""项目化 · 阶段5：编辑器界面配色换成 HAE 设计系统令牌（暗底 · 美术馆黑版）。

为什么改：上游 tool.css 的强调色是外来品红 #e94560、底色是冷蓝 navy（#16213e/#0f3460），
与《HAE Creator Design System V0.1》冲突。导出物那侧已由 brands/<key>.theme.css 覆盖，
本脚本管的是**编辑器本身**——我们每天盯十几个小时的界面。

做法：只做「色值替换」，不改任何选择器、形制、布局与逻辑。
  - 编辑器 chrome 全部色值 → 暖色暗底 ramp + 铁锈红强调
  - 强调色作为**文字**时（color:#e94560，共 10+ 处）用提亮档 #E07A52，
    因为 #B7472A 是按浅纸底验证过的（白字/accent 5.01），压在暗底上对比度不够。
    #E07A52 是本脚本引入的「accent-on-dark」候选档，需 HAE 决定是否收进设计系统。

刻意不改（改了会影响客户交付物或属于数据默认值）：
  - server/index.js 里的全部色值（那是导出物 style.css 模板，归品牌主题层管）
  - tool.js / index.html 里 btn3BgColor:'#e94560' 等 settings 默认值（会进导出配置）
  - tool.css 里样式预设面板的色板数据（#27ae60/#2196F3/#CE93D8/#FFCC80 等一次性色值）
  - 中性灰阶 #aaa/#888/#666/#444（暖底上仍成立，避免无谓改动面）

顺序：localize.py → localize2.py → localize3.py → rebrand.py → 本脚本
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MT-Panoramic"))
F_CSS = os.path.join(BASE, "public", "css", "tool.css")
F_TOOL = os.path.join(BASE, "public", "js", "tool.js")
F_HTML = os.path.join(BASE, "public", "index.html")

# ── 设计令牌（暗底 ramp；纸/墨/强调直引 V0.1，暗底 ramp 为按色相推导）──────
BG      = "#16130F"   # 美术馆黑（V0.1 允许暗底）
PANEL   = "#1F1B16"
PANEL_2 = "#241F18"
PANEL_3 = "#2E2820"
RAISE   = "#1B1712"
DEEP    = "#0E0C09"
FIELD   = "#2A241C"
LINE    = "#332C23"
LINE_2  = "#3A332A"
LINE_3  = "#3A3126"
PAPER   = "#F4F1EA"   # 纸
PAPER_2 = "#EDE8DF"
MUTED   = "#A9A29A"   # 暗底次级文字
ACC     = "#B7472A"   # 铁锈红（V0.1）
ACC_DEEP= "#7A2E1A"   # 深铁锈（V0.1）
ACC_TXT = "#E07A52"   # accent-on-dark 候选档（文字用）
GOLD    = "#C9A469"   # 共生营造 logo 金，用于拖放目标指示


def load(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def save(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def apply(path, rules, tag):
    if not os.path.exists(path):
        print("× 文件不存在，跳过：%s" % path)
        return 0
    s = load(path)
    orig = s
    total = 0
    miss = []
    for old, new, *opt in rules:
        c = s.count(old)
        total += c
        if c:
            s = s.replace(old, new)
        elif not (opt and opt[0]):
            # optional=True 的规则是同一颜色的「有空格/无空格」兜底写法，未命中属正常
            miss.append(old)
    if s != orig:
        save(path, s)
    print("[%s] 替换 %d 处" % (tag, total))
    # 整文件 0 命中 = 已经应用过（幂等），此时逐条报 MISS 只是噪音；
    # 只有部分命中部分落空时，MISS 才是「上游改了配色」的真信号。
    if total:
        for m in miss:
            print("    MISS [%s] %r" % (tag, m[:60]))
    return total


# ── tool.css：按「先具体后通用」排序，避免文字档被通用档吃掉 ──────────────
CSS_RULES = [
    # 强调色作为文字 → 提亮档
    ("color:#e94560", "color:" + ACC_TXT),
    ("color: #e94560", "color: " + ACC_TXT, True),
    # 冷 navy ramp → 暖暗底 ramp
    ("#1a1a2e", BG),
    ("#0a0a1a", DEEP),
    ("#12192e", RAISE),
    ("#16213e", PANEL),
    ("#1a2744", FIELD),
    ("#1a2a4a", PANEL_2),
    ("#2a2a4a", PANEL_3),
    ("#1e3060", LINE_3),
    ("#2a3a5a", LINE_2),
    ("#0f3460", LINE),
    # 冷灰蓝文字 → 暖次级 / 纸
    ("#8aa0bf", MUTED),
    ("rgba(138, 160, 191", "rgba(169, 162, 154", True),
    ("rgba(138,160,191", "rgba(169,162,154"),
    ("#d8e2f2", PAPER_2),
    ("#e0e0e0", PAPER),
    # 强调色（描边/底色/填充）
    ("#c73652", ACC_DEEP),
    ("#e94560", ACC),
    ("rgba(233, 69, 96", "rgba(183, 71, 42", True),
    ("rgba(233,69,96", "rgba(183, 71, 42"),
    # 拖放目标指示：冷蓝 → logo 金
    ("#45b6ff", GOLD),
    ("rgba(69, 182, 255", "rgba(201, 164, 105", True),
    ("rgba(69,182,255", "rgba(201, 164, 105"),
]

# ── tool.js：只改运行期写进界面的 chrome 内联样式，不碰 settings 默认值 ────
TOOL_RULES = [
    ("status.style.color='#e94560'", "status.style.color='" + ACC_TXT + "'"),
    ("$('#backup-status').style.color = '#e94560'", "$('#backup-status').style.color = '" + ACC_TXT + "'"),
    ("border:1px solid #e94560", "border:1px solid " + ACC),
    ('<span style="color:#e94560;font-size:12px">', '<span style="color:' + ACC_TXT + ';font-size:12px">'),
]

# ── index.html：编辑器画布上的指北针针叶（不是导出物，也不是 settings 默认值）──
HTML_RULES = [
    ('<polygon points="30,6 34,30 30,26 26,30" fill="#e94560"/>',
     '<polygon points="30,6 34,30 30,26 26,30" fill="' + ACC + '"/>'),
    ('<polygon points="30,8 40,32 30,27 20,32" fill="#e94560"/>',
     '<polygon points="30,8 40,32 30,27 20,32" fill="' + ACC + '"/>'),
    ('style="text-align:left;font-size:13px;color:#e94560;',
     'style="text-align:left;font-size:13px;color:' + ACC_TXT + ';'),
]


# ── WCAG 对比度自检（交付前不靠肉眼判断）────────────────────────────
def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def contrast(h1, h2):
    def rgb(h):
        h = h.lstrip("#")
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    a, b = [_lin(x) for x in rgb(h1)], [_lin(x) for x in rgb(h2)]
    L1, L2 = 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2], 0.2126 * b[0] + 0.7152 * b[1] + 0.0722 * b[2]
    hi, lo = max(L1, L2), min(L1, L2)
    return round((hi + 0.05) / (lo + 0.05), 2)


CHECKS = [
    ("正文 纸/底", PAPER, BG, 4.5),
    ("次级 暖灰/面板", MUTED, PANEL, 4.5),
    ("强调文字 accent-on-dark/底", ACC_TXT, BG, 4.5),
    ("强调文字 accent-on-dark/面板", ACC_TXT, PANEL, 4.5),
    ("白字/强调按钮底", "#FFFFFF", ACC, 4.5),
    ("描边 线/面板", LINE, PANEL, 1.0),
]

if __name__ == "__main__":
    n = 0
    n += apply(F_CSS, CSS_RULES, "tool.css")
    n += apply(F_TOOL, TOOL_RULES, "tool.js")
    n += apply(F_HTML, HTML_RULES, "index.html")
    print("· 编辑器色值替换合计 %d 处%s" % (n, "（重跑 = 0 处，说明已应用）" if n == 0 else ""))
    print("· WCAG 对比度自检：")
    bad = 0
    for name, fg, bg, need in CHECKS:
        r = contrast(fg, bg)
        ok = "✓" if r >= need else "×"
        if r < need:
            bad += 1
        print("    %s %-26s %s on %s = %.2f（需 ≥%.1f）" % (ok, name, fg, bg, r, need))
    print("· 全部达标" if bad == 0 else "· 有 %d 项不达标，需回看令牌" % bad)
