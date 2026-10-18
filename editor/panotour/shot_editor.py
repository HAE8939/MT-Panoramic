# -*- coding: utf-8 -*-
"""编辑器/导览页视觉自检：截图 + 关键 DOM 读数 + JS 报错收集。

用途：改完 tool.css 或品牌主题后，跑一次拿到「看起来对不对」的客观证据，
而不是靠 curl 猜。WebGL 场景需 --use-gl=angle --use-angle=swiftshader；
注意 headless 软件渲染下 Marzipano 可能只在画布中央画方块（真浏览器正常），
凡 headless 发现的异常都要留真机复核，别据此改设计。

用法：
  python panotour/shot_editor.py                      # 默认拍 http://127.0.0.1:3199/
  python panotour/shot_editor.py <url> <输出png路径>
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3199/"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "dist", "自检_编辑器.png")
CANDS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
exe = next((c for c in CANDS if os.path.exists(c)), None)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with sync_playwright() as p:
    kw = {"executable_path": exe} if exe else {}
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader"], **kw)
    pg = b.new_page(viewport={"width": 1440, "height": 860})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    print("· 内核：", exe or "playwright 自带 chromium")
    print("· 标签页标题：", pg.title())
    if pg.locator(".topbar-left").count():
        print("· 页头品牌：", pg.inner_text(".topbar-left").strip())
        probe = lambda sel, prop: pg.eval_on_selector(sel, "el => getComputedStyle(el)." + prop)
        print("· 页头文字色：", probe(".logo", "color"))
        print("· 页面底色：", probe("body", "backgroundColor"))
        print("· 面板底色：", probe(".sidebar", "backgroundColor"))
        print("· 导出钮底色：", probe("#export-btn", "backgroundColor"))
        print("· 顶栏是否溢出：", pg.evaluate(
            "(()=>{const t=document.querySelector('.topbar');return t.scrollWidth>t.clientWidth})()"))
    pg.wait_for_timeout(600)
    pg.screenshot(path=OUT)
    print("· JS 报错：", errs or "无")
    b.close()
print("✓ 截图：", OUT)
