#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MT-Panoramic 品牌化导览构建器
==========================
把 全景照片 → 切片 → 品牌化自包含 web 导览 一条龙跑完，全程走编辑器（MT-Panoramic，
基于开源 PanoPath 二创）的本地 API，不改它的运行时逻辑；品牌层以「settings 注入 +
导出后追加 brand.css」两级实现。中文界面与工具改名由 patches/ 下四个脚本重放，不靠手改。

用法：
  python build_tour.py --brand gongsheng --project "XX 工地竣工" --out ./dist \
      "E:/path/pano1.jpg=客厅" "E:/path/pano2.jpg=主卧"

  --server  http://127.0.0.1:3199   编辑器服务地址（未启动会自动拉起）
  --no-export-zip                   只出解压版，便于本地直接看
  --start-server / --keep-server    自行管理服务生命周期

品牌包目录 brands/：
  <key>.json        设计令牌 → 编辑器原生 settings（标题/logo/热点色/平面图打点色）
  <key>.theme.css   导出后追加的叠层主题（把设计系统落成 CSS）
"""
import argparse, base64, io, json, math, mimetypes, os, re, subprocess, sys, time, urllib.request, zipfile

# Windows 控制台默认 GBK，中文与 ✓ 会炸；统一转 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND_DIR = os.path.join(HERE, "brands")
ENGINE_DIR = os.path.abspath(os.path.join(HERE, "..", "MT-Panoramic"))  # 全景编辑器引擎目录（原 PanoPath）
DEFAULT_SERVER = "http://127.0.0.1:3199"


# ────────────────────────────── 基础 HTTP ──────────────────────────────
def http_json(url, payload=None, timeout=600):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_post_multipart(url, file_path, field="panorama", extra=None, timeout=600):
    """手工拼 multipart/form-data，避免引入 requests 依赖。"""
    bound = "----HAE7" + os.urandom(8).hex()
    body = io.BytesIO()
    for k, v in (extra or {}).items():
        body.write(f"--{bound}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    name = os.path.basename(file_path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(file_path, "rb") as f:
        blob = f.read()
    body.write(f"--{bound}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n"
               f"Content-Type: {ctype}\r\n\r\n".encode())
    body.write(blob)
    body.write(f"\r\n--{bound}--\r\n".encode())
    req = urllib.request.Request(url, data=body.getvalue(),
                                headers={"Content-Type": f"multipart/form-data; boundary={bound}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def server_alive(server):
    try:
        http_json(server + "/api/projects", timeout=3)
        return True
    except Exception:
        return False


def ensure_server(server, spawn=True, keep=False):
    if server_alive(server):
        print(f"· 复用已运行的编辑器：{server}")
        return None
    if not spawn:
        sys.exit(f"× 编辑器未运行（{server}）。先 cd MT-Panoramic && node server/index.js")
    port = re.search(r":(\d+)", server).group(1)
    print(f"· 拉起编辑器（PORT={port}）…")
    env = dict(os.environ, PORT=port)
    p = subprocess.Popen(["node", "server/index.js"], cwd=ENGINE_DIR, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        if server_alive(server):
            break
        time.sleep(1)
    else:
        p.terminate(); sys.exit("× 编辑器启动超时")
    print(f"· 已就绪：{server}")
    return (p, keep)


# ────────────────────────────── 品牌注入 ──────────────────────────────
def load_brand(key):
    cfg_path = os.path.join(BRAND_DIR, f"{key}.json")
    if not os.path.exists(cfg_path):
        sys.exit(f"× 找不到品牌包：{cfg_path}")
    with open(cfg_path, encoding="utf-8") as f:
        brand = json.load(f)
    theme_path = os.path.join(BRAND_DIR, brand.get("theme_css", f"{key}.theme.css"))
    brand["_theme_path"] = theme_path if os.path.exists(theme_path) else None
    return brand


def logo_data_uri(brand):
    p = brand.get("logo")
    if not p:
        return None
    # 相对路径按品牌包目录解析，品牌资产随 brands/ 一起入库，不再依赖桌面 TEMP 里的原件
    if not os.path.isabs(p):
        p = os.path.join(BRAND_DIR, p)
    if not os.path.exists(p):
        print(f"! logo 文件不存在，本次导出不带 logo：{p}"); return None
    mime = mimetypes.guess_type(p)[0] or "image/svg+xml"
    with open(p, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def apply_brand(brand, project):
    """settings 层：把设计令牌写进编辑器的原生配置字段。"""
    s = json.loads(json.dumps(brand.get("settings", {})))  # deep copy
    s["title"] = brand.get("title_template", "{brand} · {project}").format(
        brand=brand.get("brand", ""), project=project)
    uri = logo_data_uri(brand)
    if uri:
        s["logoData"] = uri
    return s


def zip_bytes(url, payload, timeout=900):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def inject_theme(raw_zip, theme_path, css_name="brand.css"):
    """导出后处理：index.html 的 style.css 之后追加品牌主题 link，并塞入 css 文件。"""
    with open(theme_path, encoding="utf-8") as f:
        css = f.read()
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zin, \
         zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "index.html":
                html = data.decode("utf-8")
                link = f'  <link rel="stylesheet" href="{css_name}">\n</head>'
                if css_name not in html:
                    html = html.replace("</head>", link, 1)
                data = html.encode("utf-8")
            if item.filename == css_name:      # 主题迭代时整条替换
                continue
            zout.writestr(item, data)
        zout.writestr(css_name, css)
    return out.getvalue()


def refresh_theme(brand, zip_path, view_dir=None):
    """只换主题、不重跑切片——调 CSS 时用，省掉每张图十几秒的切片开销。"""
    if not brand["_theme_path"]:
        sys.exit("× 该品牌包没有 theme.css")
    if not os.path.exists(zip_path):
        sys.exit(f"× 找不到 ZIP：{zip_path}")
    with open(zip_path, "rb") as f:
        raw = f.read()
    raw = inject_theme(raw, brand["_theme_path"])
    with open(zip_path, "wb") as f:
        f.write(raw)
    print(f"✓ 主题已刷新：{zip_path}  （{len(raw)/1024/1024:.1f} MB）")
    if view_dir and os.path.isdir(view_dir):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            z.extractall(view_dir)
        print(f"✓ 解压版同步：{view_dir}")



def load_plan_data_uri(plan_path):
    if not plan_path:
        return None, None
    if not os.path.exists(plan_path):
        sys.exit(f"× 平面图不存在：{plan_path}")
    mime = mimetypes.guess_type(plan_path)[0] or "image/jpeg"
    if mime not in ("image/png", "image/jpeg"):
        sys.exit(f"× 平面图格式仅支持 png/jpeg，当前 {mime}")
    with open(plan_path, "rb") as f:
        blob = f.read()
    # 读真实宽高比：planAspectRatio 必须等于图片实际比例，
    # 否则 object-fit:contain 会在 img 内留边，归一化打点坐标就会偏。
    from struct import unpack
    w = h = None
    try:
        from PIL import Image
        with Image.open(plan_path) as im:
            w, h = im.size
    except Exception:
        print("! 无法读取平面图尺寸，planAspectRatio 需用默认值（打点可能偏移）")
    uri = f"data:{mime};base64," + base64.b64encode(blob).decode()
    return uri, (w / h if w and h else None)


def build_scenes_from_spec(spec, server, base_dir="."):
    """spec: {"plan": 路径, "scenes":[{"image","name","dot":[x,y],"yaw":deg,"pitch":deg,"fov":deg}]}
    相对路径按 spec 文件所在目录解析 → 项目整体搬家不会断（绝对路径仍原样生效）。"""
    def resolve(p):
        return p if (not p or os.path.isabs(p)) else os.path.normpath(os.path.join(base_dir, p))

    scenes = []
    n = len(spec["scenes"])
    for i, sc in enumerate(spec["scenes"], 1):
        img = resolve(sc["image"])
        if not os.path.exists(img):
            sys.exit(f"× 文件不存在：{img}")
        name = sc.get("name") or os.path.splitext(os.path.basename(img))[0]
        print(f"· [{i}/{n}] 切片 {os.path.basename(img)} → {name}")
        r = http_post_multipart(server + "/api/process", img)
        if r.get("error"):
            sys.exit(f"× 处理失败：{r['error']}")
        yaw = math.radians(float(sc.get("yaw", 0)))
        pitch = math.radians(float(sc.get("pitch", 0)))
        fov = math.radians(float(sc.get("fov", 90)))
        scene = {
            "id": r["sceneId"], "name": name, "levels": r["levels"], "faceSize": r["faceSize"],
            "initialView": {"yaw": yaw, "pitch": pitch, "fov": fov},
            "initialViewSet": True, "hotspots": [], "projection": r.get("projection", "cube"),
            "compassEnabled": bool(sc.get("compassEnabled", False)),
            "northOffset": float(sc.get("northOffset", 0)),
            "sourceUrl": r.get("sourceUrl"),
        }
        if sc.get("dot"):
            scene["planDot"] = {"x": float(sc["dot"][0]), "y": float(sc["dot"][1]),
                                "rotation": float(sc.get("dotRotation", 0))}
        scenes.append(scene)
        print(f"    ✓ {r['faceSize']}px cube / {len(r['levels'])} 级"
              + (f" / 打点 ({sc['dot'][0]:.3f},{sc['dot'][1]:.3f})" if sc.get("dot") else ""))
    return scenes


def slim_from_full(brand, full_zip, out_dir, server=DEFAULT_SERVER, keep_server=False):
    """从已构建的完整版 ZIP 派生「托管版」：走 /api/export-slim，
    去掉每景 source.jpg（原图，占体积近一半）与 project.json。
    本地留全量母版可回编辑，发布用托管版。"""
    if not os.path.exists(full_zip):
        sys.exit(f"× 找不到完整版 ZIP：{full_zip}")
    with zipfile.ZipFile(full_zip) as z:
        proj = json.loads(z.read("project.json").decode("utf-8"))
    scenes, settings = proj["scenes"], proj["settings"]
    print(f"· 完整版：{len(scenes)} 景，母版 {os.path.getsize(full_zip)/1024/1024:.1f} MB")

    ctl = ensure_server(server, keep=keep_server)
    raw = zip_bytes(server + "/api/export-slim", {"scenes": scenes, "settings": settings})
    print(f"· 托管版导出：{len(raw)/1024/1024:.1f} MB")
    if brand["_theme_path"]:
        raw = inject_theme(raw, brand["_theme_path"])
        print(f"· 已注入品牌主题")

    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(full_zip))[0].replace("_全景导览", "")
    zip_path = os.path.join(out_dir, f"{stem}_托管版.zip")
    with open(zip_path, "wb") as f:
        f.write(raw)
    view_dir = os.path.join(out_dir, f"{stem}_托管版_web")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(view_dir)
    print(f"✓ 托管版 ZIP：{zip_path}")
    print(f"✓ 发布用目录：{view_dir}")
    if ctl and not keep_server:
        ctl[0].terminate()
    return view_dir


# ────────────────────────────── 主流程 ──────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="MT-Panoramic 品牌化全景导览构建器")
    ap.add_argument("images", nargs="*", help="全景图路径，可写作 路径=场景名")
    ap.add_argument("--brand", default="gongsheng", help="品牌包 key（brands/<key>.json）")
    ap.add_argument("--project", default="全景测试", help="项目名，进标题")
    ap.add_argument("--out", default=os.path.join(HERE, "dist"))
    ap.add_argument("--server", default=DEFAULT_SERVER)
    ap.add_argument("--keep-server", action="store_true", help="构建后不关闭自拉起的编辑器")
    ap.add_argument("--spec", help="项目清单 JSON：含 plan 与 scenes（每张图的名称/打点/初始视角）")
    ap.add_argument("--plan", help="平面图路径（jpg/png），启用后打点可点击跳转场景")
    ap.add_argument("--theme-only", metavar="ZIP", help="只把品牌主题刷进已有 ZIP（不重跑切片，不调用服务）")
    ap.add_argument("--view-dir", help="配合 --theme-only，同步刷新解压版目录")
    ap.add_argument("--slim-from", metavar="FULLZIP", help="从完整版 ZIP 派生托管版（去 source.jpg，用于发布）")
    args = ap.parse_args()

    brand = load_brand(args.brand)

    if args.theme_only:
        refresh_theme(brand, args.theme_only, args.view_dir)
        return

    if args.slim_from:
        slim_from_full(brand, args.slim_from, args.out, args.server, args.keep_server)
        return

    if not args.images and not args.spec:
        ap.error("至少给一张全景图，或用 --spec 项目清单")

    ctl = ensure_server(args.server, keep=args.keep_server)

    # 1) 场景切片
    if args.spec:
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
        spec_dir = os.path.dirname(os.path.abspath(args.spec))
        scenes = build_scenes_from_spec(spec, args.server, spec_dir)
        raw_plan = args.plan or spec.get("plan")
        plan_path = (raw_plan if not raw_plan or os.path.isabs(raw_plan)
                     else os.path.normpath(os.path.join(spec_dir, raw_plan)))
    else:
        scenes = []
        for i, spec_s in enumerate(args.images, 1):
            path, _, name = spec_s.rpartition("=")
            if not path:                      # 没有 =名字 的情况
                path, name = spec_s, None
            if not os.path.exists(path):
                sys.exit(f"× 文件不存在：{path}")
            name = name or os.path.splitext(os.path.basename(path))[0]
            print(f"· [{i}/{len(args.images)}] 切片 {os.path.basename(path)} → {name}")
            r = http_post_multipart(args.server + "/api/process", path)
            if r.get("error"):
                sys.exit(f"× 处理失败：{r['error']}")
            scenes.append({
                "id": r["sceneId"], "name": name, "levels": r["levels"], "faceSize": r["faceSize"],
                "initialView": r.get("suggestedInitialView") or {"yaw": 0, "pitch": 0, "fov": 1.5707963},
                "initialViewSet": False, "hotspots": [], "projection": r.get("projection", "cube"),
                "compassEnabled": bool(brand.get("settings", {}).get("compass")),
                "sourceUrl": r.get("sourceUrl"),
            })
            print(f"    ✓ {r['faceSize']}px cube / {len(r['levels'])} 级")
        plan_path = args.plan

    # 2) settings 合并
    settings = apply_brand(brand, args.project)
    plan_uri, plan_aspect = load_plan_data_uri(plan_path)
    if plan_uri:
        settings["planData"] = plan_uri
        if plan_aspect:
            settings["planAspectRatio"] = plan_aspect
            print(f"· 平面图 {plan_aspect:.4f} 宽高比已对齐（打点坐标准确的前提）")
        ndots = sum(1 for s in scenes if s.get("planDot"))
        print(f"· 平面图已挂载，{ndots}/{len(scenes)} 个场景有打点")
        if ndots and settings.get("dotType") == "arrow":
            print("! dotType=arrow 需要每个打点有可靠朝向，确认过再开")

    # 3) 导出
    print("· 导出自包含 ZIP…")
    raw = zip_bytes(args.server + "/api/export", {"scenes": scenes, "settings": settings})
    print(f"    ✓ {len(raw)/1024/1024:.1f} MB")


    # 4) 主题注入
    if brand["_theme_path"]:
        print(f"· 注入品牌主题 {os.path.basename(brand['_theme_path'])}")
        raw = inject_theme(raw, brand["_theme_path"])
    else:
        print("! 无 theme.css，仅完成 settings 注入")

    # 5) 落盘
    os.makedirs(args.out, exist_ok=True)
    slug = re.sub(r'[\\/:*?"<>|\s]+', "_", f"{brand.get('brand','brand')}_{args.project}")
    zip_path = os.path.join(args.out, f"{slug}_全景导览.zip")
    with open(zip_path, "wb") as f:
        f.write(raw)
    print(f"✓ ZIP：{zip_path}")

    view_dir = os.path.join(args.out, f"{slug}_web")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(view_dir)
    print(f"✓ 解压版：{view_dir}  （内含 index.html）")

    if ctl and not args.keep_server:
        ctl[0].terminate()
        print("· 已关闭自拉起的编辑器")

    print(f"\n本地预览：cd \"{view_dir}\" && python -m http.server 8124  → http://127.0.0.1:8124")


if __name__ == "__main__":
    main()
