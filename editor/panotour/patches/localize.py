# -*- coding: utf-8 -*-
"""深度汉化批量替换脚本（分阶段）。只替换“人可见文本”，不碰结构/id/类名/数据值。"""
import sys, io, os

# 从脚本自身位置相对推导：panotour/patches/ -> 项目根 -> MT-Panoramic（引擎目录，原 PanoPath）
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MT-Panoramic"))
F_HTML = BASE + r"\public\index.html"
F_TOOL = BASE + r"\public\js\tool.js"
F_SRV  = BASE + r"\server\index.js"

# 归一化：源文件里若干处省略号被写成了 cp1252 乱码 'â€¦'（U+00E2 U+20AC U+00A6）
MOJI = "â€¦"
ELL  = "…"

def load(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

def save(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)

def _a(x):
    # ascii-safe preview so a GBK console can't crash the run mid-way (before save)
    return x.encode("ascii", "ignore").decode("ascii")

def apply(path, rules, tag):
    s = load(path)
    total_miss = 0
    for old, new in rules:
        c = s.count(old)
        if c == 0:
            print("MISS [%s] %r" % (tag, _a(old)[:70]))
            total_miss += 1
        else:
            s = s.replace(old, new)
    save(path, s)
    print("[%s] applied, misses=%d\n" % (tag, total_miss))
    return total_miss

# ── index.html ───────────────────────────────────────────────────────────────
HTML_RULES = [
    # header
    (">Undo</button>", ">撤销</button>"),
    ('title="Undo"', 'title="撤销"'),
    (">Redo</button>", ">重做</button>"),
    ('title="Redo"', 'title="重做"'),
    ('value="My Panorama Tour"', 'value="我的全景漫游"'),
    ('placeholder="Project title"', 'placeholder="项目名称"'),
    (">Saved</span>", ">已保存</span>"),
    (">Project ▾</button>", ">项目 ▾</button>"),
    (">New project</button>", ">新建项目</button>"),
    (">Open saved project…</button>", ">打开已存项目…</button>"),
    (">Import ZIP…</button>", ">导入 ZIP…</button>"),
    (">Save project</button>", ">保存项目</button>"),
    (">Save as…</button>", ">另存为…</button>"),
    (">Preview tour</button>", ">预览漫游</button>"),
    (">Settings</button>", ">设置</button>"),
    (">Floor Plan</button>", ">户型图</button>"),
    (">Export</button>", ">导出</button>"),
    # settings modal header + tabs
    (">Settings <span", ">设置 <span"),
    ('title="Close"', 'title="关闭"'),
    (">Viewer</button>", ">查看器</button>"),
    (">Branding</button>", ">品牌</button>"),
    (">Hotspots</button>", ">热点</button>"),
    (">Presets</button>", ">预设</button>"),
    (">Backup</button>", ">备份</button>"),
    # viewer tab
    (">Viewer Controls</h3>", ">查看器控件</h3>"),
    ("> Autorotate</label>", "> 自动旋转</label>"),
    ("> Fullscreen button</label>", "> 全屏按钮</label>"),
    ("> Zoom buttons</label>", "> 缩放按钮</label>"),
    ("> Compass</label>", "> 指南针</label>"),
    (">When enabled, select a scene to turn the compass on or off for that view and set the north offset.</p>",
     ">开启后，可选中某个场景来为该视角开启或关闭指南针，并设置正北偏移。</p>"),
    (">Mouse mode", ">鼠标模式"),
    (">Drag</option>", ">拖拽</option>"),
    # branding tab
    (">Logo and buttons appear in the top-right corner of the published tour.</p>",
     ">Logo 与按钮会显示在已发布漫游页面的右上角。</p>"),
    (">Button 1</h3>", ">按钮 1</h3>"),
    (">Button 2</h3>", ">按钮 2</h3>"),
    (">Button 3</h3>", ">按钮 3</h3>"),
    (">Text<div", ">文字<div"),
    (">BG<div", ">背景<div"),
    ('>Label<input', '>文字<input'),
    ('>URL<input', '>链接<input'),
    ('placeholder="Our Website"', 'placeholder="我们的官网"'),
    ('placeholder="Portfolio"', 'placeholder="作品集"'),
    ('placeholder="See More Projects"', 'placeholder="更多项目"'),
    (" New tab</label>", " 新标签页</label>"),
    ('>Button 1</span>', '>按钮 1</span>'),
    ('>Button 2</span>', '>按钮 2</span>'),
    ('>Button 3</span>', '>按钮 3</span>'),
    ('>Link URL<input', '>链接地址<input'),
    (" Open in new tab</label>", " 在新标签页打开</label>"),
    (">Image</span>", ">图片</span>"),
    (">Upload</button>", ">上传</button>"),
    (">Remove</button>", ">移除</button>"),
    # hotspots tab
    (">Customise the background and icon colour for each hotspot type. The preview updates live.</p>",
     ">为每种热点类型自定义背景色与图标色，预览会实时更新。</p>"),
    (">Preview</span>", ">预览</span>"),
    (">Type</span>", ">类型</span>"),
    (">Background</span>", ">背景色</span>"),
    (">Icon colour</span>", ">图标色</span>"),
    (">Info</span>", ">信息</span>"),
    (">Camera</span>", ">相机</span>"),
    (">Arrow</span>", ">箭头</span>"),
    (">Door</span>", ">门</span>"),
    (">Star</span>", ">星标</span>"),
    (">Eye</span>", ">眼睛</span>"),
    (">Location</span>", ">位置</span>"),
    ('title="Camera"', 'title="相机"'),
    ('title="Arrow"', 'title="箭头"'),
    ('title="Door"', 'title="门"'),
    ('title="Star"', 'title="星标"'),
    ('title="Eye"', 'title="眼睛"'),
    ('title="Location"', 'title="位置"'),
    # presets tab
    (">Save all Settings (viewer controls, branding, hotspot colours) as a named preset to reuse across projects.</p>",
     ">将所有设置（查看器控件、品牌、热点颜色）保存为命名预设，以便跨项目复用。</p>"),
    (">Load a preset</h3>", ">载入预设</h3>"),
    (">— select preset —", ">— 选择预设 —"),
    (">Load</button>", ">载入</button>"),
    ('title="Delete preset"', 'title="删除预设"'),
    (">Save current settings as preset</h3>", ">将当前设置存为预设</h3>"),
    ('placeholder="Preset name…"', 'placeholder="预设名称…"'),
    (">Save</button>", ">保存</button>"),
    # backup tab
    (">Export a backup of your data to restore on another machine or after a fresh install.</p>",
     ">导出你的数据备份，以便在另一台机器上或全新安装后恢复。</p>"),
    (">Storage</h3>", ">存储</h3>"),
    (">Refresh</button>", ">刷新</button>"),
    (">Clean Orphan Tiles</button>", ">清理孤立瓦片</button>"),
    (">Export Backup</h3>", ">导出备份</h3>"),
    (">Select what to include in the backup:</p>", ">选择要包含进备份的内容：</p>"),
    ("> Saved projects ", "> 已存项目 "),
    (">(includes scene tiles)</span>", ">（含场景瓦片）</span>"),
    ("> Style presets</label>", "> 样式预设</label>"),
    (">Export Backup</button>", ">导出备份</button>"),
    (">Import Backup</h3>", ">导入备份</h3>"),
    (">Restore data from a previously exported PanoPath backup ZIP.</p>",
     ">从此前导出的 PanoPath 备份 ZIP 恢复数据。</p>"),
    (">Import Backup</button>", ">导入备份</button>"),
    # floor plan panel
    (">Floor Plan Image</h3>", ">户型图图片</h3>"),
    (">Upload a floor plan image, then place a dot for each scene using the <em>Floor Plan Dot</em> section in the right panel.</p>",
     ">上传一张户型图，然后在右侧面板的<em>户型图标点</em>区域为每个场景放置一个标点。</p>"),
    (">Dot Style</h3>", ">标点样式</h3>"),
    (">Circle</button>", ">圆点</button>"),
    (">Direction</button>", ">方向</button>"),
    (">Plan Size</h3>", ">户型图尺寸</h3>"),
    (">Small</span>", ">小</span>"),
    (">Large</span>", ">大</span>"),
    (">Dot Appearance</h3>", ">标点外观</h3>"),
    (">Dot Size<input", ">标点大小<input"),
    (">Active dot colour<div", ">当前场景标点颜色<div"),
    (">Current scene</span>", ">当前场景</span>"),
    (">Inactive dot colour<div", ">其他场景标点颜色<div"),
    (">Other scenes</span>", ">其他场景</span>"),
    (">Ring colour<div", ">描边颜色<div"),
    (">Outline</span>", ">外圈描边</span>"),
    (">Active</span>", ">激活</span>"),
    (">Inactive</span>", ">未激活</span>"),
    # sidebar
    (">Panoramas</span>", ">全景图</span>"),
    (">+ Add</button>", ">+ 添加</button>"),
    ('placeholder="Search scenes, tags, notes"', 'placeholder="搜索场景、标签、备注"'),
    (">Drag &amp; drop images here</div>", ">将图片拖放到此处</div>"),
    (">or click + Add above", ">或点击上方“+ 添加”"),
    # viewer area
    (">Add panoramas to get started</div>", ">添加全景图开始制作</div>"),
    (">Plan</span>", ">平面图</span>"),
    ('title="Maximise"', 'title="最大化"'),
    ('title="Minimise"', 'title="最小化"'),
    ('alt="Plan"', 'alt="平面图"'),
    ("hidden>Plan <svg", "hidden>平面图 <svg"),
    (">Click to place hotspot — Esc to cancel</div>", ">点击放置热点 — 按 Esc 取消</div>"),
    (">Click anywhere to place dot on plan — Esc to cancel</div>", ">点击任意处在平面图上放置标点 — 按 Esc 取消</div>"),
    (">Select a scene to edit</div>", ">选择一个场景进行编辑</div>"),
    (">Drop images here</div>", ">松开以放置图片</div>"),
    (">Processing...</div>", ">处理中…</div>"),
    (">Cancel</button>", ">取消</button>"),
    ('title="Cancel"', 'title="取消"'),
    ('placeholder="Enter info text…"', 'placeholder="输入信息文字…"'),
    (">OK</button>", ">确定</button>"),
    (">Link Hotspot</h3>", ">跳转热点</h3>"),
    (">Choose an icon style</p>", ">选择图标样式</p>"),
    (">Select target scene</p>", ">选择目标场景</p>"),
    (">Open Project</h3>", ">打开项目</h3>"),
    (">No saved projects yet.<br>Use \"Project → Save project\" to save your current work.</div>",
     ">还没有已保存的项目。<br>使用“项目 → 保存项目”来保存当前工作。</div>"),
    (">Save Project</h3>", ">保存项目</h3>"),
    (">Saves to the server so you can load it later from any browser on this machine.</p>",
     ">保存到服务器，之后可在本机的任意浏览器载入。</p>"),
    ('placeholder="Project name…"', 'placeholder="项目名称…"'),
    (">Fisheye Field of View</h3>", ">鱼眼视场角</h3>"),
    (">Enter the lens FOV in degrees.<br>Most fisheye lenses are 180°.</p>",
     ">输入镜头的视场角（度）。<br>多数鱼眼镜头为 180°。</p>"),
    (">Range: 90° – 280°</p>", ">范围：90° – 280°</p>"),
    (">Continue</button>", ">继续</button>"),
    (">Switch Projection?</h3>", ">切换投影模式？</h3>"),
    (">The following will be permanently lost:</p>", ">以下内容将被永久清除：</p>"),
    (">The initial view and north offset will also be reset.</p>", ">初始视角与正北偏移也会被重置。</p>"),
    (">Re-process</button>", ">重新处理</button>"),
    (">Export Tour</h3>", ">导出漫游</h3>"),
    (">Choose an export type</p>", ">选择导出类型</p>"),
    (">Full Export</div>", ">完整导出</div>"),
    (">Includes all files needed to host and re-import for future editing. Larger file size.</div>",
     ">包含托管及日后重新导入编辑所需的全部文件，体积较大。</div>"),
    (">Hosting Only</div>", ">仅托管</div>"),
    (">Tiles and viewer only — smallest possible size for hosting on a website.</div>",
     ">仅包含瓦片与查看器——用于网站托管的最小体积。</div>"),
    (">Cannot be re-imported for future editing.</div>", ">无法再导入进行后续编辑。</div>"),
    (">Tour Exported!</h3>", ">漫游已导出！</h3>"),
    (">Extract the ZIP and open <code>index.html</code> in any browser.</p>",
     ">解压 ZIP 后，在任意浏览器中打开 <code>index.html</code>。</p>"),
    ("<span>Floor Plan</span>", "<span>户型图</span>"),
]

def stage_html():
    s = load(F_HTML)
    n = s.count(MOJI); s = s.replace(MOJI, ELL)
    print("[html] normalized ellipsis mojibake x%d" % n)
    save(F_HTML, s)
    return apply(F_HTML, HTML_RULES, "html")

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "html"
    if which == "html":
        stage_html()
    else:
        print("unknown stage")
