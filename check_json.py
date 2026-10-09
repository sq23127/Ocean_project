# -*- coding: utf-8 -*-
# 检查解包生成的 JSON（分类文件 + 三合一文件）
import os
import math
import json

OUT_DIR = "02_Geojson"

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def stats(rows):
    vals = [x for row in rows for x in row if x is not None]
    nulls = sum(1 for row in rows for x in row if x is None)
    if not vals:
        return None
    return min(vals), max(vals), len(vals), nulls

def check(fname, fields):
    path = os.path.join(OUT_DIR, fname)
    print("=" * 56)
    print(path)
    if not os.path.exists(path):
        print("  [文件缺失，请先运行 build_json.py]")
        return
    d = load(path)
    print("  网格 %d x %d" % (d.get("nx", 0), d.get("ny", 0)))
    print("  范围 bounds =", d.get("bounds"))
    for key, label, unit in fields:
        if key not in d:
            print("  [缺字段] %s" % key)
            continue
        s = stats(d[key])
        if not s:
            print("  %s：无有效点" % label)
            continue
        print("  %-4s %8.3f ~ %8.3f %-4s | 有效 %d，空值 %d" %
              (label, s[0], s[1], unit, s[2], s[3]))
    if "u" in d and "v" in d:
        sp = [math.hypot(x, y)
              for ru, rv in zip(d["u"], d["v"])
              for x, y in zip(ru, rv)
              if x is not None and y is not None]
        if sp:
            print("  流速 %8.3f ~ %8.3f m/s" % (min(sp), max(sp)))

check("scs_temp.json",    [("temperature", "温度", "C")])
check("scs_sal.json",     [("salinity", "盐度", "PSU")])
check("scs_current.json", [("u", "u", "m/s"), ("v", "v", "m/s")])
check("scs_field.json",   [("temperature", "温度", "C"),
                           ("salinity", "盐度", "PSU"),
                           ("u", "u", "m/s"),
                           ("v", "v", "m/s")])
print("=" * 56)
print("检查完成。")
