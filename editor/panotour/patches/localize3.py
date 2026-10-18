# -*- coding: utf-8 -*-
"""深度汉化 · 阶段3：server/index.js（后端提示 + 预览页 + 导出漫游页模板 + README），及 index.html 指南针 N→北。"""
import sys, io, os

# 从脚本自身位置相对推导：panotour/patches/ -> 项目根 -> MT-Panoramic（引擎目录，原 PanoPath）
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MT-Panoramic"))
F_SRV  = BASE + r"\server\index.js"
F_HTML = BASE + r"\public\index.html"

def load(p):
    with io.open(p, "r", encoding="utf-8") as f: return f.read()
def save(p, s):
    with io.open(p, "w", encoding="utf-8") as f: f.write(s)
def _a(x): return x.encode("ascii","ignore").decode("ascii")
def apply(path, rules, tag):
    s = load(path); miss = []
    for old, new in rules:
        c = s.count(old)
        if c == 0: miss.append(old)
        else: s = s.replace(old, new)
    save(path, s)
    for m in miss: print("MISS [%s] %r" % (tag, _a(m)[:80]))
    print("[%s] done, rules=%d misses=%d" % (tag, len(rules), len(miss)))

# ── 后端面向用户提示（res.json error / 会被前端 alert 或 throw 暴露）──────────────
SRV_MSG = [
    ("{ error: 'No file uploaded' }", "{ error: '未上传文件' }"),
    ("{ error: 'No file uploaded.' }", "{ error: '未上传文件。' }"),
    ("'Failed to process: ' + err.message", "'处理失败：' + err.message"),
    ("'Could not read image dimensions'", "'无法读取图像尺寸'"),
    ("error: 'No project.json found in ZIP. Make sure you upload an exported PanoPath ZIP.'",
     "error: 'ZIP 中未找到 project.json。请上传导出的 PanoPath ZIP。'"),
    ("'Project contains an invalid scene id.'", "'项目含有无效的场景 id。'"),
    ("'Import failed: ' + err.message", "'导入失败：' + err.message"),
    ("{ error: 'name and project required' }", "{ error: '缺少 name 或 project' }"),
    ("{ error: 'Not found' }", "{ error: '未找到' }"),
    ("{ error: 'presets must be an array' }", "{ error: 'presets 必须为数组' }"),
    ("{ error: 'No scenes' }", "{ error: '没有场景' }"),
    ("{ error: 'Invalid scene id' }", "{ error: '无效的场景 id' }"),
    ("{ error: 'Scene not found' }", "{ error: '未找到场景' }"),
    ("{ error: 'degrees must be 0, 90, 180, or 270' }", "{ error: '旋转角度必须为 0、90、180 或 270' }"),
    ("{ error: 'No image found for this scene' }", "{ error: '未找到该场景的图片' }"),
    ("'Rotation failed: ' + err.message", "'旋转失败：' + err.message"),
    ("error: 'No source image found for this scene. Re-import the original file to enable projection switching.'",
     "error: '未找到该场景的原图。请重新导入原始文件以启用投影切换。'"),
    ("{ error: 'projection must be flat, cube, or fisheye' }", "{ error: 'projection 必须为 flat、cube 或 fisheye' }"),
    ("'Reprocess failed: ' + err.message", "'重新处理失败：' + err.message"),
    ("'Preview expired or not found'", "'预览已过期或不存在'"),
    ("res.status(500).json({ error: 'Failed to read storage stats: ' + err.message })",
     "res.status(500).json({ error: '读取存储信息失败：' + err.message })"),
    ("res.status(500).json({ error: 'Failed to clean orphan tiles: ' + err.message })",
     "res.status(500).json({ error: '清理孤立瓦片失败：' + err.message })"),
    # 导入校验告警（前端 loadProject 以 alert 暴露）
    ("'Duplicate scene IDs found: '", "'发现重复的场景 ID：'"),
    ("'Scenes missing tile files: '", "'以下场景缺少瓦片文件：'"),
    ("'Tile folders not referenced by project.json: '", "'未被 project.json 引用的瓦片目录：'"),
]

# ── 预览页（编辑器「预览漫游」打开的顶层页）───────────────────────────────────
SRV_PREVIEW = [
    ("<title>PanoPath Preview</title>", "<title>PanoPath 预览</title>"),
    (">Desktop</button>", ">桌面</button>"),
    (">Phone</button>", ">手机</button>"),
    (">Live preview from current editor state</span>", ">基于当前编辑器状态的实时预览</span>"),
]

