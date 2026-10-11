# -*- coding: utf-8 -*-
# 通用格式转换文件：读取 02_Geojson/scs_field.json，内嵌进自带网页模板，
# 生成 index_standalone.html（双击即可打开，无需服务器/联网安装）。
import os

DATA = "02_Geojson/scs_field.json"
OUT = "index_standalone.html"
MARK = "const EMBEDDED_DATA = null; // pack_standalone.py 会把 null 替换为真实数据对象"

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>中国海域三维可视化演示</title>
<script>window.CESIUM_BASE_URL="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/";</script>
<script src="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Cesium.js"></script>
<link href="https://cesium.com/downloads/cesiumjs/releases/1.118/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
<style>
  html,body,#cesiumContainer{width:100%;height:100%;margin:0;padding:0;font-family:"Microsoft YaHei",sans-serif;}
  .box{background:rgba(30,40,60,.10);border-radius:10px;color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.45);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
  #panel{position:absolute;top:12px;left:12px;z-index:999;padding:14px;width:218px;max-height:calc(100vh - 24px);overflow-y:auto;box-sizing:border-box;}
  #panel h3{margin:0 0 10px;font-size:15px;border-bottom:1px solid rgba(255,255,255,.25);padding-bottom:8px;}
  #panel button{width:100%;margin:4px 0;padding:9px 6px;border:none;border-radius:10px;cursor:pointer;background:#15b8d0;color:#fff;font-size:13px;transition:background .2s,transform .08s;}
  #panel button:hover{background:#4d86c4;}
  #panel button:active{transform:scale(.97);}
  #panel button.active{background:#e08a2e;}
  #panel button.imp{background:#DD1D3A;} #panel button.imp:hover{background: #920d23;}
  #panel button.imp.main{background:#86AB21;} #panel button.imp.main:hover{background:#2f9558;}
  #panel h4{margin:12px 0 6px;font-size:13px;color:#cdd9ea;font-weight:normal;}
  .btngrid{display:grid;grid-template-columns:1fr 1fr;gap:6px;}
  .btngrid button{margin:0;padding:11px 2px;font-size:12px;border-radius:8px;line-height:1.2;}
  #status{font-size:11px;color:#9fe89f;margin:6px 1px;min-height:15px;word-break:break-all;}
  #title{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:998;color:#fff;font-size:19px;font-weight:bold;text-shadow:0 2px 6px rgba(0,0,0,.85);letter-spacing:1px;}
  #legend{position:absolute;bottom:24px;right:16px;z-index:999;padding:10px 12px;font-size:12px;display:none;}
  #legend .bar{width:190px;height:14px;border-radius:3px;margin:6px 0;background:linear-gradient(to right,rgb(0,0,255),rgb(0,255,255),rgb(0,255,0),rgb(255,255,0),rgb(255,0,0));}
  #legend .lab{display:flex;justify-content:space-between;}
  #infoBox{position:absolute;bottom:42px;left:12px;z-index:999;padding:10px 12px;font-size:12px;width:220px;}
  #infoBox .t{font-size:13px;font-weight:bold;border-bottom:1px solid rgba(255,255,255,.25);padding-bottom:5px;margin-bottom:6px;}
  #infoBox .r{display:flex;justify-content:space-between;margin:3px 0;} #infoBox .r b{color:#7fd4ff;font-weight:normal;}
  #infoBox .hint{color:#aab;font-size:11px;margin-top:5px;}
  #hoverTip{position:absolute;bottom:120px;right:16px;z-index:999;padding:11px 13px;font-size:12px;width:218px;display:none;border:1px solid rgba(127,212,255,.35);}
  #hoverTip .t{font-size:13px;font-weight:bold;color:#7fd4ff;border-bottom:1px solid rgba(255,255,255,.2);padding-bottom:5px;margin-bottom:6px;}
  #hoverTip .r{display:flex;justify-content:space-between;margin:3px 0;} #hoverTip .r b{font-weight:normal;color:#e8f4ff;}
</style>
</head>
<body>
<div id="title">cesium三维可视化演示</div>
<div id="cesiumContainer"></div>

