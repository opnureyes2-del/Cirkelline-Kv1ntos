import { useState, useMemo, useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════
   KV1NTOS v5 · ADMIRAL OPERATIONS CENTER
   Chat-paste · Desktop integration · Live review · Intelligent søgning
   ═══════════════════════════════════════════════════════════════ */

// ─── DATA ────────────────────────────────────────────────────
const INIT={
  phases:[
    {id:0,n:"DISCOVERY",s:"I GANG",d:"Find ALT. Antag INTET.",v:"Fund klassificeret + godkendt"},
    {id:1,n:"OPRYDNING",s:"VENTER",d:"Fjern ødelagt. Bevar fungerende.",v:"docker ps = kun nødvendige"},
    {id:2,n:"FUNDAMENT",s:"VENTER",d:"Docker, netværk, Git.",v:"Docker+Compose+Git rent"},
    {id:3,n:"OBSERVABILITY",s:"VENTER",d:"Prometheus, Loki, Tempo, Grafana.",v:"Grafana fejlfri"},
    {id:4,n:"AI-MODELLER",s:"VENTER",d:"Ollama, Claude, Gemini.",v:"Rate-limiter aktiv"},
    {id:5,n:"ODIN",s:"VENTER",d:"Videnbase, regler, agenter.",v:"Kommandokæde fungerer"},
    {id:6,n:"INTEGRATION",s:"VENTER",d:"Forbind systemer.",v:"Grafana bekræfter"},
    {id:7,n:"PROJEKTER",s:"VENTER",d:"BØRNESKABER, Three Realms, Gaming.",v:"Stabilt i prod"},
  ],
  items:[
    {id:"SVC-001",nm:"Docker Engine",tp:"SVC",pt:"socket",st:"AFVENTER SCAN",ct:"CORE",ph:2,bg:["A4","B5","C7"],dp:[],db:["SVC-002","SVC-003","SVC-004","SVC-005","SVC-006","SVC-007","SVC-008"],hc:"systemctl status docker",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-002",nm:"Prometheus",tp:"SVC",pt:"9090",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:9090/-/healthy",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-003",nm:"Loki",tp:"SVC",pt:"3100",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:3100/ready",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-004",nm:"Grafana",tp:"SVC",pt:"3000",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","B7","C10"],dp:["SVC-001","SVC-002","SVC-003"],db:[],hc:"curl localhost:3000/api/health",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-005",nm:"Tempo",tp:"SVC",pt:"3200",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:3200/ready",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-006",nm:"Alertmanager",tp:"SVC",pt:"9093",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7"],dp:["SVC-001","SVC-002"],db:[],hc:"curl localhost:9093/-/healthy",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-007",nm:"n8n",tp:"SVC",pt:"5678",st:"AFVENTER SCAN",ct:"AUTO",ph:6,bg:[],dp:["SVC-001"],db:[],hc:"curl localhost:5678/healthz",nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-008",nm:"Ollama",tp:"SVC",pt:"11434",st:"AFVENTER SCAN",ct:"AI",ph:4,bg:[],dp:[],db:[],hc:"curl localhost:11434",nt:"",pin:false,ann:[],docs:[]},
    {id:"PLT-001",nm:"Cirkelline",tp:"PLT",pt:"7777",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B1","C1","D2"],dp:[],db:[],hc:"",nt:"db:PostgreSQL:5533",pin:false,ann:[],docs:[]},
    {id:"PLT-002",nm:"Cosmic Library",tp:"PLT",pt:"7778",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B2","C2","D3"],dp:[],db:[],hc:"",nt:"db:PostgreSQL:5534",pin:false,ann:[],docs:[]},
    {id:"PLT-003",nm:"CKC Gateway",tp:"PLT",pt:"7779",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B3","C3","D4"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]},
    {id:"PLT-004",nm:"Kommandør",tp:"PLT",pt:"7800",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B4","C4","D5"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]},
    {id:"PLT-005",nm:"BØRNESKABER",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"Genesis: farver,lyde,tegn",pin:false,ann:[],docs:[]},
    {id:"PLT-006",nm:"Three Realms",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"GPS+1825/nu/2050",pin:false,ann:[],docs:[]},
    {id:"PLT-007",nm:"Gaming Platform",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"Steam-kvalitet",pin:false,ann:[],docs:[]},
    {id:"API-001",nm:"Claude (privat)",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"opus/sonnet/haiku|max3",pin:false,ann:[],docs:[]},
    {id:"API-002",nm:"Claude (firma)",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"opus/sonnet/haiku|max3",pin:false,ann:[],docs:[]},
    {id:"API-003",nm:"Gemini",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"Fleet|flash/pro",pin:false,ann:[],docs:[]},
    ...["AI Fleet Mgr:9800","Family Orch:9801","Evolved Swarm:9802","Cirkelline Ev:9803","CKC Evolved:9804","Kommandør Ev:9805","Cosmic Ev:9806","Unified Brain:9807","Admiral Hybrid:9808","Prod Dashboard:9809","Family MsgBus:9010"].map((s,i)=>{const[nm,pt]=s.split(":");return{id:`INT-${String(i+1).padStart(3,"0")}`,nm,tp:"INT",pt,st:"AFVENTER SCAN",ct:"INT",ph:i===8?5:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]}}),
    {id:"DB-001",nm:"PostgreSQL (Cirkelline)",tp:"DB",pt:"5533",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["A5","C8"],dp:[],db:["PLT-001"],hc:"",nt:"",pin:false,ann:[],docs:[]},
    {id:"DB-002",nm:"PostgreSQL (Cosmic)",tp:"DB",pt:"5534",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["A5","C8"],dp:[],db:["PLT-002"],hc:"",nt:"",pin:false,ann:[],docs:[]},
    {id:"DB-003",nm:"Redis",tp:"DB",pt:"",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["C5"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]},
    ...["prometheus:9090:prom/prometheus","loki:3100:grafana/loki","tempo:3200:grafana/tempo","grafana:3000:grafana/grafana","alertmanager:9093:prom/alertmanager","n8n:5678:n8nio/n8n"].map((s,i)=>{const[n,p,img]=s.split(":");return{id:`CTR-${String(i+1).padStart(3,"0")}`,nm:`kv1ntos-${n}`,tp:"CTR",pt:p,st:"AFVENTER SCAN",ct:"DOCK",ph:n==="n8n"?6:3,bg:["A4"],dp:[],db:[],hc:"",nt:img,pin:false,ann:[],docs:[]}}),
    {id:"AGT-001",nm:"Kommandør (21)",tp:"AGT",pt:"",st:"REGISTRERET",ct:"AGT",ph:5,bg:["E3"],dp:[],db:[],hc:"",nt:"M5+S5+R3+A4+G4",pin:false,ann:[],docs:[]},
    {id:"AGT-002",nm:"ELLE (122)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E1"],dp:[],db:[],hc:"",nt:"H30+T25+M20+O47",pin:false,ann:[],docs:[]},
    {id:"AGT-003",nm:"CKC (5)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E3"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]},
    {id:"AGT-004",nm:"Cosmic (9)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E4"],dp:[],db:[],hc:"",nt:"Research",pin:false,ann:[],docs:[]},
  ],
  errors:[{id:"E-001",sr:"Grafana",ds:"Dashboard fejl",sv:"HØJ",st:"ÅBEN",fx:"Scan"},{id:"E-002",sr:"API",ds:"Kvote-udtømning",sv:"KRITISK",st:"ÅBEN",fx:"Rate-limiter"},{id:"E-003",sr:"Plugins",ds:"28 plugins/16 aktive",sv:"MIDDEL",st:"ÅBEN",fx:"Scan"}],
  learnings:[{id:"L-001",a:"INFRA",t:"API simultant→quota",o:"rules/api-limits.md"},{id:"L-002",a:"INFRA",t:"Restart-policy nødvendig",o:"rules/docker.md"},{id:"L-003",a:"INFRA",t:"Grafana URL match",o:"knowledge/grafana.md"},{id:"L-004",a:"INFRA",t:"VRAM frigives ikke auto",o:"rules/ollama.md"},{id:"L-005",a:"INFRA",t:"nvidia-smi FØR load",o:"rules/ollama.md"},{id:"L-010",a:"PROMPT",t:"'ud over basale' nødvendigt",o:"knowledge/prompting.md"},{id:"L-011",a:"PROMPT",t:"XML-tags→bedre",o:"knowledge/prompting.md"},{id:"L-020",a:"PROCES",t:"Scan er BLOCKER",o:"rules/discovery.md"},{id:"L-021",a:"PROCES",t:"Alt i filer",o:"rules/dok.md"}],
  rules:[{id:"R-01",r:"API-nøgler ALDRIG i Git",c:"SIK"},{id:"R-02",r:"Restart+healthcheck+Loki",c:"DOC"},{id:"R-03",r:"UFW firewall",c:"SIK"},{id:"R-04",r:"Ugentlig ClamAV",c:"SIK"},{id:"R-05",r:"Max 3 Claude-kald",c:"API"},{id:"R-06",r:"Max 50 API totalt",c:"API"},{id:"R-07",r:"Commits m/ besked",c:"GIT"},{id:"R-08",r:"Ugentlig backup",c:"BAK"},{id:"R-09",r:"Trivy images",c:"SIK"},{id:"R-10",r:"git-secrets",c:"SIK"},{id:"R-11",r:"127.0.0.1 only",c:"NET"},{id:"R-12",r:"0 TODO",c:"KVA"},{id:"R-13",r:"nvidia-smi FØR",c:"AI"}],
  bogforing:[{c:"A",n:"STATUS",f:10,l:8241,m:"01-discovery"},{c:"B",n:"COMMANDS",f:10,l:6671,m:"04-drift"},{c:"C",n:"CONFIG",f:10,l:9850,m:"05-kontrol"},{c:"D",n:"ARCH",f:10,l:16787,m:"03-genopbyg"},{c:"E",n:"AGENTS",f:4,l:5060,m:"02-reg"},{c:"F",n:"HISTORY",f:10,l:707,m:"07-log"},{c:"G",n:"LAPTOP",f:5,l:1751,m:"01-disc"},{c:"H",n:"FLEET",f:2,l:642,m:"05-kontrol"},{c:"I",n:"OPS",f:8,l:5320,m:"05+07"},{c:"J",n:"META",f:2,l:6300,m:"00-styring"}],
  cmds:[
    {id:"C01",n:"Dagligt tjek",cmd:"docker ps -a --format '{{.Names}}: {{.Status}}' && free -h && nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader",c:"DRIFT"},
    {id:"C02",n:"Healthcheck",cmd:"for p in 9090 3100 3200 3000 5678 11434 9093; do curl -s --max-time 2 http://localhost:$p >/dev/null && echo \"$p:OK\" || echo \"$p:NEDE\"; done",c:"DRIFT"},
    {id:"C03",n:"Docker prune",cmd:"docker system prune -f && docker image prune -f",c:"VEDL"},
    {id:"C04",n:"Fejl 24h",cmd:"docker ps --format '{{.Names}}' | while read n; do e=$(docker logs $n --since 24h 2>&1|grep -ci 'error\\|fatal'); [ $e -gt 0 ] && echo \"$n: $e\"; done",c:"DIAG"},
    {id:"C05",n:"Ollama",cmd:"ollama ps && nvidia-smi",c:"AI"},
    {id:"C06",n:"Komplet scan",cmd:"echo '=SCAN=' && docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' && free -h && df -h / && nvidia-smi 2>/dev/null && ollama ps 2>/dev/null",c:"DISC"},
    {id:"C07",n:"Porte",cmd:"ss -tlnp | grep -E ':(3000|3100|3200|5678|9090|9093|11434|7777|7778|9800)' | sort",c:"NET"},
  ],
  tasks:[],captures:[],files:[],chatPastes:[],
  log:[{ts:new Date().toISOString().slice(0,16),w:"SYS",m:"v5.0 init"}],
};

