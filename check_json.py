# -*- coding: utf-8 -*-
# 通用 JSON 检查器：自动扫描 02_Geojson/*.json
# 检查 温度 / 盐度 / 海流(u,v) / 波浪WAM(swh,mwd,mwp)，识别时间精度（年/月/日/时刻）
import os
import re
import glob
import math
import json

OUT_DIR = "02_Geojson"

# 字段：(中文标签, 单位, 物理合理下限, 物理合理上限)
FIELDS = {
    "temperature": ("海表温度", "℃", -2.0, 40.0),
    "salinity":    ("海表盐度", "PSU", 0.0, 45.0),
    "u":           ("海流u(东向)", "m/s", -5.0, 5.0),
    "v":           ("海流v(北向)", "m/s", -5.0, 5.0),
    "swh":         ("有效波高", "m", 0.0, 25.0),
    "mwd":         ("平均波向", "°", 0.0, 360.0),
    "mwp":         ("平均波周期", "s", 0.0, 30.0),
}

def time_granularity(t):
    if not t:
        return "未提供"
    t = t.strip()
    if re.fullmatch(r"\d{4}", t): return "年"
    if re.fullmatch(r"\d{4}-\d{2}", t): return "月"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t): return "日"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[T ]\d{2}", t): return "小时"
    if re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", t): return "具体时刻"
    return "其它格式"

def collect(rows):
    vals, nulls = [], 0
    for row in rows:
        for x in row:
            if x is None: nulls += 1
            else: vals.append(x)
    return vals, nulls

def check_file(path):
    name = os.path.basename(path)
    print("=" * 60)
    print("文件：", name)
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    # ---- 结构 ----
    b = d.get("bounds"); nx = d.get("nx"); ny = d.get("ny")
    if not b or not nx or not ny:
        print("  [结构错误] 缺少 bounds / nx / ny")
        return
    print("  网格：%d × %d（经度×纬度）" % (nx, ny))
    print("  范围：西%s 东%s 南%s 北%s" %
          (b.get("west"), b.get("east"), b.get("south"), b.get("north")))
    t = d.get("time")
    print("  时间：%s  〔精度：%s〕" % (t or "—", time_granularity(t)))

    present = [k for k in FIELDS if k in d]
    if not present:
        print("  [警告] 文件里没有任何可识别要素字段")
        return

    for k in present:
        label, unit, lo, hi = FIELDS[k]
        grid = d[k]
        # 尺寸一致性
        if len(grid) != ny or any(len(r) != nx for r in grid):
            print("  %-10s [尺寸错误] 应为 %d 行×%d 列" % (label, ny, nx))
            continue
        vals, nulls = collect(grid)
        total = nx * ny
        if not vals:
            print("  %-10s 无有效点" % label); continue
        mn, mx = min(vals), max(vals)
        warn = ""
        if mn < lo or mx > hi:
            warn = "  ⚠ 超出常见物理范围(%g~%g)" % (lo, hi)
        print("  %-10s %8.3f ~ %8.3f %-4s | 有效 %d (%.1f%%)，空值 %d%s" %
              (label, mn, mx, unit, len(vals), 100.0 * len(vals) / total, nulls, warn))

    # ---- 海流配对：合成流速 ----
    if "u" in d and "v" in d:
        sp = [math.hypot(x, y) for ru, rv in zip(d["u"], d["v"])
              for x, y in zip(ru, rv) if x is not None and y is not None]
        if sp:
            print("  → 合成流速 %6.3f ~ %6.3f m/s" % (min(sp), max(sp)))

    # ---- 波浪：波向口径提示 ----
    if "mwd" in d:
        print("  → mwd 为波浪“来向”，前端已自动转传播方向(mwd-180)")

def main():
    files = sorted(glob.glob(os.path.join(OUT_DIR, "*.json")))
    if not files:
        print("%s 里没有 JSON，请先运行 build_json.py" % OUT_DIR)
        return
    for p in files:
        try:
            check_file(p)
        except Exception as e:
            print("  [检查失败] %s：%r" % (os.path.basename(p), e))
    print("=" * 60)
    print("检查完成。")

if __name__ == "__main__":
    main()