<div id="panel" class="box">
  <h3>数据加载与显示</h3>
  <h4>① 导入数据（可分类导入，自动合并）</h4>
  <button class="imp main" id="impField">导入 三合一（温盐流）</button>
  <button class="imp" id="impCur">导入 海流（u/v）</button>
  <button class="imp" id="impTemp">导入 海温</button>
  <button class="imp" id="impSal">导入 盐度</button>
  <button class="imp" id="impWave">导入 波浪（WAM）</button>
  <input type="file" id="fileInput" accept=".json,application/json" style="display:none">
  <div id="status">正在载入内嵌数据…</div>
  <h4>② 显示</h4>
  <div class="btngrid">
    <button data-mode="temp">温度</button>
    <button data-mode="sal">盐度</button>
    <button data-mode="particle">海流粒子</button>
    <button data-mode="swh">波高</button>
    <button data-mode="waveparticle">波浪粒子</button>
    <button data-mode="clear">全部清除</button>
  </div>
</div>

<div id="legend" class="box">
  <div id="legendName"></div>
  <div class="bar"></div>
  <div class="lab"><span id="legendMin"></span><span id="legendMax"></span></div>
</div>

<div id="infoBox" class="box">
  <div class="t">数据信息</div>
  <div class="r"><span>数据日期</span><b id="dataDate">—</b></div>
  <div class="r"><span>数据来源</span><b id="dataSource">ECMWF（ORAS5）</b></div>
  <div class="r"><span>经度</span><b id="curLon">--</b></div>
  <div class="r"><span>纬度</span><b id="curLat">--</b></div>
  <div class="hint">先导入数据文件，再点上方按钮显示；鼠标移动可看坐标和该点数据</div>
</div>

<div id="hoverTip" class="box">
  <div class="t">该点实时数据</div>
  <div class="r"><span>经度 / 纬度</span><b id="htPos"></b></div>
  <div class="r"><span>温度</span><b id="htTemp"></b></div>
  <div class="r"><span>盐度</span><b id="htSal"></b></div>
  <div class="r"><span>流速</span><b id="htSpeed"></b></div>
  <div class="r"><span>u / v</span><b id="htUV"></b></div>
  <div class="r"><span>波高</span><b id="htSwh"></b></div>
</div>

<script>
// ================= 1. 初始化 =================
Cesium.Ion.defaultAccessToken="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IkcxbnhWV2c3ZXc3RmNvMFkiLCJqdGkiOiIyYTBlZjJlMS1kMWE2LTRhN2UtYTE4OC02MWEyOGUxYWY4NmIiLCJpZCI6NTEzNjc0LCJzdWIiOiLmooHor5fnkKoiLCJpc3MiOiJodHRwczovL2FwaS5jZXNpdW0uY29tIiwiYXVkIjoib2NlYW5feWVsbG93c2VhIiwiaWF0IjoxNzkxMjYxOTM5fQ.K-p5r8_9EEsXJYXxO7tveKV8kM9OvKCNH4VNxUqc-6I";

const viewer=new Cesium.Viewer("cesiumContainer",{
  animation:false,timeline:false,baseLayerPicker:false,geocoder:false,
  sceneModePicker:true,navigationHelpButton:false,fullscreenButton:false,
  homeButton:false,infoBox:false,selectionIndicator:false
});
viewer.useBrowserRecommendedResolution=false;
viewer.resolutionScale=1.0;
viewer.scene.fxaa=false;
viewer.scene.msaaSamples=4;
viewer.scene.globe.baseColor=Cesium.Color.fromCssColorString("#0a2a43");
viewer.camera.setView({destination:Cesium.Rectangle.fromDegrees(105,0,122,23)});

