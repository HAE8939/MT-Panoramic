# -*- coding: utf-8 -*-
"""深度汉化 · 阶段2：tool.js（编辑器动态文案/弹窗/属性面板）。用带引号的完整字面量精确匹配，只改显示文本。"""
import sys, io, os

# 从脚本自身位置相对推导：panotour/patches/ -> 项目根 -> MT-Panoramic（引擎目录，原 PanoPath）
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MT-Panoramic"))
F_TOOL = BASE + r"\public\js\tool.js"
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

TOOL_RULES = [
    # 状态
    ("updateProjectStatus('Unsaved', 'dirty')", "updateProjectStatus('未保存', 'dirty')"),
    ("updateProjectStatus('Saved')", "updateProjectStatus('已保存')"),
    ("updateProjectStatus('Autosaved', 'autosaved')", "updateProjectStatus('已自动保存', 'autosaved')"),
    ("confirm('Restore the last autosaved session?')", "confirm('恢复上次自动保存的会话？')"),
    # 侧栏行 title 与默认值
    ("title='Drag to reorder'", "title='拖动以重新排序'"),
    ("title='Double-click to rename'", "title='双击重命名'"),
    ("title='Double-click to rename folder'", "title='双击重命名文件夹'"),
    ("del.title='Remove'", "del.title='移除'"),
    ("b.title='First scene'", "b.title='起始场景'"),
    ("chips.push('note')", "chips.push('备注')"),
    ("folder.name || 'Folder'", "folder.name || '文件夹'"),
    ("name: 'Folder'", "name: '文件夹'"),
    # 场景复制 / 删除 / 移除瓦片
    ("sd.name + ' Copy'", "sd.name + ' 副本'"),
    ("confirm('Remove this scene?')", "confirm('删除此场景？')"),
    ("confirm('Remove tile folders that are not referenced by any saved project?')",
     "confirm('删除未被任何已保存项目引用的瓦片目录？')"),
    ("confirm('Start a new project? Unsaved changes will be lost.')",
     "confirm('开始新项目？未保存的更改将丢失。')"),
    # 各种 alert / prompt
    ("alert('No supported images found.')", "alert('未找到受支持的图片。')"),
    ("alert('Enter a preset name.')", "alert('请输入预设名称。')"),
    ("alert('Choose a preset first.')", "alert('请先选择一个预设。')"),
    ("confirm('Delete preset \"'+name+'\"?')", "confirm('删除预设“'+name+'”？')"),
    ("alert('Select at least one item to include in the backup.')",
     "alert('请至少选择一项纳入备份。')"),
    ("alert('Add at least one panorama first.')", "alert('请先添加至少一个全景。')"),
    ("alert('Duplicate failed: '+err.message)", "alert('复制失败：'+err.message)"),
    ("alert('Need at least 2 scenes for a link hotspot.')", "alert('链接热点至少需要 2 个场景。')"),
    ("alert('Re-processing returned incomplete data. Please try again.')",
     "alert('重新处理返回的数据不完整，请重试。')"),
    ("alert('Scene re-processed but could not be displayed: ' + e.message)",
     "alert('场景已重新处理，但无法显示：' + e.message)"),
    ("alert('Re-processing failed: ' + err.message)", "alert('重新处理失败：' + err.message)"),
    ("alert('Export failed: '+err.message)", "alert('导出失败：'+err.message)"),
    ("alert('Add at least one scene first.')", "alert('请先添加至少一个场景。')"),
    ("alert('Popup blocked. Please allow popups to open preview.')",
     "alert('弹窗被拦截。请允许弹窗以打开预览。')"),
    ("alert('Preview failed: '+err.message)", "alert('预览失败：'+err.message)"),
    ("alert('No scenes found.')", "alert('未找到任何场景。')"),
    ("alert('Add at least one scene before saving.')", "alert('保存前请先添加至少一个场景。')"),
    ("alert('Save failed: '+err.message)", "alert('保存失败：'+err.message)"),
    ("alert('Enter a project name.')", "alert('请输入项目名称。')"),
    ("confirm('\"'+name+'\" already exists. Overwrite it?')", "confirm('“'+name+'” 已存在，要覆盖吗？')"),
    ("alert('Import error: '+err.message)", "alert('导入错误：'+err.message)"),
    ("alert('Import failed: '+err.message)", "alert('导入失败：'+err.message)"),
    ("alert('Error processing \"'+file.name+'\":\\n'+err.message)",
     "alert('处理\"'+file.name+'\"时出错：\\n'+err.message)"),
    ("window.prompt('Edit hotspot text', hs.text || '')", "window.prompt('编辑热点文字', hs.text || '')"),
    # 备份 / 存储
    ("status.textContent='Preparing backup...'", "status.textContent='正在准备备份…'"),
    ("status.textContent='Backup exported.'", "status.textContent='备份已导出。'"),
    ("status.textContent='Importing backup...'", "status.textContent='正在导入备份…'"),
    ("parts.push(r.projects+' project(s)')", "parts.push(r.projects+' 个项目')"),
    ("parts.push('presets')", "parts.push('预设')"),
    ("parts.push('tile files')", "parts.push('瓦片文件')"),
    ("status.textContent='Restored: '+parts.join(', ')+'. Reload to see changes.';",
     "status.textContent='已恢复：'+parts.join('、')+'。刷新后可见更改。';"),
    ("status.textContent='Export failed: '+err.message", "status.textContent='导出失败：'+err.message"),
    ("status.textContent='Import failed: '+err.message", "status.textContent='导入失败：'+err.message"),
    ("['Saved projects', stats.projectCount]", "['已保存项目', stats.projectCount]"),
    ("['Scene tile folders', stats.sceneTileCount]", "['场景瓦片目录', stats.sceneTileCount]"),
    ("['Projects size', formatBytes(stats.projectBytes)]", "['项目占用', formatBytes(stats.projectBytes)]"),
    ("['Tiles size', formatBytes(stats.tileBytes)]", "['瓦片占用', formatBytes(stats.tileBytes)]"),
    ("['Temp uploads', formatBytes(stats.uploadBytes)]", "['临时上传', formatBytes(stats.uploadBytes)]"),
    ("['Presets size', formatBytes(stats.presetsBytes)]", "['预设占用', formatBytes(stats.presetsBytes)]"),
    ("['Orphan tiles', stats.orphanTileCount", "['孤立瓦片', stats.orphanTileCount"),
    ("Loading storage stats…", "正在加载存储信息…"),
    ("Could not load stats: ", "无法加载统计："),
    ("$('#backup-status').textContent = 'Removed '+data.removedCount+' orphan tile folder(s), freed '+formatBytes(data.removedBytes)+'.';",
     "$('#backup-status').textContent = '已删除 '+data.removedCount+' 个孤立瓦片目录，释放 '+formatBytes(data.removedBytes)+'。';"),
    ("$('#backup-status').textContent = 'Cleanup failed: '+err.message;", "$('#backup-status').textContent = '清理失败：'+err.message;"),
    # 预设下拉（文本位于 ">…<" 之间）
    (">— select preset —<", ">— 选择预设 —<"),
    # 按钮预览 / 项目标题
    ("|| 'Button '+n", "|| '按钮 '+n"),
    ("$('#project-title').value='My Panorama Tour';", "$('#project-title').value='我的全景漫游';"),
    ("value||'Panorama Tour'", "value||'全景漫游'"),
    ("'<div class=\"props-empty\">Select a scene to edit</div>'", "'<div class=\"props-empty\">选择一个场景进行编辑</div>'"),
    # 处理进度标签
    ("label.textContent='Processing: '+file.name;", "label.textContent='处理中：'+file.name;"),
    ("label.textContent='Importing project ZIP…';", "label.textContent='正在导入项目 ZIP…';"),
    ("$('#processing-label').textContent='Generating ZIP…';", "$('#processing-label').textContent='正在生成 ZIP…';"),
    ("label.textContent = 'Re-processing as ' + targetLabel + '…';", "label.textContent = '正在重新处理为 ' + targetLabel + '…';"),
    # 平面旋转 alert
    ("alert('Rotation failed: '+result.error)", "alert('旋转失败：'+result.error)"),
    ("alert('Rotation failed: '+err.message)", "alert('旋转失败：'+err.message)"),
    # 平面图最大化/最小化标题
    ("maxBtn.title = on ? 'Restore' : 'Maximise';", "maxBtn.title = on ? '还原' : '最大化';"),
    # renderProps 标签
    ("el('div','prop-label','Scene Name')", "el('div','prop-label','场景名称')"),
    ("el('div','prop-label','Tags')", "el('div','prop-label','标签')"),
    ("ti.placeholder='lobby, exterior, floor 2';", "ti.placeholder='如：客厅、外观、二楼';"),
    ("el('div','prop-label','Notes')", "el('div','prop-label','备注')"),
    ("notes.placeholder='Scene notes for search and project organization';",
     "notes.placeholder='用于搜索与项目整理的场景备注';"),
    ("el('button','btn btn-sm','Duplicate Scene')", "el('button','btn btn-sm','复制场景')"),
    ("el('span','prop-section','Image Settings')", "el('span','prop-section','图像设置')"),
    ("el('div','prop-label','Rotate Image')", "el('div','prop-label','旋转图像')"),
    ("rotHint.textContent='(flat images only)';", "rotHint.textContent='（仅平面图像）';"),
    ("rb.title='Only available for flat images';", "rb.title='仅平面图像可用';"),
    ("'No source image stored. Re-import this image to enable projection switching.'",
     "'未存储原图。请重新导入此图片以启用投影切换。'"),
    ("curProjLabel = sd.projection === 'flat' ? 'Flat' : (sd.fisheyeFov ? 'Fisheye (' + sd.fisheyeFov + '°)' : 'Panorama');",
     "curProjLabel = sd.projection === 'flat' ? '平面' : (sd.fisheyeFov ? '鱼眼（' + sd.fisheyeFov + '°）' : '全景');"),
    ("curNote.textContent='Current: ' + curProjLabel + '. Switch to:';", "curNote.textContent='当前：' + curProjLabel + '。切换到：';"),
    ("makeProjBtn('Flat', 'flat')", "makeProjBtn('平面', 'flat')"),
    ("makeProjBtn('Panorama', 'cube')", "makeProjBtn('全景', 'cube')"),
    ("makeProjBtn('Fisheye', 'fisheye')", "makeProjBtn('鱼眼', 'fisheye')"),
    ("el('div','prop-section','Scene Controls')", "el('div','prop-section','场景控制')"),
    ("'✓ View Set' : 'Set Initial View'", "'✓ 视角已设' : '设初始视角'"),
    ("sivBtn.textContent='✓ View Set';", "sivBtn.textContent='✓ 视角已设';"),
    ("sivBtn.textContent=sd.initialViewSet?'✓ View Set':'Set Initial View';", "sivBtn.textContent=sd.initialViewSet?'✓ 视角已设':'设初始视角';"),
    ("isFirst ? '★ First Scene' : 'Set as First'", "isFirst ? '★ 起始场景' : '设为起始'"),
    ("sfb.textContent='★ First Scene';", "sfb.textContent='★ 起始场景';"),
    ("el('span','prop-section','Compass')", "el('span','prop-section','指南针')"),
    ("+'> Show compass on this view'", "+'> 在此视角显示指南针'"),
    ("el('div','prop-label','North Offset')", "el('div','prop-label','正北偏移')"),
    ("el('button','btn btn-sm','Use Current Heading')", "el('button','btn btn-sm','使用当前朝向')"),
    ("cmpOff.innerHTML='Compass is off. Enable it in <strong>Settings → Viewer</strong>.';",
     "cmpOff.innerHTML='指南针已关闭。请在<strong>设置 → 查看器</strong>中开启。';"),
    ("el('span','prop-section','Floor Plan Dot')", "el('span','prop-section','户型图标点')"),
    ("sd.planDot?'Dot placed — click to move':'Click to place dot on plan'", "sd.planDot?'已放置标点 — 点击移动':'点击在平面图上放置标点'"),
    ("el('button','btn btn-sm','Remove Dot')", "el('button','btn btn-sm','移除标点')"),
    ("dotTxt.textContent='Click to place dot on plan';", "dotTxt.textContent='点击在平面图上放置标点';"),
    ("el('div','prop-label','Dot Type')", "el('div','prop-label','标点类型')"),
    ("dtLabels={default:'Default',circle:'Dot',arrow:'Direction'};", "dtLabels={default:'默认',circle:'圆点',arrow:'方向'};"),
    ("el('div','prop-label','Direction')", "el('div','prop-label','方向')"),
    ("fpOff.innerHTML='No floor plan uploaded. Add one using the <strong>Floor Plan</strong> button in the toolbar.';",
     "fpOff.innerHTML='尚未上传户型图。请通过工具栏的<strong>户型图</strong>按钮添加。';"),
    ("el('div','prop-section','Hotspots')", "el('div','prop-section','热点')"),
    ("bi=el('button','btn','Info');", "bi=el('button','btn','信息');"),
    ("bl=el('button','btn','Link');", "bl=el('button','btn','跳转');"),
    # 热点列表
    (">No hotspots yet<", ">暂无热点<"),
    ("(hs.text||'Info'):('→ '+(hs.targetName||'Scene'))", "(hs.text||'信息'):('→ '+(hs.targetName||'场景'))"),
    ("(hs.text||'Info'):('Link: '+(hs.targetName||'Scene'))", "(hs.text||'信息'):('跳转：'+(hs.targetName||'场景'))"),
    ("el('button','hs-action','Edit')", "el('button','hs-action','编辑')"),
    ("el('button','hs-action','Copy')", "el('button','hs-action','复制')"),
    ("=el('button','hs-del','x');", "=el('button','hs-del','✕');"),
    ("(clone.text || 'Info') + ' Copy'", "(clone.text || '信息') + ' 副本'"),
    ("d.title='Delete'", "d.title='删除'"),
    # 放置提示
    ("$('#place-msg').textContent='Click in the panorama to place '+(type==='info'?'info':'link')+' hotspot — Esc to cancel';",
     "$('#place-msg').textContent='点击全景放置'+(type==='info'?'信息':'跳转')+'热点 — 按 Esc 取消';"),
    # 投影切换
    ("var PROJ_LABELS = { flat: 'Flat', cube: 'Panorama', fisheye: 'Fisheye' };",
     "var PROJ_LABELS = { flat: '平面', cube: '全景', fisheye: '鱼眼' };"),
    ("document.querySelector('#reproject-modal h3').textContent = 'Switch to ' + targetLabel + '?';",
     "document.querySelector('#reproject-modal h3').textContent = '切换到 ' + targetLabel + '？';"),
    ("flat:    'The image will be re-processed as a flat 2D scene.',",
     "flat:    '图像将被重新处理为平面 2D 场景。',"),
    ("cube:    'The image will be re-processed as a 360° equirectangular panorama.',",
     "cube:    '图像将被重新处理为 360° 等距柱状全景。',"),
    ("fisheye: 'The image will be re-processed as a fisheye hemisphere (FOV: ' + _reprojFov + '°).'",
     "fisheye: '图像将被重新处理为鱼眼半球（视场角：' + _reprojFov + '°）。'"),
    ("if (infoCount) losses.push(infoCount + ' info hotspot' + (infoCount>1?'s':''));", "if (infoCount) losses.push(infoCount + ' 个信息热点');"),
    ("if (linkCount) losses.push(linkCount + ' link hotspot' + (linkCount>1?'s':''));", "if (linkCount) losses.push(linkCount + ' 个跳转热点');"),
    ("if (hasPlanDot) losses.push('floor plan dot position');", "if (hasPlanDot) losses.push('户型图标点位置');"),
    # 导出结果
    ("title.textContent='Hosting Export Ready!';", "title.textContent='托管导出已就绪！';"),
    ("msg.innerHTML='Extract the ZIP and upload to your web server.<br><span style=\"color:#e94560;font-size:12px\">⚠ This export cannot be re-imported for editing.</span>';",
     "msg.innerHTML='解压 ZIP 并上传到你的 Web 服务器。<br><span style=\"color:#e94560;font-size:12px\">⚠ 此导出无法再导入进行编辑。</span>';"),
    ("title.textContent='Tour Exported!';", "title.textContent='漫游已导出！';"),
    ("msg.innerHTML='Extract the ZIP and open <code>index.html</code> in any browser.';",
     "msg.innerHTML='解压 ZIP 后在任意浏览器中打开 <code>index.html</code>。';"),
    # 预览占位
    ("'<title>PanoPath Preview</title><p style=\"font-family:sans-serif;padding:16px\">Preparing preview...</p>'",
     "'<title>PanoPath 预览</title><p style=\"font-family:sans-serif;padding:16px\">正在准备预览…</p>'"),
    # 载入列表
    ("<div class=\"saved-empty\">Loading…</div>", "<div class=\"saved-empty\">加载中…</div>"),
    ("<div class=\"saved-empty\">No saved projects yet.<br>Use Save Project to save your work.</div>",
     "<div class=\"saved-empty\">还没有已保存的项目。<br>使用“保存项目”保存你的工作。</div>"),
    ("(p.sceneCount||0)+' scenes'", "(p.sceneCount||0)+' 个场景'"),
    ("del.title='Delete'", "del.title='删除'"),
    ("if(!confirm('Delete \"'+p.name+'\"?')) return;", "if(!confirm('删除“'+p.name+'”？')) return;"),
    ("<div class=\"saved-empty\">Could not load projects.</div>", "<div class=\"saved-empty\">无法加载项目列表。</div>"),
    # 保存反馈
    ("btn.textContent='✓ Saved!';", "btn.textContent='✓ 已保存！';"),
    ("btn.textContent='Save project';", "btn.textContent='保存项目';"),
    # 载入通知
    ("notices.push('Warning: '+missing.length+' scene(s) have missing tiles.');",
     "notices.push('警告：'+missing.length+' 个场景的瓦片缺失。');"),
    ("notices.push('Project loaded: '+state.scenes.length+' scene(s).');",
     "notices.push('项目已加载：'+state.scenes.length+' 个场景。');"),
]

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "tool"
    if stage == "tool":
        apply(F_TOOL, TOOL_RULES, "tool")
    elif stage == "toolfix":
        s = load(F_TOOL)
        for o, n in [("â€¦", "…"), ("âœ•", "✕")]:
            print("[toolfix] normalize x%d -> %r" % (s.count(o), _a(n)))
            s = s.replace(o, n)
        save(F_TOOL, s)
        apply(F_TOOL, [
            ("Loading storage stats…", "正在加载存储信息…"),
            ("=el('button','scene-del','x');", "=el('button','scene-del','✕');"),
        ], "toolfix")
    elif stage == "htmlfix":
        apply(F_HTML, [("Loading storage stats…", "正在加载存储信息…")], "htmlfix")
    else:
        print("unknown stage", stage)
