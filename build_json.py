# -*- coding: utf-8 -*-
# 通用海洋数据解包器：
# 自动扫描 01_data/*.nc，识别 温度 / 盐度 / 海流(u,v) / 波浪WAM(swh,mwd,mwp)
# 无论数据是年、月、日、小时，都能识别时间层并选层；不同网格统一重采样对齐。
import os
import glob
import json
import numpy as np
import xarray as xr
from scipy.interpolate import griddata

# ================= 参数（一般只改这里）=================
W, E, S, N = 105.0, 128.0, 0.0, 42.0   # 中国海全域：西105 东128 南0(赤道/南沙) 北42(渤海北)
STEP = 0.1                              # 输出网格精度（度）
TIME_INDEX = 0                          # 取第几个时间层：0=最早，-1=最新；下了整年/多日就改这个数
WAVE_AGG = "month"                      # 波浪多时间层聚合：month月平均 / day日平均 / none取某层(TIME_INDEX)
DATA_DIR = "01_data"
OUT_DIR = "02_Geojson"

TIME_DIMS = ["time_counter", "valid_time", "time"]
DEPTH_DIMS = ["deptht", "depth", "level"]
LON_NAMES = ["nav_lon", "longitude", "lon"]
LAT_NAMES = ["nav_lat", "latitude", "lat"]

# 识别规则：(内部key, 输出字段, 变量名token, 中文标签)；按顺序匹配
RULES = [
    ("temperature", "temperature", ["sosstsst", "sea_surface_temperature", "sst"], "海表温度"),
    ("salinity",    "salinity",    ["sosaline", "sea_surface_salinity", "salinity"], "海表盐度"),
    ("u",           "u",           ["vozocrte", "uo"], "海流u(东向)"),
    ("v",           "v",           ["vomecrtn", "vo"], "海流v(北向)"),
    ("swh",         "swh",         ["swh", "significant_height_of_combined_wind_waves_and_swell"], "有效波高"),
    ("mwd",         "mwd",         ["mwd", "mean_wave_direction"], "平均波向"),
    ("mwp",         "mwp",         ["mwp", "pp1d", "mean_wave_period"], "平均波周期"),
]
FIELD_NAME = {r[0]: r[1] for r in RULES}
LABEL = {r[0]: r[3] for r in RULES}

def match_var(name):
    n = name.lower()
    for key, _, tokens, _ in RULES:
        for t in tokens:
            if n == t or (len(t) >= 4 and t in n):   # 短token(uo/vo/sst)只允许精确匹配
                return key
    return None

def find_dim(ds, candidates):
    for d in candidates:
        if d in ds.dims:
            return d
    return None

def get_coords(ds):
    lon_n = next((x for x in LON_NAMES if x in ds.variables), None)
    lat_n = next((x for x in LAT_NAMES if x in ds.variables), None)
    lon = ds[lon_n].values; lat = ds[lat_n].values
    if lon.ndim == 2:
        return lon, lat
    # 一维规则网格 -> 扩成二维
    LON2, LAT2 = np.meshgrid(lon, lat)
    return LON2, LAT2

def surface_values(da, ti, agg="none"):
    td = next((d for d in TIME_DIMS if d in da.dims), None)
    dd = next((d for d in DEPTH_DIMS if d in da.dims), None)

    # 多时间层聚合（主要用于逐小时海浪）
    if td and da.sizes[td] >= 2 and agg in ("month", "day"):
        tcoord = da[td]
        key = tcoord.dt.strftime("%Y-%m") if agg == "month" else tcoord.dt.floor("d")
        if match_var(da.name) == "mwd":           # 波向是环形量，先转矢量再平均
            ang = np.deg2rad(da)
            sx = np.sin(ang).groupby(key).mean(dim=td)
            cy = np.cos(ang).groupby(key).mean(dim=td)
            da = np.mod(np.rad2deg(np.arctan2(sx, cy)), 360.0)
        else:
            da = da.groupby(key).mean(dim=td)
        da = da.squeeze()

    idx = {}
    if td and td in da.dims:
        nt = da.sizes[td]
        idx[td] = ti if 0 <= ti < nt else nt - 1
    if dd and dd in da.dims:
        idx[dd] = 0
    if idx:
        da = da.isel(idx)
    return np.asarray(da.values, dtype=float)