const STS=["AFVENTER SCAN","I GANG","VENTER","KOMPLET","ÅBEN","AFVENTER TEST","IKKE STARTET","REGISTRERET","AFVENTER REG.","LUKKET"];
const TPS=["SVC","PLT","API","INT","DB","CTR","AGT","CUSTOM"];

function useS(k,i){const[d,sD]=useState(()=>{try{return window._kv?.[k]||JSON.parse(JSON.stringify(i))}catch{return JSON.parse(JSON.stringify(i))}});const s=useCallback(fn=>{sD(p=>{const n=typeof fn==="function"?fn(p):fn;if(!window._kv)window._kv={};window._kv[k]=n;return n})},[k]);return[d,s]}

const CSS=`@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Serif&family=Outfit:wght@300;400;500;600;700;800&display=swap');
:root{--bg:#050507;--b2:#0a0a0f;--b3:#111118;--bd:#1c1c28;--g:#d4a054;--gd:#6b5a3a;--gn:#4ade80;--rd:#f87171;--bl:#60a5fa;--pr:#c084fc;--cy:#22d3ee;--tx:#e8e4dc;--t2:#999;--t3:#555;--f:'Outfit',sans-serif;--m:'DM Mono',monospace;--s:'Instrument Serif',serif}
*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--gd);border-radius:2px}
@keyframes fu{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes si{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:none}}
@keyframes glow{0%,100%{box-shadow:0 0 4px rgba(212,160,84,.08)}50%{box-shadow:0 0 14px rgba(212,160,84,.2)}}
@keyframes pl{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes scan{0%{transform:translateY(-100%)}100%{transform:translateY(100vh)}}
.e{background:0;border:1px solid transparent;color:inherit;font:inherit;padding:1px 3px;width:100%;outline:0;border-radius:1px;transition:border .1s}.e:hover{border-color:var(--bd)}.e:focus{border-color:var(--g);background:var(--b3)}
.b{background:var(--b3);border:1px solid var(--bd);color:var(--t2);padding:4px 9px;font:500 10px var(--m);cursor:pointer;border-radius:1px;transition:all .1s;letter-spacing:.3px}.b:hover{border-color:var(--g);color:var(--g)}.bp{background:rgba(212,160,84,.06);border-color:var(--gd);color:var(--g)}.bd{color:var(--rd)}.b:active{transform:scale(.97)}
.dz{border:2px dashed var(--gd);padding:20px;text-align:center;border-radius:2px;transition:all .12s;cursor:pointer}.dz:hover,.dz.ov{border-color:var(--g);background:rgba(212,160,84,.03)}
.trm{background:#07070b;border:1px solid var(--bd);border-radius:2px;font:11px/1.5 var(--m);color:var(--gn);padding:10px;white-space:pre-wrap;word-break:break-all;overflow:auto}
.tst{position:fixed;bottom:14px;left:50%;transform:translateX(-50%);background:var(--g);color:#050507;padding:6px 18px;font:600 11px var(--m);border-radius:2px;z-index:999;animation:fu .12s ease-out}
.grain{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.025;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.scanline{position:fixed;left:0;width:100%;height:1px;background:linear-gradient(90deg,transparent,rgba(212,160,84,.04),transparent);z-index:1;pointer-events:none;animation:scan 10s linear infinite}
.chat-block{background:var(--b2);border:1px solid var(--bd);border-left:3px solid var(--pr);padding:10px 12px;margin:4px 0;border-radius:0 2px 2px 0;font:11px/1.6 var(--m);color:var(--tx);white-space:pre-wrap;position:relative}
.chat-block:hover{border-left-color:var(--g)}
.chat-block .meta{font-size:9px;color:var(--t3);margin-bottom:4px}
.ref-link{color:var(--cy);cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px}.ref-link:hover{color:var(--g)}`;