// ================= 2. 网格基础 / 采样 =================
let G=null;
function setupGrid(d){
  const b=d.bounds,nx=d.nx,ny=d.ny;
  G={b,nx,ny,dLon:(b.east-b.west)/(nx-1),dLat:(b.north-b.south)/(ny-1)};
}
function bil(grid,fi,fj){
  if(!grid)return null;
  const nx=G.nx,ny=G.ny;
  const i0=Math.floor(fi),j0=Math.floor(fj),ti=fi-i0,tj=fj-j0;
  function a(j,i){if(i<0||i>=nx||j<0||j>=ny)return null;return grid[j][i];}
  const v00=a(j0,i0),v10=a(j0,i0+1),v01=a(j0+1,i0),v11=a(j0+1,i0+1);
  if(v00===null||v10===null||v01===null||v11===null)return null;
  return (v00*(1-ti)+v10*ti)*(1-tj)+(v01*(1-ti)+v11*ti)*tj;
}
function lonLat(fi,fj){return {lon:G.b.west+fi*G.dLon,lat:G.b.south+fj*G.dLat};}
function isOcean(fi,fj){return pOcean?bil(pOcean,fi,fj)!==null:false;}
function hasTemp(){return data&&!!data.temperature;}
function hasSal(){return data&&!!data.salinity;}
function hasCur(){return data&&!!data.u&&!!data.v;}
function hasWave(){return data&&!!data.swh&&!!data.mwd;}
function sampLL(grid,lon,lat){return bil(grid,(lon-G.b.west)/G.dLon,(lat-G.b.south)/G.dLat);}

// ================= 3. 颜色 =================
const STOPS=[[0,0,1],[0,1,1],[0,1,0],[1,1,0],[1,0,0]];
function colorAt(t,a){
  t=Math.max(0,Math.min(1,t));
  const seg=t*(STOPS.length-1),i=Math.floor(seg),f=seg-i;
  const x=STOPS[i],y=STOPS[Math.min(i+1,4)];
  return new Cesium.Color(x[0]+(y[0]-x[0])*f,x[1]+(y[1]-x[1])*f,x[2]+(y[2]-x[2])*f,a==null?1:a);
}
function fieldRange(grid){
  let mn=Infinity,mx=-Infinity;
  for(const row of grid)for(const v of row){if(v===null)continue;if(v<mn)mn=v;if(v>mx)mx=v;}
  return [mn,mx];
}

// ================= 4. 连续色面 =================
const layers={};
function rasterize(grid,maxSide){
  const b=G.b,aspect=(b.east-b.west)/(b.north-b.south);
  let W,H;
  if(aspect>=1){W=maxSide;H=Math.round(maxSide/aspect);}else{H=maxSide;W=Math.round(maxSide*aspect);}
  const canvas=document.createElement("canvas");canvas.width=W;canvas.height=H;
  const ctx=canvas.getContext("2d"),img=ctx.createImageData(W,H);
  const rr=fieldRange(grid),mn=rr[0],mx=rr[1];
  const FEATHER=4; // 外边界羽化宽度（网格数）
  for(let py=0;py<H;py++){
    const fj=(G.ny-1)*(1-(py+0.5)/H);
    for(let px=0;px<W;px++){
      const fi=(G.nx-1)*((px+0.5)/W);
      const o=(py*W+px)*4;
      const i0=Math.floor(fi),j0=Math.floor(fj),ti=fi-i0,tj=fj-j0;
      const w00=(1-ti)*(1-tj),w10=ti*(1-tj),w01=(1-ti)*tj,w11=ti*tj;
      function cg(j,i){if(i<0||i>=G.nx||j<0||j>=G.ny)return null;return grid[j][i];}
      const c00=cg(j0,i0),c10=cg(j0,i0+1),c01=cg(j0+1,i0),c11=cg(j0+1,i0+1);
      let Wsum=0,Vsum=0,valid=0;
      [[c00,w00],[c10,w10],[c01,w01],[c11,w11]].forEach(function(q){
        if(q[0]!==null){Wsum+=q[1];Vsum+=q[0]*q[1];valid+=q[1];}
      });
      if(Wsum<=0){img.data[o+3]=0;continue;}
      const v=Vsum/Wsum;
      const di=Math.min(fi,G.nx-1-fi),dj=Math.min(fj,G.ny-1-fj);
      const edge=Math.max(0,Math.min(1,Math.min(di,dj)/FEATHER));
      const a=valid*edge; // 海岸 + 外边界柔和淡化
      if(a<=0.004){img.data[o+3]=0;continue;}
      const c=colorAt((v-mn)/(mx-mn),1);
      img.data[o]=c.red*255;img.data[o+1]=c.green*255;img.data[o+2]=c.blue*255;
      img.data[o+3]=Math.round(255*a*0.8);
    }
  }
  ctx.putImageData(img,0,0);
  return {canvas,mn,mx};
}
async function showSurface(mode,grid,name,unit){
  removeSurface(mode);
  const r=rasterize(grid,2048),canvas=r.canvas,mn=r.mn,mx=r.mx;
  const url=await new Promise(res=>canvas.toBlob(bl=>res(URL.createObjectURL(bl)),"image/png"));
  const b=G.b;
  const provider=await Cesium.SingleTileImageryProvider.fromUrl(url,
    {rectangle:Cesium.Rectangle.fromDegrees(b.west,b.south,b.east,b.north)});
  const layer=viewer.imageryLayers.addImageryProvider(provider);
  layers[mode]={layer,url};
  document.getElementById("legend").style.display="block";
  document.getElementById("legendName").textContent=name+"（"+unit+"）";
  document.getElementById("legendMin").textContent=mn.toFixed(2);
  document.getElementById("legendMax").textContent=mx.toFixed(2);
}
function removeSurface(mode){
  if(layers[mode]){viewer.imageryLayers.remove(layers[mode].layer,true);URL.revokeObjectURL(layers[mode].url);delete layers[mode];}
}