def time_label(tvals, sel, ds):
    import pandas as pd
    t = pd.Timestamp(tvals[sel])
    if len(tvals) >= 2:
        dt = abs((pd.Timestamp(tvals[1]) - pd.Timestamp(tvals[0])).total_seconds())
        if dt >= 0.9 * 365 * 86400:
            return "%04d" % t.year
        if dt >= 25 * 86400:
            return "%04d-%02d" % (t.year, t.month)
        if dt >= 22 * 3600:
            return "%04d-%02d-%02d" % (t.year, t.month, t.day)
        return "%04d-%02d-%02dT%02d" % (t.year, t.month, t.day, t.hour)
    title = str(ds.attrs.get("title", "")).lower()
    if "monthly" in title:
        return "%04d-%02d" % (t.year, t.month)
    if "daily" in title:
        return "%04d-%02d-%02d" % (t.year, t.month, t.day)
    return np.datetime_as_string(tvals[sel], unit="s")

# ================= 主流程 =================
print("扫描目录：", DATA_DIR)
files = sorted(glob.glob(os.path.join(DATA_DIR, "*.nc")))
if not files:
    raise SystemExit("01_data 里没有 .nc 文件，请先下载放入。")

glon = np.arange(W, E + 1e-6, STEP)
glat = np.arange(S, N + 1e-6, STEP)
GLON, GLAT = np.meshgrid(glon, glat)

have = {}     # key -> 规则网格2D数组
time_str = None

for fp in files:
    name = os.path.basename(fp)
    try:
        ds = xr.open_dataset(fp, engine="h5netcdf")
    except Exception as e:
        print("  跳过（打不开）：%s %s" % (name, repr(e)[:60]))
        continue

    hits = {}
    for vn in ds.data_vars:
        k = match_var(vn)
        if k and k not in hits:
            hits[k] = vn
    if not hits:
        ds.close(); continue

    print("\n文件：", name)
    is_wave = bool({"swh", "mwd", "mwp"} & set(hits))
    agg = WAVE_AGG if (is_wave and WAVE_AGG in ("month", "day")) else "none"
    td = find_dim(ds, TIME_DIMS)
    if td is not None:
        tvals = ds[td].values
        _sel0 = TIME_INDEX if 0 <= TIME_INDEX < len(tvals) else len(tvals) - 1
        if agg in ("month", "day"):
            import pandas as pd
            tt = pd.Timestamp(tvals[_sel0])
            lab = ("%04d-%02d" % (tt.year, tt.month)) if agg == "month" \
                  else ("%04d-%02d-%02d" % (tt.year, tt.month, tt.day))
            print("  时间层 %d 个，按%s聚合 → %s" % (len(tvals), agg, lab))
        else:
            lab = time_label(tvals, _sel0, ds)
            print("  时间层 %d 个，取第 %d 层：%s" % (len(tvals), _sel0, lab))
        if time_str is None:
            time_str = lab

    lon2d, lat2d = get_coords(ds)
    cm = (lon2d >= W - 1) & (lon2d <= E + 1) & (lat2d >= S - 1) & (lat2d <= N + 1)
    if cm.sum() < 4:
        print("  该文件与目标海域无交集，跳过"); ds.close(); continue

    xc, yc = lon2d[cm], lat2d[cm]
    # 用第一个要素生成统一海陆掩膜（同文件坐标一致）
    first_v = ds[hits[list(hits)[0]]]
    fa = surface_values(first_v, TIME_INDEX, agg)[cm]
    oc = np.isfinite(fa).astype(float)
    mask_grid = griddata((xc, yc), oc, (GLON, GLAT), method="nearest")
    land = mask_grid < 0.5

    for k, vn in hits.items():
        z = surface_values(ds[vn], TIME_INDEX, agg)[cm]
        good = np.isfinite(z)
        if good.sum() < 4:
            print("  %s 有效点不足，跳过" % LABEL[k]); continue
        lin = griddata((xc[good], yc[good]), z[good], (GLON, GLAT), method="linear")
        lin[land] = np.nan
        have[k] = lin
        print("  %-8s 范围：%.3f ~ %.3f" % (LABEL[k], np.nanmin(lin), np.nanmax(lin)))
    ds.close()

if not have:
    raise SystemExit("没有在目标海域提取到任何要素，请检查数据或 W/E/S/N。")

# ================= 输出 JSON =================
def to_list(a):
    return [[None if not np.isfinite(x) else round(float(x), 4) for x in row] for row in a]

os.makedirs(OUT_DIR, exist_ok=True)
base = {"bounds": {"west": W, "east": E, "south": S, "north": N},
        "nx": len(glon), "ny": len(glat), "time": time_str}

def dump(fname, obj):
    p = os.path.join(OUT_DIR, fname)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    print("  已输出：", p)

field = dict(base)
for k, arr in have.items():
    field[FIELD_NAME[k]] = to_list(arr)

print("\n输出：")
dump("scs_field.json", field)
print("\n完成。已识别要素：%s" % "、".join(LABEL[k] for k in have))