const SB=({s,oc})=>{const c={"AFVENTER SCAN":"var(--g)","I GANG":"var(--gn)","VENTER":"var(--bl)","KOMPLET":"#4ade80","ÅBEN":"var(--rd)","AFVENTER TEST":"var(--g)","IKKE STARTET":"#444","KRITISK":"#ff4444","HØJ":"#f59e0b","MIDDEL":"#eab308","REGISTRERET":"#4ade80","AFVENTER REG.":"var(--g)","LUKKET":"#666"}[s]||"#666";
return<span onClick={oc} style={{padding:"2px 6px",fontSize:9,fontFamily:"var(--m)",fontWeight:500,color:c,border:`1px solid ${c}33`,borderRadius:1,whiteSpace:"nowrap",cursor:oc?"pointer":"default"}}>{s}</span>};

const EF=({v,os,mn,ml})=>{const[ed,sE]=useState(false);const[val,sV]=useState(v);const r=useRef();useEffect(()=>{sV(v)},[v]);useEffect(()=>{if(ed&&r.current)r.current.focus()},[ed]);
if(!ed)return<span onClick={()=>sE(true)} style={{cursor:"pointer",fontFamily:mn?"var(--m)":"inherit",borderBottom:"1px dashed transparent",transition:"border .08s"}} onMouseEnter={e=>e.currentTarget.style.borderBottomColor="var(--gd)"} onMouseLeave={e=>e.currentTarget.style.borderBottomColor="transparent"}>{v||<i style={{color:"var(--t3)"}}>—</i>}</span>;
const sv=()=>{sE(false);if(val!==v)os(val)};
if(ml)return<textarea ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Escape"){sV(v);sE(false)}}} rows={3} style={{fontFamily:mn?"var(--m)":"var(--f)",fontSize:11,resize:"vertical"}}/>;
return<input ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Enter")sv();if(e.key==="Escape"){sV(v);sE(false)}}} style={{fontFamily:mn?"var(--m)":"var(--f)",fontSize:11}}/>};

const SF=({v,o,os})=><select value={v} onChange={e=>os(e.target.value)} style={{background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",padding:"2px 4px",fontSize:10,fontFamily:"var(--m)",borderRadius:1,cursor:"pointer"}}>{o.map(x=><option key={x}>{x}</option>)}</select>;

const SH=({id,t,cnt,act})=><div style={{marginTop:20,marginBottom:8,paddingBottom:5,borderBottom:"1px solid var(--bd)",display:"flex",justifyContent:"space-between",alignItems:"center"}}><div style={{display:"flex",alignItems:"baseline",gap:6}}><span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--g)",letterSpacing:2,fontWeight:500}}>{id}</span><h2 style={{fontFamily:"var(--s)",fontSize:18,fontWeight:400,color:"var(--tx)",fontStyle:"italic"}}>{t}</h2>{cnt!=null&&<span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--t3)"}}>({cnt})</span>}</div>{act}</div>;

