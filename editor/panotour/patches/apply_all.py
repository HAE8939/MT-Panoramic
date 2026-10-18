# -*- coding: utf-8 -*-
"""一键重放全部补丁 —— 把「升级引擎后该跑什么」这条最容易记错的知识固化成一条命令。

背景（2026-09-26 实测发现）：localize2.py / localize3.py 是**分阶段**的，
只按文件名依次跑一遍会静默漏掉 `toolfix` / `htmlfix` / `compass` 三个阶段，
结果比仓库里已提交的状态少 6 处改动（存储加载文案、两个删除按钮的 ✕、指北针「北」×2）。
所以别再手敲单脚本，统一走本文件。

用法：
  python panotour/patches/apply_all.py              # 在当前状态上重放（幂等，已应用处报 0）
  python panotour/patches/apply_all.py --pristine   # 先回到上游 pristine 再重放，用于校验可复现性

--pristine 会执行 `git checkout <上游基线> -- .`，把工作区里所有被改过的跟踪文件
打回上游原样（不影响 .git 历史，也不影响未跟踪的 tmp/ 与 public/img/），随后重放。
重放完用 `git -C MT-Panoramic diff --stat HEAD` 核对：应当只剩你本次真正新增的东西。
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows 控制台默认 GBK，中文与 ▶ 会炸
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ENGINE = os.path.join(ROOT, "MT-Panoramic")
BASELINE = "aa8861b"   # 上游基线 commit（引擎仓库 git log 里我们的第一个 commit 的父）

# 顺序不可乱：后阶段依赖前阶段改出的中文串
SEQUENCE = [
    ("localize.py", None,        "index.html 首轮文案"),
    ("localize2.py", "tool",     "tool.js 主体文案"),
    ("localize2.py", "toolfix",  "tool.js 乱码归一 + 补两处（省略号/✕）"),
    ("localize2.py", "htmlfix",  "index.html 补漏（存储加载文案）"),
    ("localize3.py", "srv",      "server 后端提示 + 导出模板 + README"),
    ("localize3.py", "compass",  "指北针 N→北（index.html 与导出模板）"),
    ("rebrand.py", None,         "身份替换 → MT-Panoramic + logo 装配 + README 重写"),
    ("theme_editor.py", None,    "编辑器配色 → 设计系统令牌"),
]


def run(script, stage, desc):
    argv = [sys.executable, os.path.join(HERE, script)] + ([stage] if stage else [])
    env = dict(os.environ, PYTHONIOENCODING="utf-8")   # 子进程 stdout 也走 UTF-8，防 GBK 崩
    print("\n▶ %s%s   —— %s" % (script, " " + stage if stage else "", desc))
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.splitlines():
        if "MISS" in line:
            print("   " + line.strip())
    tail = [l for l in out.splitlines() if l.strip()]
    if tail:
        print("   " + " | ".join(l.strip() for l in tail[-4:]))
    if p.returncode != 0:
        print("   × 退出码 %d" % p.returncode)
        sys.exit(p.returncode)


def main():
    pristine = "--pristine" in sys.argv[1:]
    if pristine:
        print("· 回到上游 pristine：%s" % BASELINE)
        subprocess.run(["git", "checkout", BASELINE, "--", "."], cwd=ENGINE, check=True)
    for script, stage, desc in SEQUENCE:
        run(script, stage, desc)
    if pristine:
        # 关键收尾：`git checkout <commit> -- .` 会把 baseline 内容**暂存进索引**。
        # 此时若直接 git commit，就会把上游原文件一起提交、静默回退掉汉化与配色
        # （2026-09-26 实际踩过一次）。mixed reset 只把索引同步回 HEAD，不碰工作区。
        subprocess.run(["git", "reset", "-q"], cwd=ENGINE, check=True)
        print("· 已把索引同步回 HEAD（避免 baseline 暂存内容被误提交）")
    print("\n· 重放完成。核对：git -C MT-Panoramic diff --stat HEAD（应只剩本次真正新增的东西）")
    subprocess.run(["git", "diff", "--stat", "HEAD"], cwd=ENGINE)


if __name__ == "__main__":
    main()