// ============ 精细海岸线遮罩（Cesium 世界地形；温度/盐度共用，仅生成一次）============
let _tp=null,_cmask=null,_csize=null;
async function getTerrain(){
  if(_tp!==null)return _tp;
  try{_tp=await Cesium.createWorldTerrainAsync({requestVertexNormals:false,requestWaterMask:false});}
  catch(e){console.log("世界地形加载失败：",e);_tp=false;}
  return _tp;
}
async function coastMask(W,H){
  if(_cmask&&_csize&&_csize[0]===W&&_csize[1]===H)return _cmask;
  const tp=await getTerrain(),b=G.b;
  const SCALE=2; // 每2个贴面像素采一个地形点
  const mw=Math.max(2,Math.round(W/SCALE)),mh=Math.max(2,Math.round(H/SCALE));
  const small=document.createElement("canvas");small.width=mw;small.height=mh;
  const sx=small.getContext("2d"),si=sx.createImageData(mw,mh);
  if(tp){
    const pts=[];
    for(let my=0;my<mh;my++){const lat=b.north-(my+0.5)*(b.north-b.south)/mh;
      for(let mx=0;mx<mw;mx++){const lon=b.west+(mx+0.5)*(b.east-b.west)/mw;
        pts.push({my,mx,h:null,c:Cesium.Cartographic.fromDegrees(lon,lat)});}}
    const BATCH=15000;
    for(let k=0;k<pts.length;k+=BATCH){
      const bs=pts.slice(k,k+BATCH);
      try{const rr=await Cesium.sampleTerrain(tp,15,bs.map(q=>q.c));
        bs.forEach((q,i)=>{q.h=rr[i].height;});
      }catch(e){console.log("地形采样失败：",e);break;}
    }
    for(const p of pts){const oo=(p.my*mw+p.mx)*4;
      if(p.h!==null&&p.h>0){si.data[oo]=255;si.data[oo+1]=255;si.data[oo+2]=255;si.data[oo+3]=255;} // 陆地白
      else si.data[oo+3]=0;}
  }
  sx.putImageData(si,0,0);
  const big=document.createElement("canvas");big.width=W;big.height=H;
  const bx=big.getContext("2d");bx.imageSmoothingEnabled=true;bx.imageSmoothingQuality="high";
  bx.drawImage(small,0,0,W,H); // 放大并软边抗锯齿
  _cmask=big;_csize=[W,H];
  return big;
}
async function applyCoast(canvas){
  const m=await coastMask(canvas.width,canvas.height);
  if(!m)return;
  const cx=canvas.getContext("2d");
  cx.globalCompositeOperation="destination-out";
  cx.drawImage(m,0,0);
  cx.globalCompositeOperation="source-over";
}

// ================= 5. 真实海流粒子（RK2）=================
const R_EARTH=6371008.8, P_HEIGHT=60;
let pc=null,segLines=[],remover=null,parts=[],spMax=1;
let pU=null,pV=null,pOcean=null,pKind="current";
const P_N=900,TRAIL=6,SEG=TRAIL-1,DT=8*3600;
function hideAll(arr){for(const ln of arr)ln.show=false;}

