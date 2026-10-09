# -*- coding: utf-8 -*-
# 打包独立网页：把 scs_field.json 内嵌进 index_southsea.html → index_standalone.html
import os

TEMPLATE = "index_southsea.html"
DATA = "02_Geojson/scs_field.json"
OUT = "index_standalone.html"
MARK = "const EMBEDDED_DATA = null;"

with open(TEMPLATE, encoding="utf-8") as f:
    html = f.read()
with open(DATA, encoding="utf-8") as f:
    data_text = f.read()

if MARK not in html:
    raise SystemExit("没找到占位标记，请确认 index_southsea.html 是最新版")

html = html.replace(MARK, "const EMBEDDED_DATA = " + data_text + ";", 1)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("已输出：", os.path.abspath(OUT))
print("文件大小：%.2f MB" % (os.path.getsize(OUT) / 1048576))
