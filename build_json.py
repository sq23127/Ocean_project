# -*- coding: utf-8 -*-
# 解包 ORAS5：生成 3 个分类 JSON（海温/盐度/海流uv）+ 1 个三合一 JSON
import os
import json
import numpy as np
import xarray as xr
from scipy.interpolate import griddata

# ===== 南海范围与网格精度（改海域/精度只改这里）=====
W, E, S, N = 105.0, 122.0, 0.0, 23.0
STEP = 0.1
OUT_DIR = "02_Geojson"

def open_ds(fn):
    return xr.open_dataset(fn, engine="h5netcdf")

dst = open_ds("01_data/oras5_temp.nc")
dss = open_ds("01_data/oras5_sal.nc")
dsu = open_ds("01_data/oras5_u.nc")
dsv = open_ds("01_data/oras5_v.nc")

navlon = dst["nav_lon"].values
navlat = dst["nav_lat"].values

# 温盐(2D)；u/v 取时间0、最浅表层(deptht=0)
temp = dst["sosstsst"].isel(time_counter=0).values
sal  = dss["sosaline"].isel(time_counter=0).values
u    = dsu["vozocrte"].isel(time_counter=0, deptht=0).values
v    = dsv["vomecrtn"].isel(time_counter=0, deptht=0).values

# 裁剪（留 1 度缓冲）
m = (navlon >= W - 1) & (navlon <= E + 1) & (navlat >= S - 1) & (navlat <= N + 1)
lonc, latc = navlon[m], navlat[m]
temp, sal, u, v = temp[m], sal[m], u[m], v[m]
ocean = np.isfinite(temp).astype(float)

# 规则目标网格
glon = np.arange(W, E + 1e-6, STEP)
glat = np.arange(S, N + 1e-6, STEP)
GLON, GLAT = np.meshgrid(glon, glat)

def regrid(a):
    return griddata((lonc, latc), a, (GLON, GLAT), method="linear")

gT = regrid(temp)
gS = regrid(sal)
gU = regrid(u)
gV = regrid(v)
# 海陆掩膜：陆地格子置空
gO = griddata((lonc, latc), ocean, (GLON, GLAT), method="nearest")
land = gO < 0.5
for g in (gT, gS, gU, gV):
    g[land] = np.nan

print("规则网格：经度 %d，纬度 %d" % (len(glon), len(glat)))
print("温度 %.2f~%.2f C | 盐度 %.2f~%.2f PSU" %
      (np.nanmin(gT), np.nanmax(gT), np.nanmin(gS), np.nanmax(gS)))
spd = np.sqrt(gU ** 2 + gV ** 2)
print("流速 %.3f~%.3f m/s | 陆地格子 %d/%d" %
      (np.nanmin(spd), np.nanmax(spd), land.sum(), land.size))

def to_list(a):
    return [[None if not np.isfinite(x) else round(float(x), 4) for x in row] for row in a]

base = {
    "bounds": {"west": W, "east": E, "south": S, "north": N},
    "nx": len(glon), "ny": len(glat),
}
T = to_list(gT); S2 = to_list(gS); U2 = to_list(gU); V2 = to_list(gV)

os.makedirs(OUT_DIR, exist_ok=True)
def write_json(name, obj):
    p = os.path.join(OUT_DIR, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    print("已输出：", p)

# 三个分类文件
write_json("scs_temp.json",    dict(base, temperature=T))
write_json("scs_sal.json",     dict(base, salinity=S2))
write_json("scs_current.json", dict(base, u=U2, v=V2))
# 一个三合一文件
write_json("scs_field.json", dict(base, temperature=T, salinity=S2, u=U2, v=V2))
print("全部完成。")