// ═══ APP ═══
export default function App(){
  const[D,sD]=useS("kv5",INIT);
  const[sec,sSec]=useState("overview");const[q,sQ]=useState("");const[sel,sSel]=useState(null);const[mod,sMod]=useState(null);const[toast,sT]=useState("");const[cap,sCap]=useState(false);
  const sR=useRef();const cR=useRef();const fR=useRef();

  const ts=()=>new Date().toISOString().slice(0,16);
  const lg=m=>sD(d=>({...d,log:[{ts:ts(),w:"ADM",m},...(d.log||[]).slice(0,299)]}));
  const fl=m=>{sT(m);setTimeout(()=>sT(""),1600)};
  const cp=t=>{navigator.clipboard?.writeText(t);fl("Kopieret")};

  const uI=(id,f,v)=>{sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,[f]:v}:i)}));lg(`${id}.${f}`)};
  const dI=id=>{if(!confirm(`Slet ${id}?`))return;sD(d=>({...d,items:d.items.filter(i=>i.id!==id)}));lg(`DEL:${id}`);sSel(null)};
  const aI=it=>{sD(d=>({...d,items:[...d.items,it]}));lg(`NY:${it.id}`);fl("Tilføjet")};
  const tP=id=>sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,pin:!i.pin}:i)}));
  const aAnn=(id,t)=>sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,ann:[{ts:ts(),t},...(i.ann||[])]}:i)}));
  // Chat paste → attach to element
  const aDoc=(id,doc)=>{sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,docs:[{ts:ts(),...doc},...(i.docs||[])]}:i)}));lg(`DOC→${id}:${doc.title}`)};
  const aCap=c=>{sD(d=>({...d,captures:[{ts:ts(),text:c},...(d.captures||[])]}));lg("CAPTURE");fl("Gemt")};
  // Chat paste system
  const aPaste=(p)=>{sD(d=>({...d,chatPastes:[{ts:ts(),...p},...(d.chatPastes||[])]}));lg(`CHAT:${p.source}→${p.target||"uplaceret"}`)};
  const hFiles=fs=>Array.from(fs).forEach(f=>{const r=new FileReader();r.onload=e=>{sD(d=>({...d,files:[...(d.files||[]),{name:f.name,size:f.size,type:f.type,dt:ts(),content:e.target.result}]}));lg(`FIL:${f.name}`)};r.readAsText(f)});
  const exportJ=()=>{const b=new Blob([JSON.stringify(D,null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=`kv1ntos-${ts().replace(/:/g,"")}.json`;a.click();fl("Export OK")};

  useEffect(()=>{const h=e=>{const m=e.metaKey||e.ctrlKey;if(m&&e.key==="k"){e.preventDefault();sCap(p=>!p);setTimeout(()=>cR.current?.focus(),60)}if(m&&e.key==="n"){e.preventDefault();sMod("item")}if(m&&e.key==="f"){e.preventDefault();sR.current?.focus()}if(m&&e.key==="e"){e.preventDefault();exportJ()}if(m&&e.key==="p"){e.preventDefault();sMod("paste")}if(e.key==="Escape"){sSel(null);sMod(null);sCap(false)}};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[]);

  const items=D.items||[];const byTp=t=>items.filter(i=>i.tp===t);
  // INTELLIGENT SEARCH — fuzzy, numbers, bog refs, cross-ref
  const filtered=useMemo(()=>{if(!q.trim())return[];const ql=q.toLowerCase().trim();
    return items.filter(i=>{const hay=[i.id,i.nm,i.tp,i.ct,i.pt,i.nt,...(i.bg||[]),...(i.dp||[]),...(i.db||[]),...(i.ann||[]).map(a=>a.t),...(i.docs||[]).map(d=>d.title||d.text||"")].join(" ").toLowerCase();
      if(hay.includes(ql))return true;
      // number search: "9090" finds port 9090
      if(/^\d+$/.test(ql)&&(i.pt===ql||i.id.includes(ql)))return true;
      // bog ref: "A7" finds items with A7
      if(/^[A-J]\d*$/i.test(ql)&&(i.bg||[]).some(b=>b.toLowerCase().startsWith(ql)))return true;
      // fuzzy: 3+ chars, check if all chars appear in order
      if(ql.length>=3){const nm=i.nm.toLowerCase();let qi=0;for(let ci=0;ci<nm.length&&qi<ql.length;ci++)if(nm[ci]===ql[qi])qi++;return qi===ql.length}
      return false})},[items,q]);
  const st={tot:items.length,ver:items.filter(i=>i.st==="KOMPLET"||i.st==="REGISTRERET").length,err:(D.errors||[]).filter(e=>e.st==="ÅBEN").length};
  const td={padding:"5px 6px",fontSize:10,borderBottom:"1px solid rgba(28,28,40,.2)"};

  // Resolve cross-references
  const goRef=(ref)=>{const it=items.find(i=>i.id===ref);if(it){sSel(ref);fl(`→ ${ref}`)}};

  const IT=({rows,showTp})=><div style={{overflowX:"auto",marginBottom:8}}><table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}>
    <thead><tr>{["★","ID","NAVN",showTp&&"TP","PORT","STATUS","F","REF"].filter(Boolean).map((h,i)=><th key={i} style={{textAlign:"left",padding:"4px 6px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,fontWeight:600,letterSpacing:1,background:"var(--b2)",position:"sticky",top:0,zIndex:2}}>{h}</th>)}</tr></thead>
    <tbody>{rows.map((r,i)=><tr key={r.id} onClick={()=>sSel(r.id)} style={{cursor:"pointer",borderBottom:"1px solid rgba(28,28,40,.15)",animation:`fu .18s ease-out ${i*12}ms both`}}
      onMouseEnter={e=>e.currentTarget.style.background="rgba(212,160,84,.018)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
      <td style={td}><span onClick={e=>{e.stopPropagation();tP(r.id)}} style={{cursor:"pointer",fontSize:10}}>{r.pin?"⭐":"·"}</span></td>
      <td style={{...td,color:"var(--g)",fontWeight:500,fontSize:9}}>{r.id}</td>
      <td style={{...td,color:"var(--tx)"}}>{r.nm}{(r.docs||[]).length>0&&<span style={{color:"var(--pr)",fontSize:8,marginLeft:3}}>📎{r.docs.length}</span>}{(r.ann||[]).length>0&&<span style={{color:"var(--cy)",fontSize:8,marginLeft:3}}>✎{r.ann.length}</span>}</td>
      {showTp&&<td style={{...td,color:"var(--t2)",fontSize:9}}>{r.tp}</td>}
      <td style={{...td,color:"var(--cy)"}}>{r.pt||"—"}</td>
      <td style={td}><SB s={r.st} oc={e=>{e.stopPropagation();const ci=STS.indexOf(r.st);uI(r.id,"st",STS[(ci+1)%STS.length])}}/></td>
      <td style={{...td,color:"var(--t3)",fontSize:9}}>F{r.ph}</td>
      <td style={{...td,fontSize:8}}>{(r.bg||[]).map((b,j)=><span key={j} className="ref-link" onClick={e=>{e.stopPropagation();sQ(b)}} style={{marginRight:3}}>{b}</span>)}</td>
    </tr>)}</tbody></table></div>;

  const NAV=[{id:"overview",l:"◈ OVERBLIK"},{id:"all",l:"▤ ALLE"},{id:"paste",l:"💬 CHAT PASTE"},{id:"capture",l:"⌨ TERMINAL"},{id:"tasks",l:"☐ OPGAVER"},
    {id:"services",l:"● SERVICES"},{id:"platforms",l:"◻ PLATFORME"},{id:"apis",l:"⟡ API'ER"},{id:"integrations",l:"⊞ INT."},{id:"containers",l:"▣ CTR"},{id:"agents",l:"◎ AGT"},{id:"databases",l:"▥ DB"},
    {id:"commands",l:"$ CMDS"},{id:"files",l:"📁 FILER"},{id:"bogforing",l:"📋 A-J"},
    {id:"errors",l:"⚠ FEJL"},{id:"learnings",l:"◆ LEARN"},{id:"rules",l:"⛨ ODIN"},{id:"log",l:"✎ LOG"}];

  return<>
    <style>{CSS}</style>
    <div className="grain"/><div className="scanline"/>
    <div style={{display:"flex",minHeight:"100vh",background:"var(--bg)",color:"var(--tx)",fontFamily:"var(--f)",position:"relative",zIndex:2}}>
      {/* SIDEBAR */}
      <nav style={{width:150,borderRight:"1px solid var(--bd)",position:"fixed",top:0,left:0,height:"100vh",overflowY:"auto",background:"rgba(5,5,7,.96)",backdropFilter:"blur(8px)",zIndex:50,display:"flex",flexDirection:"column"}}>
        <div style={{padding:"10px 11px 8px",borderBottom:"1px solid var(--bd)"}}>
          <div style={{fontFamily:"var(--s)",fontSize:18,color:"var(--g)",fontStyle:"italic"}}>KV1NTOS</div>
          <div style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)"}}>OPS CENTER v5</div>
          <div style={{marginTop:3,display:"flex",gap:3,alignItems:"center"}}><span style={{width:4,height:4,borderRadius:"50%",background:"var(--gn)",animation:"pl 2s infinite"}}/><span style={{fontSize:8,color:"var(--t2)",fontFamily:"var(--m)"}}>F0</span></div>
        </div>
        <div style={{flex:1,padding:"2px 0",overflowY:"auto"}}>
          {NAV.map(n=><button key={n.id} onClick={()=>{sSec(n.id);sSel(null);sQ("")}} style={{display:"block",width:"100%",padding:"4px 11px",background:sec===n.id?"rgba(212,160,84,.04)":"transparent",border:"none",borderLeft:sec===n.id?"2px solid var(--g)":"2px solid transparent",color:sec===n.id?"var(--tx)":"var(--t3)",cursor:"pointer",fontSize:9,fontFamily:"var(--m)",textAlign:"left",transition:"all .08s"}}
            onMouseEnter={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t2)"}} onMouseLeave={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t3)"}}>{n.l}</button>)}
        </div>
        <div style={{padding:"5px 11px",borderTop:"1px solid var(--bd)",fontSize:8,fontFamily:"var(--m)"}}>
          <div style={{display:"flex",justifyContent:"space-between"}}><span style={{color:"var(--t3)"}}>Elem</span><span style={{color:"var(--g)"}}>{st.tot}</span></div>
          <div style={{display:"flex",justifyContent:"space-between"}}><span style={{color:"var(--t3)"}}>Fejl</span><span style={{color:"var(--rd)"}}>{st.err}</span></div>
          <div style={{display:"flex",gap:2,marginTop:3}}><button className="b" style={{flex:1,fontSize:7,padding:"2px"}} onClick={exportJ}>EXP</button><button className="b" style={{flex:1,fontSize:7,padding:"2px"}} onClick={()=>{if(confirm("Reset?"))sD(JSON.parse(JSON.stringify(INIT)))}}>RST</button></div>
          <div style={{marginTop:3,textAlign:"center",color:"var(--t3)",fontSize:7}}><span className="b" style={{border:0,padding:0,background:0,fontSize:7}}>⌘K</span>cap <span style={{fontSize:7}}>⌘P</span>paste <span style={{fontSize:7}}>⌘N</span>ny</div>
        </div>
      </nav>

      {/* MAIN */}
      <main style={{flex:1,marginLeft:150,padding:"10px 20px 40px",maxWidth:900}}>
        <div style={{display:"flex",gap:4,marginBottom:12}}>
          <input ref={sR} value={q} onChange={e=>sQ(e.target.value)} placeholder="Intelligent søgning: navn, ID, port, bog-ref (A7), fuzzy..." style={{flex:1,padding:"7px 10px",background:"var(--b2)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",outline:0,borderRadius:1}} onFocus={e=>e.target.style.borderColor="var(--gd)"} onBlur={e=>e.target.style.borderColor="var(--bd)"}/>
          <button className="b bp" onClick={()=>sMod("item")} title="⌘N">+</button>
          <button className="b" onClick={()=>sMod("paste")} title="⌘P">💬</button>
          <button className="b" onClick={()=>{sCap(p=>!p);setTimeout(()=>cR.current?.focus(),60)}} title="⌘K">⌨</button>
          <label className="b" style={{cursor:"pointer"}}>↑<input type="file" accept=".json" style={{display:"none"}} onChange={e=>{if(e.target.files[0]){const r=new FileReader();r.onload=ev=>{try{sD(JSON.parse(ev.target.result));fl("Import OK")}catch{alert("Ugyldig JSON")}};r.readAsText(e.target.files[0])}}}/></label>
        </div>

        {/* CAPTURE */}
        {cap&&<div style={{marginBottom:12,background:"var(--b2)",border:"1px solid var(--gd)",borderRadius:2,padding:10,animation:"fu .12s"}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--g)"}}>⌨ TERMINAL CAPTURE</span><button className="b" style={{fontSize:7,padding:"1px 5px"}} onClick={()=>sCap(false)}>✕</button></div>
          <textarea ref={cR} placeholder="Paste terminal output..." style={{width:"100%",minHeight:50,background:"#07070b",border:"1px solid var(--bd)",color:"var(--gn)",fontFamily:"var(--m)",fontSize:10,padding:7,borderRadius:1,resize:"vertical",outline:0}} onKeyDown={e=>{if((e.metaKey||e.ctrlKey)&&e.key==="Enter"&&cR.current.value.trim()){aCap(cR.current.value);cR.current.value=""}}}/>
          <div style={{display:"flex",justifyContent:"space-between",marginTop:3}}><span style={{fontSize:7,color:"var(--t3)"}}>⌘+Enter=gem</span><button className="b bp" style={{fontSize:8}} onClick={()=>{if(cR.current?.value.trim()){aCap(cR.current.value);cR.current.value=""}}}>GEM</button></div>
        </div>}

        {q.trim()&&<><SH id="SØG" t={`"${q}"`} cnt={filtered.length}/><IT rows={filtered} showTp/></>}

        {/* ═══ OVERVIEW ═══ */}
        {sec==="overview"&&!q.trim()&&<>
          <h1 style={{fontFamily:"var(--s)",fontSize:28,color:"var(--tx)",fontStyle:"italic",animation:"fu .2s",letterSpacing:-.3}}>KV1NTOS Operations</h1>
          <p style={{fontSize:10,color:"var(--t2)",marginBottom:14,fontFamily:"var(--m)"}}>{st.tot} elem · {st.err} fejl · {(D.chatPastes||[]).length} chat-pastes · {(D.captures||[]).length} captures · {(D.tasks||[]).length} tasks</p>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(95px,1fr))",gap:4,marginBottom:16}}>
            {[{l:"ELEMENTER",v:st.tot},{l:"VERIFICERET",v:st.ver,c:"var(--gn)"},{l:"SERVICES",v:byTp("SVC").length},{l:"PLATFORME",v:byTp("PLT").length},{l:"FEJL",v:st.err,c:"var(--rd)"},{l:"CHAT PASTES",v:(D.chatPastes||[]).length,c:"var(--pr)"},{l:"CAPTURES",v:(D.captures||[]).length,c:"var(--gn)"},{l:"FILER",v:(D.files||[]).length,c:"var(--bl)"}].map((s,i)=>
              <div key={i} style={{background:"var(--b2)",border:"1px solid var(--bd)",padding:"10px",borderRadius:1,animation:`fu .25s ease-out ${i*20}ms both`}}>
                <div style={{fontFamily:"var(--m)",fontSize:18,fontWeight:700,color:s.c||"var(--g)",lineHeight:1}}>{s.v}</div>
                <div style={{fontSize:8,color:"var(--t2)",marginTop:2}}>{s.l}</div></div>)}
          </div>
          {items.filter(i=>i.pin).length>0&&<><SH id="★" t="Pinned"/><IT rows={items.filter(i=>i.pin)} showTp/></>}
          <SH id="F" t="Faser"/>
          <div style={{display:"flex",gap:2,marginBottom:12}}>{D.phases.map(p=><div key={p.id} onClick={()=>{const nx=p.s==="VENTER"?"I GANG":p.s==="I GANG"?"KOMPLET":"VENTER";sD(d=>({...d,phases:d.phases.map(x=>x.id===p.id?{...x,s:nx}:x)}))}} style={{flex:1,padding:"6px 2px",background:p.s==="I GANG"?"rgba(212,160,84,.03)":"var(--b2)",border:`1px solid ${p.s==="I GANG"?"var(--gd)":p.s==="KOMPLET"?"#1a4a2a":"var(--bd)"}`,textAlign:"center",cursor:"pointer",borderRadius:1,position:"relative"}}>
            {p.s==="I GANG"&&<div style={{position:"absolute",top:0,left:0,right:0,height:2,background:"var(--g)",animation:"glow 2s infinite"}}/>}
            <div style={{fontFamily:"var(--m)",fontSize:12,fontWeight:700,color:p.s==="I GANG"?"var(--g)":p.s==="KOMPLET"?"var(--gn)":"var(--t3)"}}>{p.id}</div>
            <div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)"}}>{p.n}</div></div>)}</div>
        </>}

        {/* ═══ CHAT PASTE ═══ */}
        {sec==="paste"&&!q.trim()&&<><SH id="💬" t="Chat Paste" cnt={(D.chatPastes||[]).length} act={<button className="b bp" onClick={()=>sMod("paste")}>+ PASTE (⌘P)</button>}/>
          <p style={{fontSize:10,color:"var(--t2)",marginBottom:10}}>Kopiér fra Claude/Gemini/ChatGPT → paste her → vælg sektion/element → GEM. Auto-bogføres med kilde, tidsstempel, og reference.</p>
          {(D.chatPastes||[]).map((p,i)=><div key={i} className="chat-block" style={{animation:`fu .2s ease-out ${i*15}ms both`}}>
            <div className="meta">{p.ts} · <span style={{color:"var(--pr)"}}>{p.source}</span>{p.target&&<> · →<span className="ref-link" onClick={()=>sSel(p.target)}>{p.target}</span></>}{p.section&&<> · 📋{p.section}</>}</div>
            <div>{p.text.length>300?p.text.slice(0,300)+"...":p.text}</div>
            <div style={{marginTop:4,display:"flex",gap:3}}><button className="b" style={{fontSize:7,padding:"1px 5px"}} onClick={()=>cp(p.text)}>CP</button>{!p.target&&<button className="b bp" style={{fontSize:7,padding:"1px 5px"}} onClick={()=>{const id=prompt("Tilknyt til element-ID:");if(id){const it=items.find(x=>x.id===id.toUpperCase());if(it){aDoc(it.id,{title:`Chat: ${p.source}`,text:p.text});sD(d=>({...d,chatPastes:d.chatPastes.map((x,j)=>j===i?{...x,target:it.id}:x)}));fl(`→ ${it.id}`)}else fl("ID ikke fundet")}}}>TILKNYT</button>}<button className="b bd" style={{fontSize:7,padding:"1px 5px"}} onClick={()=>sD(d=>({...d,chatPastes:d.chatPastes.filter((_,j)=>j!==i)}))}>✕</button></div>
          </div>)}
        </>}

        {sec==="all"&&!q.trim()&&<><SH id="ALL" t="Alle elementer" cnt={items.length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={items} showTp/></>}

        {/* TYPE SECTIONS */}
        {["services","platforms","apis","integrations","containers","agents","databases"].map(s=>{const tp={services:"SVC",platforms:"PLT",apis:"API",integrations:"INT",containers:"CTR",agents:"AGT",databases:"DB"}[s];const nm={services:"Services",platforms:"Platforme",apis:"API'er",integrations:"Integrationer",containers:"Containere",agents:"Agenter",databases:"Databaser"}[s];
          return sec===s&&!q.trim()?<div key={s}><SH id={tp} t={nm} cnt={byTp(tp).length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp(tp)}/></div>:null})}

        {/* TERMINAL */}
        {sec==="capture"&&!q.trim()&&<><SH id="⌨" t="Terminal Captures" cnt={(D.captures||[]).length} act={<button className="b bp" onClick={()=>{sCap(true);setTimeout(()=>cR.current?.focus(),60)}}>+</button>}/>
          {!cap&&<button className="b bp" onClick={()=>{sCap(true);setTimeout(()=>cR.current?.focus(),60)}} style={{width:"100%",padding:10,marginBottom:10}}>⌨ Capture (⌘K)</button>}
          {(D.captures||[]).map((c,i)=><div key={i} style={{marginBottom:8,animation:`fu .15s ease-out ${i*15}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}><span style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)"}}>{c.ts}</span><div style={{display:"flex",gap:2}}><button className="b" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>cp(c.text)}>CP</button><button className="b bd" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>sD(d=>({...d,captures:d.captures.filter((_,j)=>j!==i)}))}>✕</button></div></div>
            <div className="trm" style={{maxHeight:120}}>{c.text}</div></div>)}
        </>}

        {/* TASKS */}
        {sec==="tasks"&&!q.trim()&&<><SH id="☐" t="Opgaver" cnt={(D.tasks||[]).length} act={<button className="b bp" onClick={()=>sMod("task")}>+</button>}/>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:6}}>
            {["TODO","I GANG","KOMPLET"].map(col=><div key={col}>
              <div style={{fontSize:8,fontFamily:"var(--m)",color:col==="TODO"?"var(--rd)":col==="I GANG"?"var(--g)":"var(--gn)",letterSpacing:1,marginBottom:4,paddingBottom:2,borderBottom:`1px solid currentColor`}}>{col} ({(D.tasks||[]).filter(t=>t.s===col).length})</div>
              {(D.tasks||[]).filter(t=>t.s===col).map((t,i)=>{const idx=(D.tasks||[]).indexOf(t);return<div key={i} style={{background:"var(--b2)",border:"1px solid var(--bd)",padding:"7px 8px",marginBottom:3,borderRadius:1,fontSize:10}}>
                <div style={{fontWeight:600,marginBottom:2}}>{t.title}</div>
                {t.desc&&<div style={{fontSize:9,color:"var(--t2)",marginBottom:3}}>{t.desc}</div>}
                <div style={{display:"flex",gap:2}}>{col!=="TODO"&&<button className="b" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>sD(d=>({...d,tasks:d.tasks.map((x,j)=>j===idx?{...x,s:col==="I GANG"?"TODO":"I GANG"}:x)}))}>←</button>}{col!=="KOMPLET"&&<button className="b" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>sD(d=>({...d,tasks:d.tasks.map((x,j)=>j===idx?{...x,s:col==="TODO"?"I GANG":"KOMPLET"}:x)}))}>→</button>}</div></div>})}</div>)}
          </div>
        </>}

        {/* COMMANDS */}
        {sec==="commands"&&!q.trim()&&<><SH id="$" t="Kommandoer" cnt={(D.cmds||[]).length}/>
          <p style={{fontSize:9,color:"var(--t2)",marginBottom:8}}>KOPIÉR → terminal → kør → kopiér output → <span style={{color:"var(--g)"}}>⌘K</span> capture</p>
          {(D.cmds||[]).map((c,i)=><div key={c.id} style={{marginBottom:5,animation:`fu .15s ease-out ${i*15}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:1}}><span style={{fontSize:10}}><span style={{color:"var(--g)",fontFamily:"var(--m)",fontSize:8}}>{c.id}</span> {c.n} <span style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)"}}>{c.c}</span></span><button className="b" style={{fontSize:7,padding:"1px 5px"}} onClick={()=>cp(c.cmd)}>KOPIÉR</button></div>
            <div className="trm" style={{maxHeight:40,fontSize:10,cursor:"pointer"}} onClick={()=>cp(c.cmd)}>{c.cmd}</div></div>)}
        </>}

        {/* FILES */}
        {sec==="files"&&!q.trim()&&<><SH id="📁" t="Filer & Desktop" cnt={(D.files||[]).length}/>
          <div className="dz" onDrop={e=>{e.preventDefault();e.currentTarget.classList.remove("ov");hFiles(e.dataTransfer.files)}} onDragOver={e=>{e.preventDefault();e.currentTarget.classList.add("ov")}} onDragLeave={e=>e.currentTarget.classList.remove("ov")} onClick={()=>fR.current?.click()}>
            <input ref={fR} type="file" multiple style={{display:"none"}} onChange={e=>hFiles(e.target.files)}/><div style={{fontSize:10,color:"var(--t2)",fontFamily:"var(--m)"}}>Drop filer fra desktop — .md .json .yml .sh .conf .env billeder</div></div>
          {(D.files||[]).map((f,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"5px 6px",borderBottom:"1px solid var(--bd)",fontSize:10,animation:`fu .15s ${i*10}ms both`}}>
            <span>{f.name} <span style={{color:"var(--t3)",fontSize:8}}>{(f.size/1024).toFixed(1)}K</span></span>
            <div style={{display:"flex",gap:2}}>{f.content&&<button className="b" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>sMod({tp:"file",f})}>VIS</button>}<button className="b" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>{const id=prompt("Tilknyt til element:");if(id){const it=items.find(x=>x.id===id.toUpperCase());if(it){aDoc(it.id,{title:f.name,text:f.content||"(binær)"});fl(`→${it.id}`)}}}}>→ELEM</button><button className="b bd" style={{fontSize:7,padding:"1px 4px"}} onClick={()=>sD(d=>({...d,files:d.files.filter(x=>x.name!==f.name)}))}>✕</button></div></div>)}
        </>}

        {/* BOGFORING */}
        {sec==="bogforing"&&!q.trim()&&<><SH id="A-J" t="Bogføringsmappe" cnt={`${(D.bogforing||[]).reduce((s,b)=>s+b.f,0)} filer`}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["KAT","NAVN","FIL","LINJER","→MANUAL"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"4px 6px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.bogforing||[]).map((b,i)=><tr key={i}><td style={{...td,color:"var(--g)",fontWeight:800,fontSize:14}}>{b.c}</td><td style={td}>{b.n}</td><td style={{...td,textAlign:"center"}}>{b.f}</td><td style={{...td,textAlign:"right"}}>{b.l.toLocaleString()}</td><td style={{...td,color:"var(--cy)"}}>{b.m}</td></tr>)}</tbody></table>
        </>}

        {sec==="errors"&&!q.trim()&&<><SH id="⚠" t="Fejl" cnt={(D.errors||[]).length} act={<button className="b bp" onClick={()=>sMod("error")}>+</button>}/>
          {(D.errors||[]).map((e,i)=><div key={e.id} style={{display:"grid",gridTemplateColumns:"50px 55px 1fr 65px 55px 20px",gap:3,padding:"5px 6px",borderBottom:"1px solid var(--bd)",fontSize:10,alignItems:"center"}}>
            <span style={{color:"var(--g)",fontSize:9}}>{e.id}</span><EF v={e.sr} os={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,sr:v}:x)}))}/><EF v={e.ds} os={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,ds:v}:x)}))}/><SB s={e.sv}/><SF v={e.st} o={["ÅBEN","I GANG","LUKKET"]} os={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,st:v}:x)}))}/><button className="b bd" style={{padding:0,fontSize:8}} onClick={()=>sD(d=>({...d,errors:d.errors.filter(x=>x.id!==e.id)}))}>✕</button></div>)}</>}

        {sec==="learnings"&&!q.trim()&&<><SH id="◆" t="Learnings" cnt={(D.learnings||[]).length}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["ID","OMR","LEARNING","→ODIN"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"4px 6px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.learnings||[]).map((l,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{l.id}</td><td style={{...td,color:"var(--t2)"}}>{l.a}</td><td style={td}>{l.t}</td><td style={{...td,color:"var(--pr)",fontSize:8}}>{l.o}</td></tr>)}</tbody></table></>}

        {sec==="rules"&&!q.trim()&&<><SH id="⛨" t="ODIN Regler" cnt={(D.rules||[]).length}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["ID","REGEL","KAT"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"4px 6px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.rules||[]).map((r,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{r.id}</td><td style={td}>{r.r}</td><td style={{...td,color:"var(--t2)"}}>{r.c}</td></tr>)}</tbody></table>
          <div style={{marginTop:6,padding:6,border:"1px solid rgba(248,113,113,.1)",borderRadius:1,fontSize:9,color:"var(--rd)"}}>UFRAVIGELIGE</div></>}

        {sec==="log"&&!q.trim()&&<><SH id="✎" t="Log" cnt={(D.log||[]).length} act={<button className="b" onClick={exportJ}>EXP</button>}/>
          {(D.log||[]).map((l,i)=><div key={i} style={{padding:"2px 0",borderBottom:"1px solid rgba(28,28,40,.12)",display:"grid",gridTemplateColumns:"100px 35px 1fr",gap:4,fontSize:9,fontFamily:"var(--m)",color:"var(--t2)"}}><span style={{color:"var(--t3)"}}>{l.ts}</span><span style={{color:"var(--g)"}}>{l.w}</span><span>{l.m}</span></div>)}</>}
      </main>
    </div>

    {/* DETAIL PANEL */}
    {sel&&(()=>{const it=items.find(i=>i.id===sel);if(!it)return null;return<div style={{position:"fixed",inset:0,zIndex:200}} onClick={()=>sSel(null)}>
      <div style={{position:"absolute",inset:0,background:"rgba(0,0,0,.4)",backdropFilter:"blur(3px)"}}/>
      <div onClick={e=>e.stopPropagation()} style={{position:"absolute",right:0,top:0,width:420,height:"100vh",background:"var(--bg)",borderLeft:"1px solid var(--gd)",overflowY:"auto",padding:"14px 18px",animation:"si .15s ease-out"}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:12}}><div style={{display:"flex",gap:5,alignItems:"center"}}><span style={{fontFamily:"var(--m)",fontSize:11,color:"var(--g)"}}>{it.id}</span><span onClick={()=>tP(it.id)} style={{cursor:"pointer"}}>{it.pin?"⭐":"☆"}</span></div><div style={{display:"flex",gap:2}}><button className="b bd" onClick={()=>dI(it.id)}>SLET</button><button className="b" onClick={()=>sSel(null)}>ESC</button></div></div>
        <div style={{fontFamily:"var(--s)",fontSize:20,fontStyle:"italic",marginBottom:10}}><EF v={it.nm} os={v=>uI(it.id,"nm",v)}/></div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6,marginBottom:10}}>
          {[["TYPE",<SF v={it.tp} o={TPS} os={v=>uI(it.id,"tp",v)}/>],["STATUS",<SF v={it.st} o={STS} os={v=>uI(it.id,"st",v)}/>],["PORT",<EF v={it.pt} mn os={v=>uI(it.id,"pt",v)}/>],["FASE",<SF v={String(it.ph)} o={["0","1","2","3","4","5","6","7"]} os={v=>uI(it.id,"ph",+v)}/>],["HEALTH",<EF v={it.hc} mn os={v=>uI(it.id,"hc",v)}/>],["KAT",<EF v={it.ct} os={v=>uI(it.id,"ct",v)}/>]].map(([l,c],i)=><div key={i}><div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.6,marginBottom:1}}>{l}</div>{c}</div>)}
        </div>
        {[["BOG.REF","bg"],["AFHÆNGER","dp"],["BRUGES AF","db"]].map(([l,k])=><div key={k} style={{marginBottom:6}}><div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.6,marginBottom:1}}>{l}</div><div style={{display:"flex",gap:2,flexWrap:"wrap"}}>{(it[k]||[]).map((r,j)=><span key={j} className="ref-link" onClick={()=>goRef(r)} style={{fontSize:10,fontFamily:"var(--m)"}}>{r}</span>)}<EF v={(it[k]||[]).join(",")} mn os={v=>uI(it.id,k,v.split(",").map(x=>x.trim()).filter(Boolean))}/></div></div>)}
        <div style={{marginBottom:10}}><div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",marginBottom:1}}>NOTER</div><EF v={it.nt} ml os={v=>uI(it.id,"nt",v)}/></div>

        {/* DOCS ATTACHED */}
        {(it.docs||[]).length>0&&<div style={{borderTop:"1px solid var(--bd)",paddingTop:8,marginBottom:8}}>
          <div style={{fontSize:8,color:"var(--pr)",fontFamily:"var(--m)",marginBottom:4}}>📎 TILKNYTTEDE DOKUMENTER ({it.docs.length})</div>
          {it.docs.map((d,i)=><div key={i} className="chat-block" style={{fontSize:10,maxHeight:100,overflow:"auto"}}><div className="meta">{d.ts} · {d.title}</div>{d.text?.slice(0,200)}{d.text?.length>200&&"..."}</div>)}
        </div>}

        {/* ANNOTATIONS */}
        <div style={{borderTop:"1px solid var(--bd)",paddingTop:8}}>
          <div style={{fontSize:8,color:"var(--g)",fontFamily:"var(--m)",marginBottom:3}}>ANNOTATIONER</div>
          <div style={{display:"flex",gap:2,marginBottom:4}}><input id="ann" placeholder="Tilføj..." style={{flex:1,padding:"4px 6px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",outline:0}} onKeyDown={e=>{if(e.key==="Enter"&&e.target.value.trim()){aAnn(it.id,e.target.value);e.target.value=""}}}/><button className="b" style={{fontSize:7}} onClick={()=>{const inp=document.getElementById("ann");if(inp?.value.trim()){aAnn(it.id,inp.value);inp.value=""}}}>+</button></div>
          {(it.ann||[]).map((a,i)=><div key={i} style={{fontSize:9,color:"var(--t2)",padding:"2px 0",borderBottom:"1px solid rgba(28,28,40,.12)"}}><span style={{color:"var(--t3)",fontFamily:"var(--m)",fontSize:7,marginRight:3}}>{a.ts}</span>{a.t}</div>)}
        </div>
      </div>
    </div>})()}

    {/* MODALS */}
    {mod==="item"&&<Md t="Nyt element" oc={()=>sMod(null)}><NI onAdd={it=>{aI(it);sMod(null)}} its={items}/></Md>}
    {mod==="error"&&<Md t="Ny fejl" oc={()=>sMod(null)}><NE onAdd={e=>{sD(d=>({...d,errors:[...d.errors,e]}));lg(`ERR:${e.ds}`);sMod(null)}} es={D.errors||[]}/></Md>}
    {mod==="task"&&<Md t="Ny opgave" oc={()=>sMod(null)}><NTk onAdd={t=>{sD(d=>({...d,tasks:[...(d.tasks||[]),t]}));lg(`TASK:${t.title}`);sMod(null)}}/></Md>}
    {mod==="paste"&&<Md t="💬 Chat Paste" oc={()=>sMod(null)}><NP onAdd={p=>{aPaste(p);sMod(null)}} its={items}/></Md>}
    {mod?.tp==="file"&&<Md t={mod.f.name} oc={()=>sMod(null)}><pre className="trm" style={{maxHeight:350}}>{mod.f.content}</pre></Md>}
    {toast&&<div className="tst">{toast}</div>}
  </>;
}