function randFi(){
  for(let k=0;k<40;k++){
    const fi=Math.random()*(G.nx-2),fj=Math.random()*(G.ny-2);
    if(isOcean(fi,fj))return {fi,fj};
  }
  return null;
}
function buildWaveUV(vs){
  const ny=G.ny,nx=G.nx,wU=new Array(ny),wV=new Array(ny);
  for(let j=0;j<ny;j++){wU[j]=new Array(nx);wV[j]=new Array(nx);
    for(let i=0;i<nx;i++){
      const m=data.mwd[j][i];
      if(m===null){wU[j][i]=null;wV[j][i]=null;continue;}
      const dir=(m-180)*Math.PI/180;
      wU[j][i]=Math.sin(dir)*vs; wV[j][i]=Math.cos(dir)*vs;
    }}
  return {wU:wU,wV:wV};
}
function startParticles(kind){
  stopParticles();
  pKind=kind||"current";
  let sg;
  if(pKind==="wave"){
    const r=buildWaveUV(0.6); pU=r.wU; pV=r.wV; pOcean=data.swh; spMax=0.6;
  }else{
    pU=data.u;pV=data.v;pOcean=data.temperature||data.u;
    sg=new Array(G.ny);
  for(let j=0;j<G.ny;j++){sg[j]=new Array(G.nx);for(let i=0;i<G.nx;i++){const u=data.u[j][i],v=data.v[j][i];sg[j][i]=(u===null||v===null)?null:Math.sqrt(u*u+v*v);}}
    spMax=fieldRange(sg)[1]||1;
  }
  pc=new Cesium.PolylineCollection();
  viewer.scene.primitives.add(pc);
  parts=[];segLines=[];
  for(let i=0;i<P_N;i++){
    const o=randFi();
    parts.push(o?{fi:o.fi,fj:o.fj,trail:[{fi:o.fi,fj:o.fj}]}:null);
    const arr=[];
    for(let s=0;s<SEG;s++){
      const w=0.4+Math.pow(s/(SEG-1),1.3)*2.6; // 尾细头粗（固定）
      const ln=pc.add({positions:Cesium.Cartesian3.fromDegreesArray([0,0,0,0]),width:w,material:Cesium.Material.fromType("Color",{color:Cesium.Color.WHITE})});
      ln.show=false;arr.push(ln);
    }
    segLines.push(arr);
  }
  let _pf=0;
  remover=viewer.scene.postRender.addEventListener(function(){_pf++;if(_pf%2===1)return;step();}); // 隔帧推进，省一半计算
  document.getElementById("legend").style.display="block";
  if(pKind==="wave"){
    document.getElementById("legendName").textContent="波浪传播方向（WAM）";
    document.getElementById("legendMin").textContent="—";
    document.getElementById("legendMax").textContent="—";
  }else{
    document.getElementById("legendName").textContent="海流速度（m/s）";
    document.getElementById("legendMin").textContent="0.00";
    document.getElementById("legendMax").textContent=spMax.toFixed(2);
  }
}
function drift(fi,fj,u,v){
  const ll=lonLat(fi,fj),cos=Math.cos(ll.lat*Math.PI/180);
  return {dfi:(u*DT)/(R_EARTH*cos)*180/Math.PI/G.dLon,
          dfj:(v*DT)/R_EARTH*180/Math.PI/G.dLat};
}
function step(){
  for(let i=0;i<P_N;i++){
    let p=parts[i];const arr=segLines[i];
    if(!p){const o=randFi();if(o)p={fi:o.fi,fj:o.fj,trail:[{fi:o.fi,fj:o.fj}]};parts[i]=p;if(!p){hideAll(arr);continue;}}
    const u1=bil(pU,p.fi,p.fj),v1=bil(pV,p.fi,p.fj);
    if(u1===null||v1===null){parts[i]=null;hideAll(arr);continue;}
    const d1=drift(p.fi,p.fj,u1,v1);
    const u2=bil(pU,p.fi+d1.dfi/2,p.fj+d1.dfj/2)||u1;
    const v2=bil(pV,p.fi+d1.dfi/2,p.fj+d1.dfj/2)||v1;
    const d2=drift(p.fi,p.fj,u2,v2);
    p.fi+=d2.dfi;p.fj+=d2.dfj;
    if(p.fi<0||p.fi>G.nx-1||p.fj<0||p.fj>G.ny-1||!isOcean(p.fi,p.fj)){parts[i]=null;hideAll(arr);continue;}
    p.trail.push({fi:p.fi,fj:p.fj});
    if(p.trail.length>TRAIL)p.trail.shift();
    const sp=Math.sqrt(u2*u2+v2*v2);
    for(let s=0;s<SEG;s++){
      const ln=arr[s];
      if(s<p.trail.length-1){
        const A=p.trail[s],B=p.trail[s+1],la=lonLat(A.fi,A.fj),lb=lonLat(B.fi,B.fj);
        ln.positions=Cesium.Cartesian3.fromDegreesArray([la.lon,la.lat,lb.lon,lb.lat]);
        const al=Math.pow((s+1)/SEG,1.6)*0.95;
        ln.material.uniforms.color=pKind==="wave"?new Cesium.Color(0.7,0.9,1.0,al):colorAt(sp/spMax,al);
        ln.show=true;
      } else ln.show=false;
    }
  }
}
function stopParticles(){
  if(remover){remover();remover=null;}
  if(pc){viewer.scene.primitives.remove(pc);pc=null;}
  parts=[];segLines=[];
}