# ── 导出漫游页（客户最终浏览的成品页）─────────────────────────────────────────
SRV_TOUR = [
    (">Panorama Tour</title>", ">全景漫游</title>"),
    ("class=\"plan-controls-title\">Plan</span>", "class=\"plan-controls-title\">平面图</span>"),
    ("title=\"Toggle dots\">Dots</button>", "title=\"切换标点\">标点</button>"),
    ("title=\"Toggle directional arrows\">Arrows</button>", "title=\"切换方向箭头\">箭头</button>"),
    ("id=\"plan-maximize-btn\" title=\"Maximise\"", "id=\"plan-maximize-btn\" title=\"最大化\""),
    ("id=\"plan-minimize-btn\" title=\"Minimise\"", "id=\"plan-minimize-btn\" title=\"最小化\""),
    ("id=\"plan-img\" src=\"plan.${planExt}\" alt=\"Plan\"", "id=\"plan-img\" src=\"plan.${planExt}\" alt=\"平面图\""),
    ("id=\"plan-restore-btn\" hidden>Plan &#9652;</button>", "id=\"plan-restore-btn\" hidden>平面图 &#9652;</button>"),
    ("<span id=\"scene-title\">Loading...</span>", "<span id=\"scene-title\">加载中…</span>"),
    ("id=\"scene-list-toggle\">&#9776; Scenes</button>", "id=\"scene-list-toggle\">&#9776; 场景</button>"),
    ("id=\"fullscreen-btn\" title=\"Fullscreen\"", "id=\"fullscreen-btn\" title=\"全屏\""),
    ("id=\"zoom-in-btn\" title=\"Zoom in\"", "id=\"zoom-in-btn\" title=\"放大\""),
    ("id=\"zoom-out-btn\" title=\"Zoom out\"", "id=\"zoom-out-btn\" title=\"缩小\""),
    ("class=\"compass-north-label\">N</text>", "class=\"compass-north-label\">北</text>"),
    ("font-weight=\"700\">N</text>", "font-weight=\"700\">北</text>"),
    ("settings.title||'Panorama Tour'", "settings.title||'全景漫游'"),
]

# ── 导出包内 README.txt ────────────────────────────────────────────────────────
SRV_README = [
    ("'Version:     ${APP_VERSION}'", "'版本：      ${APP_VERSION}'"),
    ("`Version:     ${APP_VERSION}`", "`版本：      ${APP_VERSION}`"),
    ("`Export type: ${isSlim ? 'Hosting Only' : 'Full Export'}`",
     "`导出类型：  ${isSlim ? '仅托管' : '完整导出'}`"),
    ("`Title:       ${settings.title||'全景漫游'}`", "`标题：      ${settings.title||'全景漫游'}`"),
    ("`Exported:    ${dateStr} at ${timeStr}`", "`导出时间：  ${dateStr} ${timeStr}`"),
    ("`Scenes:      ${(scenes||[]).length}`", "`场景数量：  ${(scenes||[]).length}`"),
    ("'Hosting',", "'托管部署',"),
    ("'Upload all files to any static web server and open index.html.',",
     "'将全部文件上传到任意静态 Web 服务器，然后打开 index.html 即可。',"),
    ("'All assets including marzipano.js are bundled — no internet connection required.',",
     "'包含 marzipano.js 在内的全部资源均已打包——无需联网。',"),
    ("'Re-editing',", "'再次编辑',"),
    ("'This is a Hosting Only export. It does not include source images or project.json.'",
     "'此为「仅托管」导出，不包含原图与 project.json。'"),
    ("'It cannot be re-imported into PanoPath for future editing.'",
     "'它无法再导入 PanoPath 进行后续编辑。'"),
    ("'To retain editing capability, use Full Export instead.'",
     "'如需保留可编辑能力，请改用「完整导出」。'"),
    ("'This is a Full Export. Import the ZIP back into PanoPath using Project -> Import ZIP to continue editing.'",
     "'此为「完整导出」。可用“项目 -> 导入 ZIP”把该 ZIP 导回 PanoPath 继续编辑。'"),
    ("(s.name||('Scene '+(i+1)))", "(s.name||('场景 '+(i+1)))"),
    ("toLocaleDateString('en-GB',", "toLocaleDateString('zh-CN',"),
    ("toLocaleTimeString('en-GB',", "toLocaleTimeString('zh-CN',"),
]

HTML_COMPASS = [
    ("class=\"compass-north-label\">N</text>", "class=\"compass-north-label\">北</text>"),
    ("font-weight=\"700\">N</text>", "font-weight=\"700\">北</text>"),
]

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "srv"
    if stage == "srv":
        for rules, tag in [(SRV_MSG,"srv-msg"),(SRV_PREVIEW,"srv-preview"),(SRV_TOUR,"srv-tour"),(SRV_README,"srv-readme")]:
            apply(F_SRV, rules, tag)
    elif stage == "compass":
        apply(F_HTML, HTML_COMPASS, "html-compass")
        apply(F_SRV,  [("class=\"compass-north-label\">N</text>","class=\"compass-north-label\">北</text>"),
                       ("font-weight=\"700\">N</text>","font-weight=\"700\">北</text>")], "srv-compass")
    else:
        print("unknown stage", stage)