function Md({t,oc,children}){useEffect(()=>{const h=e=>{if(e.key==="Escape")oc()};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[oc]);
return<div style={{position:"fixed",inset:0,zIndex:300,display:"flex",alignItems:"center",justifyContent:"center"}} onClick={oc}><div style={{position:"absolute",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(3px)"}}/><div onClick={e=>e.stopPropagation()} style={{background:"var(--bg)",border:"1px solid var(--gd)",padding:"16px 20px",borderRadius:2,width:460,maxHeight:"78vh",overflowY:"auto",animation:"fu .12s"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:12}}><h3 style={{fontFamily:"var(--s)",fontSize:16,color:"var(--g)",fontStyle:"italic"}}>{t}</h3><button className="b" onClick={oc}>✕</button></div>{children}</div></div>}

const ip={width:"100%",padding:"5px 7px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",borderRadius:1,outline:0};
const fl2={display:"block",fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.5,marginBottom:1,marginTop:6};

function NI({onAdd,its}){const[f,s]=useState({id:"",nm:"",tp:"SVC",pt:"",st:"AFVENTER SCAN",ct:"CORE",ph:0,bg:[],dp:[],db:[],hc:"",nt:"",pin:false,ann:[],docs:[]});
return<><div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:5}}><label style={fl2}>ID *<input value={f.id} onChange={e=>s({...f,id:e.target.value.toUpperCase()})} style={ip}/></label><label style={fl2}>NAVN *<input value={f.nm} onChange={e=>s({...f,nm:e.target.value})} style={ip}/></label><label style={fl2}>TYPE<SF v={f.tp} o={TPS} os={v=>s({...f,tp:v})}/></label><label style={fl2}>PORT<input value={f.pt} onChange={e=>s({...f,pt:e.target.value})} style={ip}/></label></div>
<label style={fl2}>NOTER<textarea value={f.nt} onChange={e=>s({...f,nt:e.target.value})} rows={2} style={{...ip,resize:"vertical"}}/></label>
<label style={fl2}>BOG.REF<input value={f.bg.join(",")} onChange={e=>s({...f,bg:e.target.value.split(",").map(x=>x.trim()).filter(Boolean)})} style={ip}/></label>
<div style={{display:"flex",gap:3,marginTop:10,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.id||!f.nm)return alert("ID+Navn");if(its.find(i=>i.id===f.id))return alert("ID eksisterer");onAdd(f)}}>OPRET</button></div></>}

function NE({onAdd,es}){const[f,s]=useState({id:`E-${String(es.length+1).padStart(3,"0")}`,sr:"",ds:"",sv:"MIDDEL",st:"ÅBEN",fx:""});
return<><label style={fl2}>KILDE<input value={f.sr} onChange={e=>s({...f,sr:e.target.value})} style={ip}/></label><label style={fl2}>BESKRIVELSE *<input value={f.ds} onChange={e=>s({...f,ds:e.target.value})} style={ip}/></label><label style={fl2}>ALV<SF v={f.sv} o={["KRITISK","HØJ","MIDDEL","LAV"]} os={v=>s({...f,sv:v})}/></label>
<div style={{display:"flex",gap:3,marginTop:10,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.ds)return alert("Beskrivelse");onAdd(f)}}>OPRET</button></div></>}