// ================= 6. 按钮 =================
let data=null;
document.querySelectorAll("#panel button[data-mode]").forEach(btn=>btn.addEventListener("click",()=>{
  const mode=btn.dataset.mode;
  document.querySelectorAll("#panel button[data-mode]").forEach(b=>b.classList.remove("active"));
  if(mode==="clear"){clearAll();return;}
  if(!data){alert("请先在上方导入数据");return;}
  if(mode==="temp"){if(!hasTemp()){alert("还没导入海温，请点「导入 海温」或三合一");return;}showSurface("temp",data.temperature,"海表温度","℃");}
  else if(mode==="sal"){if(!hasSal()){alert("还没导入盐度，请点「导入 盐度」或三合一");return;}showSurface("sal",data.salinity,"海表盐度","PSU");}
  else if(mode==="particle"){if(!hasCur()){alert("还没导入海流，请点「导入 海流」或三合一");return;}startParticles("current");}
  else if(mode==="swh"){if(!hasWave()){alert("还没导入波浪，请点「导入 波浪（WAM）」");return;}showSurface("swh",data.swh,"有效波高","m");}
  else if(mode==="waveparticle"){if(!hasWave()){alert("还没导入波浪，请点「导入 波浪（WAM）」");return;}startParticles("wave");}
  btn.classList.add("active");
}));
function clearAll(){removeSurface("temp");removeSurface("sal");removeSurface("swh");stopParticles();document.getElementById("legend").style.display="none";}