function NTk({onAdd}){const[f,s]=useState({title:"",desc:"",s:"TODO"});
return<><label style={fl2}>TITEL *<input value={f.title} onChange={e=>s({...f,title:e.target.value})} style={ip}/></label><label style={fl2}>BESKRIVELSE<textarea value={f.desc} onChange={e=>s({...f,desc:e.target.value})} rows={2} style={{...ip,resize:"vertical"}}/></label>
<div style={{display:"flex",gap:3,marginTop:10,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.title)return alert("Titel");onAdd(f)}}>OPRET</button></div></>}

// CHAT PASTE MODAL — kopiér fra enhver AI, paste, vælg target
function NP({onAdd,its}){const[f,s]=useState({text:"",source:"Claude",target:"",section:""});
return<><label style={fl2}>KILDE<SF v={f.source} o={["Claude","Gemini","ChatGPT","Ollama","Andet"]} os={v=>s({...f,source:v})}/></label>
<label style={fl2}>TEKST * — paste chat-output her<textarea value={f.text} onChange={e=>s({...f,text:e.target.value})} rows={6} placeholder="Kopiér fra din chat med AI-modellen og paste her..." style={{...ip,resize:"vertical",minHeight:100}}/></label>
<label style={fl2}>TILKNYT TIL ELEMENT (valgfrit)<input value={f.target} onChange={e=>s({...f,target:e.target.value.toUpperCase()})} placeholder="f.eks. SVC-002" style={ip}/>{f.target&&its.find(i=>i.id===f.target)?<span style={{fontSize:8,color:"var(--gn)"}}>✓ {its.find(i=>i.id===f.target).nm}</span>:f.target?<span style={{fontSize:8,color:"var(--rd)"}}>Ikke fundet</span>:null}</label>
<label style={fl2}>SEKTION/KATEGORI<input value={f.section} onChange={e=>s({...f,section:e.target.value})} placeholder="f.eks. DISCOVERY, CONFIG, DRIFT..." style={ip}/></label>
<div style={{display:"flex",gap:3,marginTop:10,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.text.trim())return alert("Tekst");onAdd(f)}}>GEM & BOGFØR</button></div></>}