// ================= 7. 数据：内嵌 + 分类导入合并 =================
const EMBEDDED_DATA = null; // pack_standalone.py 会把 null 替换为真实数据对象
function applyData(d,kind){
  if(kind==="field"||!data){
    data={bounds:d.bounds,nx:d.nx,ny:d.ny,
      temperature:d.temperature||null,salinity:d.salinity||null,
      u:d.u||null,v:d.v||null,
      swh:d.swh||null,mwd:d.mwd||null,mwp:d.mwp||null};
  }else{
    if(d.temperature)data.temperature=d.temperature;
    if(d.salinity)data.salinity=d.salinity;
    if(d.u){data.u=d.u;data.v=d.v;}
    if(d.swh)data.swh=d.swh;
    if(d.mwd)data.mwd=d.mwd;
    if(d.mwp)data.mwp=d.mwp;
  }
  setupGrid(data);refreshStatus();
}
function refreshStatus(){
  const a=[];
  if(hasTemp())a.push("温度");if(hasSal())a.push("盐度");if(hasCur())a.push("海流");if(hasWave())a.push("波浪");
  document.getElementById("status").textContent=
    a.length?("已有："+a.join("、")+"；网格 "+data.nx+"×"+data.ny):"尚无数据";
}
const fi2=document.getElementById("fileInput");
let pendingKind="field";
function bindImport(id,kind){document.getElementById(id).addEventListener("click",function(){pendingKind=kind;fi2.click();});}
bindImport("impField","field");bindImport("impCur","current");bindImport("impTemp","temp");bindImport("impSal","sal");bindImport("impWave","wave");
function parseDate(n){const m=n.match(/(\d{4})\D?(\d{2})\D?(\d{2})(?:\D?(\d{2}))?/);return m?m[1]+"-"+m[2]+"-"+m[3]+" "+(m[4]?m[4]:"00")+":00":null;}
fi2.addEventListener("change",function(){
  const file=this.files[0];if(!file)return;
  const rd=new FileReader();
  rd.onload=function(){
    let d;try{d=JSON.parse(rd.result);}catch(e){alert("不是合法 JSON");return;}
    if(!d.bounds||!d.nx||!d.ny){alert("结构不对，请用 build_json.py 生成的 JSON");return;}
    if(!d.temperature&&!d.salinity&&!d.u&&!d.swh&&!d.mwd){alert("这个文件里没有可用要素");return;}
    clearAll();applyData(d,pendingKind);
    const dt=d.time||parseDate(file.name);
    document.getElementById("dataDate").textContent=d.time?(d.time+"（月平均）"):(dt||"（文件名未含日期）");
  };
  rd.readAsText(file);this.value="";
});
// 内嵌数据：独立网页打开即带数据
if(EMBEDDED_DATA){
  applyData(EMBEDDED_DATA,"field");
  document.getElementById("dataDate").textContent=EMBEDDED_DATA.time?(EMBEDDED_DATA.time+"（月平均）"):"—";
}else{
  document.getElementById("status").textContent="无内嵌数据，请点上方按钮导入";
}

// ================= 8. 鼠标坐标 + 该点数据 =================
const hh=new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
function fmt(v,u,d){if(v===null||v===undefined)return"—";return v.toFixed(d==null?2:d)+" "+u;}
hh.setInputAction(function(mv){
  const cart=viewer.camera.pickEllipsoid(mv.endPosition,viewer.scene.globe.ellipsoid);
  if(!cart||!data){document.getElementById("hoverTip").style.display="none";return;}
  const c=Cesium.Cartographic.fromCartesian(cart);
  const lon=Cesium.Math.toDegrees(c.longitude),lat=Cesium.Math.toDegrees(c.latitude);
  document.getElementById("curLon").textContent=lon.toFixed(3)+"°";
  document.getElementById("curLat").textContent=lat.toFixed(3)+"°";
  const b=G.b;
  if(lon>=b.west&&lon<=b.east&&lat>=b.south&&lat<=b.north){
    const t=sampLL(data.temperature,lon,lat),s=sampLL(data.salinity,lon,lat);
    const u=sampLL(data.u,lon,lat),v=sampLL(data.v,lon,lat);
    document.getElementById("htPos").textContent=lon.toFixed(2)+"°,"+lat.toFixed(2)+"°";
    document.getElementById("htTemp").textContent=fmt(t,"℃");
    document.getElementById("htSal").textContent=fmt(s,"PSU");
    document.getElementById("htSpeed").textContent=(u!==null&&v!==null)?fmt(Math.sqrt(u*u+v*v),"m/s",3):"—";
    document.getElementById("htUV").textContent=(u!==null)?u.toFixed(3)+" / "+v.toFixed(3):"—";
    document.getElementById("htSwh").textContent=fmt(sampLL(data.swh,lon,lat),"m");
    document.getElementById("hoverTip").style.display="block";
  } else document.getElementById("hoverTip").style.display="none";
},Cesium.ScreenSpaceEventType.MOUSE_MOVE);
</script>
</body>
</html>'''

if not os.path.exists(DATA):
    raise SystemExit("没找到 %s，请先运行 build_json.py" % DATA)
with open(DATA, encoding="utf-8") as f:
    data_text = f.read()
if MARK not in TEMPLATE:
    raise SystemExit("自带模板里没找到占位标记")
html = TEMPLATE.replace(MARK, "const EMBEDDED_DATA = " + data_text + ";", 1)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("已输出：", os.path.abspath(OUT))
print("文件大小：%.2f MB" % (os.path.getsize(OUT) / 1048576))
