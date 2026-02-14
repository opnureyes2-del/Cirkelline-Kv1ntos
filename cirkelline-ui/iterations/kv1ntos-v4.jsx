import { useState, useMemo, useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════
   KV1NTOS v4.0 — TERMINAL OPERATIONS CENTER
   Parallelt arbejde: terminal + app + Claude Opus
   ═══════════════════════════════════════════════════════════════ */

const INIT={
  phases:[
    {id:0,n:"DISCOVERY",s:"I GANG",d:"Find ALT. Antag INTET.",v:"Alle fund klassificeret"},
    {id:1,n:"OPRYDNING",s:"VENTER",d:"Fjern ødelagt. Bevar fungerende.",v:"docker ps = kun nødvendige"},
    {id:2,n:"FUNDAMENT",s:"VENTER",d:"Docker, netværk, Git, mapper.",v:"Docker+Compose+Git rent"},
    {id:3,n:"OBSERVABILITY",s:"VENTER",d:"Prometheus, Loki, Tempo, Grafana.",v:"Grafana UDEN fejl"},
    {id:4,n:"AI-MODELLER",s:"VENTER",d:"Ollama, Claude, Gemini.",v:"Model svarer + rate-limiter"},
    {id:5,n:"ODIN",s:"VENTER",d:"Videnbase, regler, agent-register.",v:"Admiral→ODIN→HQ→Agent"},
    {id:6,n:"INTEGRATION",s:"VENTER",d:"Forbind det der virker.",v:"Alt snakker, Grafana viser"},
    {id:7,n:"PROJEKTER",s:"VENTER",d:"BØRNESKABER, Three Realms, Gaming.",v:"Stabilt i produktion"},
  ],
  items:[
    {id:"SVC-001",nm:"Docker Engine",tp:"SVC",pt:"socket",st:"AFVENTER SCAN",ct:"CORE",ph:2,bg:["A4","B5","C7"],dp:[],db:["SVC-002","SVC-003","SVC-004","SVC-005","SVC-006","SVC-007","SVC-008"],hc:"systemctl status docker",nt:"",pin:false,ann:[]},
    {id:"SVC-002",nm:"Prometheus",tp:"SVC",pt:"9090",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:9090/-/healthy",nt:"",pin:false,ann:[]},
    {id:"SVC-003",nm:"Loki",tp:"SVC",pt:"3100",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:3100/ready",nt:"",pin:false,ann:[]},
    {id:"SVC-004",nm:"Grafana",tp:"SVC",pt:"3000",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7","B7","C10"],dp:["SVC-001","SVC-002","SVC-003"],db:[],hc:"curl localhost:3000/api/health",nt:"",pin:false,ann:[]},
    {id:"SVC-005",nm:"Tempo",tp:"SVC",pt:"3200",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7"],dp:["SVC-001"],db:["SVC-004"],hc:"curl localhost:3200/ready",nt:"",pin:false,ann:[]},
    {id:"SVC-006",nm:"Alertmanager",tp:"SVC",pt:"9093",st:"AFVENTER SCAN",ct:"OBS",ph:3,bg:["A7"],dp:["SVC-001","SVC-002"],db:[],hc:"curl localhost:9093/-/healthy",nt:"",pin:false,ann:[]},
    {id:"SVC-007",nm:"n8n",tp:"SVC",pt:"5678",st:"AFVENTER SCAN",ct:"AUTO",ph:6,bg:[],dp:["SVC-001"],db:[],hc:"curl localhost:5678/healthz",nt:"",pin:false,ann:[]},
    {id:"SVC-008",nm:"Ollama",tp:"SVC",pt:"11434",st:"AFVENTER SCAN",ct:"AI",ph:4,bg:[],dp:[],db:[],hc:"curl localhost:11434",nt:"",pin:false,ann:[]},
    {id:"PLT-001",nm:"Cirkelline System",tp:"PLT",pt:"7777",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B1","C1","D2"],dp:[],db:[],hc:"",nt:"db: PostgreSQL:5533",pin:false,ann:[]},
    {id:"PLT-002",nm:"Cosmic Library",tp:"PLT",pt:"7778",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B2","C2","D3"],dp:[],db:[],hc:"",nt:"db: PostgreSQL:5534",pin:false,ann:[]},
    {id:"PLT-003",nm:"CKC Gateway",tp:"PLT",pt:"7779",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B3","C3","D4"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"PLT-004",nm:"Kommandør Gateway",tp:"PLT",pt:"7800",st:"AFVENTER SCAN",ct:"PLT",ph:7,bg:["A2","B4","C4","D5"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"PLT-005",nm:"BØRNESKABER",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"Genesis-sekvens: farver, lyde, tegninger",pin:false,ann:[]},
    {id:"PLT-006",nm:"Three Realms",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"GPS+3 tidsperioder: 1825, nu, 2050",pin:false,ann:[]},
    {id:"PLT-007",nm:"Gaming Platform",tp:"PLT",pt:"",st:"IKKE STARTET",ct:"PROJ",ph:7,bg:[],dp:[],db:[],hc:"",nt:"Steam-kvalitet, invitation-only",pin:false,ann:[]},
    {id:"API-001",nm:"Claude (privat)",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"opus-4-6, sonnet-4-5, haiku-4-5 | max 3",pin:false,ann:[]},
    {id:"API-002",nm:"Claude (firma)",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"opus-4-6, sonnet-4-5, haiku-4-5 | max 3",pin:false,ann:[]},
    {id:"API-003",nm:"Gemini",tp:"API",pt:"",st:"AFVENTER TEST",ct:"AI",ph:4,bg:["C9"],dp:[],db:[],hc:"",nt:"Fleet Router | 2.0-flash, 2.0-pro",pin:false,ann:[]},
    {id:"INT-001",nm:"AI Fleet Manager",tp:"INT",pt:"9800",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-002",nm:"Family Orchestrator",tp:"INT",pt:"9801",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-003",nm:"Evolved Swarm",tp:"INT",pt:"9802",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-004",nm:"Cirkelline Evolved",tp:"INT",pt:"9803",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-005",nm:"CKC Evolved",tp:"INT",pt:"9804",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-006",nm:"Kommandør Evolved",tp:"INT",pt:"9805",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-007",nm:"Cosmic Evolved",tp:"INT",pt:"9806",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-008",nm:"Unified Brain",tp:"INT",pt:"9807",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-009",nm:"Admiral Hybrid",tp:"INT",pt:"9808",st:"AFVENTER SCAN",ct:"INT",ph:5,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-010",nm:"Prod Dashboard",tp:"INT",pt:"9809",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"INT-011",nm:"Family Msg Bus",tp:"INT",pt:"9010",st:"AFVENTER SCAN",ct:"INT",ph:6,bg:["J2","I4"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"DB-001",nm:"PostgreSQL (Cirkelline)",tp:"DB",pt:"5533",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["A5","C8"],dp:[],db:["PLT-001"],hc:"",nt:"",pin:false,ann:[]},
    {id:"DB-002",nm:"PostgreSQL (Cosmic)",tp:"DB",pt:"5534",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["A5","C8"],dp:[],db:["PLT-002"],hc:"",nt:"",pin:false,ann:[]},
    {id:"DB-003",nm:"Redis",tp:"DB",pt:"",st:"AFVENTER SCAN",ct:"DATA",ph:7,bg:["C5"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"CTR-001",nm:"kv1ntos-prometheus",tp:"CTR",pt:"9090",st:"AFVENTER SCAN",ct:"DOCK",ph:3,bg:["A4"],dp:[],db:[],hc:"",nt:"prom/prometheus",pin:false,ann:[]},
    {id:"CTR-002",nm:"kv1ntos-loki",tp:"CTR",pt:"3100",st:"AFVENTER SCAN",ct:"DOCK",ph:3,bg:["A4"],dp:[],db:[],hc:"",nt:"grafana/loki",pin:false,ann:[]},
    {id:"CTR-003",nm:"kv1ntos-tempo",tp:"CTR",pt:"3200",st:"AFVENTER SCAN",ct:"DOCK",ph:3,bg:["A4"],dp:[],db:[],hc:"",nt:"grafana/tempo",pin:false,ann:[]},
    {id:"CTR-004",nm:"kv1ntos-grafana",tp:"CTR",pt:"3000",st:"AFVENTER SCAN",ct:"DOCK",ph:3,bg:["A4"],dp:[],db:[],hc:"",nt:"grafana/grafana",pin:false,ann:[]},
    {id:"CTR-005",nm:"kv1ntos-alertmanager",tp:"CTR",pt:"9093",st:"AFVENTER SCAN",ct:"DOCK",ph:3,bg:["A4"],dp:[],db:[],hc:"",nt:"prom/alertmanager",pin:false,ann:[]},
    {id:"CTR-006",nm:"kv1ntos-n8n",tp:"CTR",pt:"5678",st:"AFVENTER SCAN",ct:"DOCK",ph:6,bg:["A4"],dp:[],db:[],hc:"",nt:"n8nio/n8n",pin:false,ann:[]},
    {id:"AGT-001",nm:"Kommandør (21)",tp:"AGT",pt:"",st:"REGISTRERET",ct:"AGT",ph:5,bg:["E3"],dp:[],db:[],hc:"",nt:"M(5)+S(5)+R(3)+A(4)+G(4)",pin:false,ann:[]},
    {id:"AGT-002",nm:"ELLE (122)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E1"],dp:[],db:[],hc:"",nt:"Health(30)+Train(25)+Mon(20)+Other(47)",pin:false,ann:[]},
    {id:"AGT-003",nm:"CKC (5)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E3"],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]},
    {id:"AGT-004",nm:"Cosmic (9)",tp:"AGT",pt:"",st:"AFVENTER REG.",ct:"AGT",ph:5,bg:["E4"],dp:[],db:[],hc:"",nt:"Research Team",pin:false,ann:[]},
  ],
  errors:[
    {id:"E-001",sr:"Grafana",ds:"Fejl synlige i dashboards",sv:"HØJ",st:"ÅBEN",fx:"Afventer scan"},
    {id:"E-002",sr:"API",ds:"Agenter udtømmer kvoter",sv:"KRITISK",st:"ÅBEN",fx:"Rate-limiter"},
    {id:"E-003",sr:"Plugins",ds:"28 plugins, 16 aktive",sv:"MIDDEL",st:"ÅBEN",fx:"Scan identificerer"},
  ],
  learnings:[
    {id:"L-001",a:"INFRA",t:"API simultant → quota udtømt",o:"rules/api-limits.md"},
    {id:"L-002",a:"INFRA",t:"Containere uden restart forsvinder",o:"rules/docker-regler.md"},
    {id:"L-003",a:"INFRA",t:"Grafana URL: container vs localhost",o:"knowledge/grafana.md"},
    {id:"L-004",a:"INFRA",t:"VRAM frigives IKKE automatisk",o:"rules/ollama-regler.md"},
    {id:"L-005",a:"INFRA",t:"nvidia-smi FØR model load",o:"rules/ollama-regler.md"},
    {id:"L-010",a:"PROMPT",t:"'gå ud over basale' er nødvendigt",o:"knowledge/prompting.md"},
    {id:"L-011",a:"PROMPT",t:"XML-tags → bedre output",o:"knowledge/prompting.md"},
    {id:"L-012",a:"PROMPT",t:"Ét eksempel > 100 ord",o:"knowledge/prompting.md"},
    {id:"L-020",a:"PROCES",t:"Konceptuelt ≠ brugbar vejledning",o:"rules/kvalitet.md"},
    {id:"L-021",a:"PROCES",t:"Scan er BLOCKER",o:"rules/discovery.md"},
    {id:"L-022",a:"PROCES",t:"Ét ad gangen > parallelt",o:"rules/genopbygning.md"},
    {id:"L-023",a:"PROCES",t:"Alt i filer, intet i chat",o:"rules/dokumentation.md"},
  ],
  rules:[
    {id:"R-01",r:"API-nøgler ALDRIG i Git",c:"SIK"},{id:"R-02",r:"Containere: restart+healthcheck+Loki",c:"DOC"},
    {id:"R-03",r:"Firewall (UFW)",c:"SIK"},{id:"R-04",r:"Ugentlig scan ClamAV+rkhunter",c:"SIK"},
    {id:"R-05",r:"Max 3 Claude-kald",c:"API"},{id:"R-06",r:"Max 50 API totalt",c:"API"},
    {id:"R-07",r:"Commits m/ beskrivelse",c:"GIT"},{id:"R-08",r:"Ugentlig backup",c:"BAK"},
    {id:"R-09",r:"Trivy scan images",c:"SIK"},{id:"R-10",r:"git-secrets før push",c:"SIK"},
    {id:"R-11",r:"Porte kun 127.0.0.1",c:"NET"},{id:"R-12",r:"0 TODO, fejlhåndtering",c:"KVA"},
    {id:"R-13",r:"nvidia-smi FØR Ollama",c:"AI"},
  ],
  bogforing:[
    {c:"A",n:"STATUS",f:10,l:8241,m:"01-discovery"},{c:"B",n:"COMMANDS",f:10,l:6671,m:"04-drift"},
    {c:"C",n:"CONFIG",f:10,l:9850,m:"05-kontrol"},{c:"D",n:"ARCHITECTURE",f:10,l:16787,m:"03-genopbyg"},
    {c:"E",n:"AGENTS",f:4,l:5060,m:"02-registrering"},{c:"F",n:"HISTORY",f:10,l:707,m:"07-log"},
    {c:"G",n:"LAPTOP",f:5,l:1751,m:"01-discovery"},{c:"H",n:"FLEET",f:2,l:642,m:"05-kontrol"},
    {c:"I",n:"OPS",f:8,l:5320,m:"05+07"},{c:"J",n:"META",f:2,l:6300,m:"00-styring"},
  ],
  cmds:[
    {id:"C01",n:"Dagligt tjek",cmd:"docker ps -a --format '{{.Names}}: {{.Status}}' && free -h && nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader",cat:"DRIFT"},
    {id:"C02",n:"Healthcheck alle",cmd:"for p in 9090 3100 3200 3000 5678 11434 9093; do curl -s --max-time 2 http://localhost:$p >/dev/null && echo \"$p: OK\" || echo \"$p: NEDE\"; done",cat:"DRIFT"},
    {id:"C03",n:"Docker oprydning",cmd:"docker system prune -f && docker image prune -f",cat:"VEDL"},
    {id:"C04",n:"Fejl 24h",cmd:"docker ps --format '{{.Names}}' | while read n; do e=$(docker logs \"$n\" --since 24h 2>&1 | grep -ci 'error\\|fatal\\|panic'); [ \"$e\" -gt 0 ] && echo \"$n: $e fejl\"; done",cat:"DIAG"},
    {id:"C05",n:"Ollama status",cmd:"ollama ps && nvidia-smi",cat:"AI"},
    {id:"C06",n:"Git status",cmd:"find ~ -maxdepth 3 -name '.git' -type d | while read g; do repo=$(dirname \"$g\"); echo \"=== $(basename $repo) ===\"; git -C \"$repo\" status -s; done",cat:"GIT"},
    {id:"C07",n:"Backup",cmd:"tar -czf ~/kv1ntos-backup-$(date +%F).tar.gz ~/kv1ntos/",cat:"BAK"},
    {id:"C08",n:"Porte",cmd:"ss -tlnp | grep -E ':(3000|3100|3200|5678|9090|9093|11434|7777|7778|7779|7800)' | sort",cat:"NET"},
    {id:"C09",n:"Komplet scan",cmd:"echo '=SCAN=' && docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' && echo && free -h && df -h / && nvidia-smi --query-gpu=memory.used,memory.free,temperature.gpu --format=csv,noheader && ollama ps 2>/dev/null",cat:"DISC"},
  ],
  tasks:[],captures:[],files:[],
  log:[{ts:new Date().toISOString().slice(0,16),w:"SYS",m:"v4.0 init"}],
};

const STS=["AFVENTER SCAN","I GANG","VENTER","KOMPLET","ÅBEN","AFVENTER TEST","IKKE STARTET","REGISTRERET","AFVENTER REG.","LUKKET"];
const TPS=["SVC","PLT","API","INT","DB","CTR","AGT","CUSTOM"];
const CTS=["CORE","OBS","AUTO","AI","PLT","PROJ","INT","DATA","DOCK","AGT","CUSTOM"];

function useS(k,i){const[d,sD]=useState(()=>{try{return window._kv?.[k]||i}catch{return i}});const s=useCallback(fn=>{sD(p=>{const n=typeof fn==="function"?fn(p):fn;if(!window._kv)window._kv={};window._kv[k]=n;return n})},[k]);return[d,s]}

const CSS=`@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{--bg:#060608;--b2:#0c0c10;--b3:#14141e;--bd:#1a1a24;--g:#d4a054;--gd:#6b5a3a;--gn:#4ade80;--rd:#f87171;--bl:#60a5fa;--pr:#c084fc;--cy:#22d3ee;--tx:#e2ddd4;--t2:#999;--t3:#555;--f:'Outfit',sans-serif;--m:'JetBrains Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--gd);border-radius:2px}
@keyframes fu{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes si{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:none}}
@keyframes glow{0%,100%{box-shadow:0 0 4px rgba(212,160,84,.1)}50%{box-shadow:0 0 12px rgba(212,160,84,.22)}}
@keyframes pl{0%,100%{opacity:1}50%{opacity:.4}}
.e{background:0;border:1px solid transparent;color:inherit;font:inherit;padding:1px 3px;width:100%;outline:0;border-radius:1px;transition:border .1s}.e:hover{border-color:var(--bd)}.e:focus{border-color:var(--g);background:var(--b3)}
.b{background:var(--b3);border:1px solid var(--bd);color:var(--t2);padding:4px 9px;font:500 10px var(--m);cursor:pointer;border-radius:1px;transition:all .1s;letter-spacing:.3px}.b:hover{border-color:var(--g);color:var(--g)}.bp{background:rgba(212,160,84,.07);border-color:var(--gd);color:var(--g)}.bd{color:var(--rd)}
.dz{border:2px dashed var(--gd);padding:20px;text-align:center;border-radius:2px;transition:all .12s;cursor:pointer}.dz:hover,.dz.ov{border-color:var(--g);background:rgba(212,160,84,.03)}
.di{cursor:grab;transition:all .1s}.di:active{cursor:grabbing;opacity:.6}.dov{background:rgba(212,160,84,.05)!important}
.trm{background:#08080c;border:1px solid var(--bd);border-radius:2px;font:11px/1.5 var(--m);color:var(--gn);padding:10px 12px;white-space:pre-wrap;word-break:break-all;overflow:auto;max-height:300px}
.tst{position:fixed;bottom:16px;right:16px;background:var(--g);color:#000;padding:6px 14px;font:600 11px var(--m);border-radius:2px;z-index:999;animation:fu .15s ease-out}
.kbd{display:inline-block;padding:0 4px;background:var(--b3);border:1px solid var(--bd);border-radius:1px;font:9px var(--m);color:var(--t3)}`;

// Status Badge
const SB=({s,onClick:oc})=>{const cl={"AFVENTER SCAN":"var(--g)","I GANG":"var(--gn)","VENTER":"var(--bl)","KOMPLET":"#4ade80","ÅBEN":"var(--rd)","AFVENTER TEST":"var(--g)","IKKE STARTET":"#444","KRITISK":"#ff4444","HØJ":"#f59e0b","MIDDEL":"#eab308","REGISTRERET":"#4ade80","AFVENTER REG.":"var(--g)","LUKKET":"#666"};const c=cl[s]||"#666";
return<span onClick={oc} style={{padding:"2px 6px",fontSize:9,fontFamily:"var(--m)",fontWeight:500,color:c,border:`1px solid ${c}33`,borderRadius:1,whiteSpace:"nowrap",cursor:oc?"pointer":"default",letterSpacing:.5}}>{s}</span>};

// Editable
const EF=({v,onSave:os,mono:mn,multi:ml})=>{const[ed,sE]=useState(false);const[val,sV]=useState(v);const r=useRef();useEffect(()=>{sV(v)},[v]);useEffect(()=>{if(ed&&r.current)r.current.focus()},[ed]);
if(!ed)return<span onClick={()=>sE(true)} style={{cursor:"pointer",fontFamily:mn?"var(--m)":"inherit",borderBottom:"1px dashed transparent",transition:"border .08s"}} onMouseEnter={e=>e.currentTarget.style.borderBottomColor="var(--gd)"} onMouseLeave={e=>e.currentTarget.style.borderBottomColor="transparent"}>{v||<i style={{color:"var(--t3)"}}>—</i>}</span>;
const sv=()=>{sE(false);if(val!==v)os(val)};
if(ml)return<textarea ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Escape"){sV(v);sE(false)}}} rows={3} style={{fontFamily:mn?"var(--m)":"var(--f)",fontSize:11,resize:"vertical"}}/>;
return<input ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Enter")sv();if(e.key==="Escape"){sV(v);sE(false)}}} style={{fontFamily:mn?"var(--m)":"var(--f)",fontSize:11}}/>};

const SF=({v,opts:o,onSave:os})=><select value={v} onChange={e=>os(e.target.value)} style={{background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",padding:"2px 4px",fontSize:10,fontFamily:"var(--m)",borderRadius:1,cursor:"pointer"}}>{o.map(x=><option key={x} value={x}>{x}</option>)}</select>;

const SH=({id,title,cnt,act})=><div style={{marginTop:22,marginBottom:8,paddingBottom:6,borderBottom:"1px solid var(--bd)",display:"flex",justifyContent:"space-between",alignItems:"center"}}><div style={{display:"flex",alignItems:"baseline",gap:7}}><span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--g)",letterSpacing:2,fontWeight:600}}>{id}</span><h2 style={{fontSize:15,fontWeight:600,color:"var(--tx)",fontFamily:"var(--f)"}}>{title}</h2>{cnt!=null&&<span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--t3)"}}>({cnt})</span>}</div>{act}</div>;

// Parse terminal output
const parseTerm=(text)=>{const found=[];let m;
const dr=/^(\S+):\s*(Up|Exited|Created|Running|Restarting)/gm;while((m=dr.exec(text)))found.push({tp:"container",nm:m[1],st:m[2].startsWith("Up")?"KØRER":"STOPPET"});
const pr=/[\s:](\d{4,5})(?:[\/\s\->]|$)/gm;const ports=new Set();while((m=pr.exec(text)))ports.add(m[1]);
const or=/^(\S+:\S+)\s+(\d[\d.]*\s*[GMK]B)/gm;while((m=or.exec(text)))found.push({tp:"model",nm:m[1],sz:m[2]});
return{found,ports:[...ports]}};

// ═══ MAIN ═══
export default function App(){
  const[D,sD]=useS("kv4",INIT);
  const[sec,sSec]=useState("overview");const[q,sQ]=useState("");const[sel,sSel]=useState(null);const[mod,sMod]=useState(null);const[toast,sToast]=useState("");const[cap,sCap]=useState(false);const[dragId,sDI]=useState(null);const[dragO,sDO]=useState(null);
  const fR=useRef();const sR=useRef();const cR=useRef();

  const ts=()=>new Date().toISOString().slice(0,16);
  const lg=m=>sD(d=>({...d,log:[{ts:ts(),w:"ADM",m},...(d.log||[]).slice(0,199)]}));
  const flash=m=>{sToast(m);setTimeout(()=>sToast(""),1800)};
  const cp=t=>{navigator.clipboard?.writeText(t);flash("Kopieret")};

  // Mutators
  const uI=(id,f,v)=>{sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,[f]:v}:i)}));lg(`${id}.${f}`)};
  const dI=id=>{if(!confirm(`Slet ${id}?`))return;sD(d=>({...d,items:d.items.filter(i=>i.id!==id)}));lg(`DEL:${id}`);sSel(null)};
  const aI=it=>{sD(d=>({...d,items:[...d.items,it]}));lg(`NY:${it.id}`);flash("Tilføjet")};
  const aAnn=(id,t)=>sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,ann:[{ts:ts(),t},...(i.ann||[])]}:i)}));
  const tPin=id=>sD(d=>({...d,items:d.items.map(i=>i.id===id?{...i,pin:!i.pin}:i)}));
  const aTask=t=>{sD(d=>({...d,tasks:[...(d.tasks||[]),t]}));lg(`TASK:${t.title}`)};
  const uTask=(idx,f,v)=>sD(d=>({...d,tasks:(d.tasks||[]).map((t,i)=>i===idx?{...t,[f]:v}:t)}));
  const aCap=c=>{sD(d=>({...d,captures:[{ts:ts(),text:c},...(d.captures||[])]}));lg("CAPTURE");flash("Capture gemt")};
  const aFile=f=>{sD(d=>({...d,files:[...(d.files||[]),f]}));lg(`FIL:${f.name}`)};
  const hFiles=fs=>Array.from(fs).forEach(f=>{const r=new FileReader();r.onload=e=>aFile({name:f.name,size:f.size,type:f.type,dt:ts(),content:e.target.result});r.readAsText(f)});

  const exportJ=()=>{const b=new Blob([JSON.stringify(D,null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=`kv1ntos-${ts().replace(/:/g,"")}.json`;a.click();flash("Exporteret")};

  // Keys
  useEffect(()=>{const h=e=>{const m=e.metaKey||e.ctrlKey;if(m&&e.key==="k"){e.preventDefault();sCap(p=>!p);setTimeout(()=>cR.current?.focus(),80)}if(m&&e.key==="n"){e.preventDefault();sMod("item")}if(m&&e.key==="f"){e.preventDefault();sR.current?.focus()}if(m&&e.key==="e"){e.preventDefault();exportJ()}if(e.key==="Escape"){sSel(null);sMod(null);sCap(false)}};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[]);

  const items=D.items||[];const pinned=items.filter(i=>i.pin);const byTp=t=>items.filter(i=>i.tp===t);
  const filtered=useMemo(()=>{if(!q.trim())return[];const ql=q.toLowerCase();return items.filter(i=>i.nm.toLowerCase().includes(ql)||i.id.toLowerCase().includes(ql)||(i.nt||"").toLowerCase().includes(ql))},[items,q]);
  const st={tot:items.length,ver:items.filter(i=>i.st==="KOMPLET"||i.st==="REGISTRERET").length,err:(D.errors||[]).filter(e=>e.st==="ÅBEN").length};

  const td={padding:"5px 7px",fontSize:10,borderBottom:"1px solid rgba(26,26,36,.2)"};

  // Item Table
  const IT=({rows,showTp})=><div style={{overflowX:"auto",marginBottom:10}}><table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}>
    <thead><tr>{["⋮","★","ID","NAVN",showTp&&"TP","PORT","STATUS","F","BOG"].filter(Boolean).map((h,i)=><th key={i} style={{textAlign:"left",padding:"5px 7px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,fontWeight:600,letterSpacing:1,background:"var(--b2)",position:"sticky",top:0,zIndex:2}}>{h}</th>)}</tr></thead>
    <tbody>{rows.map((r,i)=><tr key={r.id} draggable onDragStart={e=>{sDI(r.id);e.dataTransfer.effectAllowed="move"}} onDragOver={e=>{e.preventDefault();sDO(r.id)}} onDrop={e=>{e.preventDefault();sDO(null);if(dragId&&dragId!==r.id){sD(d=>{const a=[...d.items];const fi=a.findIndex(x=>x.id===dragId);const ti=a.findIndex(x=>x.id===r.id);if(fi<0||ti<0)return d;const[mv]=a.splice(fi,1);a.splice(ti,0,mv);return{...d,items:a}});sDI(null)}}} onDragEnd={()=>{sDI(null);sDO(null)}}
      className={`di${dragO===r.id?" dov":""}`} onClick={()=>sSel(r.id)} style={{cursor:"pointer",borderBottom:"1px solid rgba(26,26,36,.2)",animation:`fu .2s ease-out ${i*15}ms both`}}
      onMouseEnter={e=>e.currentTarget.style.background="rgba(212,160,84,.02)"} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
      <td style={td}><span style={{color:"var(--t3)",cursor:"grab",fontSize:9}}>⋮</span></td>
      <td style={td}><span onClick={e=>{e.stopPropagation();tPin(r.id)}} style={{cursor:"pointer",fontSize:11}}>{r.pin?"⭐":"☆"}</span></td>
      <td style={{...td,color:"var(--g)",fontWeight:500,fontSize:9}}>{r.id}</td>
      <td style={{...td,color:"var(--tx)"}}>{r.nm}</td>
      {showTp&&<td style={{...td,color:"var(--t2)",fontSize:9}}>{r.tp}</td>}
      <td style={{...td,color:"var(--cy)"}}>{r.pt||"—"}</td>
      <td style={td}><SB s={r.st} onClick={e=>{e.stopPropagation();const ci=STS.indexOf(r.st);uI(r.id,"st",STS[(ci+1)%STS.length])}}/></td>
      <td style={{...td,color:"var(--t3)",fontSize:9}}>F{r.ph}</td>
      <td style={{...td,color:"var(--pr)",fontSize:8}}>{(r.bg||[]).join(",")}</td>
    </tr>)}</tbody></table></div>;

  // Nav
  const NAV=[{id:"overview",l:"OVERBLIK"},{id:"all",l:"ALLE"},{id:"capture",l:"⌨ TERMINAL"},{id:"tasks",l:"☐ OPGAVER"},
    {id:"services",l:"SERVICES"},{id:"platforms",l:"PLATFORME"},{id:"apis",l:"API'ER"},{id:"integrations",l:"INT."},{id:"containers",l:"CONTAINERE"},{id:"agents",l:"AGENTER"},{id:"databases",l:"DATABASER"},
    {id:"commands",l:"$ KOMMANDOER"},{id:"files",l:"📁 FILER"},{id:"bogforing",l:"📋 BOG. A-J"},
    {id:"errors",l:"⚠ FEJL"},{id:"learnings",l:"LEARNINGS"},{id:"rules",l:"⛨ ODIN"},{id:"log",l:"LOG"}];

  return<>
    <style>{CSS}</style>
    <div style={{display:"flex",minHeight:"100vh",background:"var(--bg)",color:"var(--tx)",fontFamily:"var(--f)"}}>
      {/* SIDEBAR */}
      <nav style={{width:160,borderRight:"1px solid var(--bd)",position:"fixed",top:0,left:0,height:"100vh",overflowY:"auto",background:"rgba(6,6,8,.97)",zIndex:50,display:"flex",flexDirection:"column"}}>
        <div style={{padding:"10px 12px 8px",borderBottom:"1px solid var(--bd)"}}>
          <div style={{fontFamily:"var(--m)",fontSize:11,color:"var(--g)",letterSpacing:3,fontWeight:700}}>KV1NTOS</div>
          <div style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)"}}>OPS CENTER v4</div>
          <div style={{marginTop:4,display:"flex",gap:3,alignItems:"center"}}><span style={{width:4,height:4,borderRadius:"50%",background:"var(--gn)",animation:"pl 2s infinite"}}/><span style={{fontSize:8,color:"var(--t2)",fontFamily:"var(--m)"}}>F0 DISCOVERY</span></div>
        </div>
        <div style={{flex:1,padding:"3px 0",overflowY:"auto"}}>
          {NAV.map(n=><button key={n.id} onClick={()=>{sSec(n.id);sSel(null);sQ("")}} style={{display:"block",width:"100%",padding:"5px 12px",background:sec===n.id?"rgba(212,160,84,.05)":"transparent",border:"none",borderLeft:sec===n.id?"2px solid var(--g)":"2px solid transparent",color:sec===n.id?"var(--tx)":"var(--t3)",cursor:"pointer",fontSize:9,fontFamily:"var(--m)",textAlign:"left",transition:"all .1s"}}
            onMouseEnter={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t2)"}} onMouseLeave={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t3)"}}>{n.l}</button>)}
        </div>
        <div style={{padding:"6px 12px",borderTop:"1px solid var(--bd)",fontSize:8,fontFamily:"var(--m)"}}>
          <div style={{display:"flex",justifyContent:"space-between"}}><span style={{color:"var(--t3)"}}>Elem</span><span style={{color:"var(--g)"}}>{st.tot}</span></div>
          <div style={{display:"flex",justifyContent:"space-between"}}><span style={{color:"var(--t3)"}}>Verif</span><span style={{color:st.ver?"var(--gn)":"var(--rd)"}}>{st.ver}</span></div>
          <div style={{display:"flex",gap:3,marginTop:4}}><button className="b" style={{flex:1,fontSize:8,padding:"2px"}} onClick={exportJ}>EXP</button><button className="b" style={{flex:1,fontSize:8,padding:"2px"}} onClick={()=>sD(INIT)}>RST</button></div>
          <div style={{marginTop:3,textAlign:"center",color:"var(--t3)",fontSize:7}}><kbd className="kbd">⌘K</kbd> cap <kbd className="kbd">⌘N</kbd> ny <kbd className="kbd">⌘F</kbd> søg</div>
        </div>
      </nav>

      {/* MAIN */}
      <main style={{flex:1,marginLeft:160,padding:"12px 22px 40px",maxWidth:920}}>
        {/* SEARCH */}
        <div style={{display:"flex",gap:5,marginBottom:14}}>
          <input ref={sR} value={q} onChange={e=>sQ(e.target.value)} placeholder="Søg (⌘F)" style={{flex:1,padding:"7px 10px",background:"var(--b2)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",outline:0,borderRadius:1}} onFocus={e=>e.target.style.borderColor="var(--gd)"} onBlur={e=>e.target.style.borderColor="var(--bd)"}/>
          <button className="b bp" onClick={()=>sMod("item")}>+ NY</button>
          <button className="b" onClick={()=>{sCap(p=>!p);setTimeout(()=>cR.current?.focus(),80)}}>⌨</button>
          <label className="b" style={{cursor:"pointer"}}><span>↑IMP</span><input type="file" accept=".json" style={{display:"none"}} onChange={e=>{if(e.target.files[0]){const r=new FileReader();r.onload=ev=>{try{sD(JSON.parse(ev.target.result));flash("Import OK")}catch{alert("Ugyldig JSON")}};r.readAsText(e.target.files[0])}}}/></label>
        </div>

        {/* CAPTURE */}
        {cap&&<div style={{marginBottom:14,background:"var(--b2)",border:"1px solid var(--gd)",borderRadius:2,padding:12,animation:"fu .15s ease-out"}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}><span style={{fontFamily:"var(--m)",fontSize:10,color:"var(--g)"}}>⌨ TERMINAL CAPTURE</span><button className="b" style={{fontSize:8,padding:"1px 6px"}} onClick={()=>sCap(false)}>✕</button></div>
          <textarea ref={cR} placeholder="Paste terminal output her..." style={{width:"100%",minHeight:60,background:"#08080c",border:"1px solid var(--bd)",color:"var(--gn)",fontFamily:"var(--m)",fontSize:10,padding:8,borderRadius:1,resize:"vertical",outline:0}} onKeyDown={e=>{if((e.metaKey||e.ctrlKey)&&e.key==="Enter"&&cR.current.value.trim()){aCap(cR.current.value);cR.current.value=""}}}/>
          <div style={{display:"flex",justifyContent:"space-between",marginTop:4}}><span style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)"}}>⌘+Enter = gem</span><button className="b bp" style={{fontSize:9}} onClick={()=>{if(cR.current?.value.trim()){aCap(cR.current.value);cR.current.value=""}}}>GEM</button></div>
        </div>}

        {q.trim()&&<><SH id="SØG" title={`"${q}"`} cnt={filtered.length}/><IT rows={filtered} showTp/></>}

        {/* OVERVIEW */}
        {sec==="overview"&&!q.trim()&&<>
          <h1 style={{fontSize:20,fontWeight:800,color:"var(--tx)",animation:"fu .2s ease-out"}}>KV1NTOS OPERATIONS CENTER</h1>
          <p style={{fontSize:10,color:"var(--t2)",marginBottom:14}}>{st.tot} elem | {st.err} fejl | {(D.captures||[]).length} captures | {(D.tasks||[]).length} tasks</p>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(100px,1fr))",gap:5,marginBottom:18}}>
            {[{l:"ELEMENTER",v:st.tot},{l:"VERIFICERET",v:st.ver,c:"var(--gn)"},{l:"SERVICES",v:byTp("SVC").length},{l:"PLATFORME",v:byTp("PLT").length},{l:"API'ER",v:byTp("API").length},{l:"FEJL",v:st.err,c:"var(--rd)"},{l:"CAPTURES",v:(D.captures||[]).length,c:"var(--gn)"},{l:"TASKS",v:(D.tasks||[]).length,c:"var(--pr)"}].map((s,i)=>
              <div key={i} style={{background:"var(--b2)",border:"1px solid var(--bd)",padding:"10px 12px",borderRadius:1,animation:`fu .3s ease-out ${i*25}ms both`}}>
                <div style={{fontFamily:"var(--m)",fontSize:20,fontWeight:700,color:s.c||"var(--g)",lineHeight:1}}>{s.v}</div>
                <div style={{fontSize:9,color:"var(--t2)",marginTop:2}}>{s.l}</div></div>)}
          </div>
          {pinned.length>0&&<><SH id="★" title="PINNED" cnt={pinned.length}/><IT rows={pinned} showTp/></>}
          <SH id="F" title="FASER" cnt={8}/>
          <div style={{display:"flex",gap:2,marginBottom:14}}>{D.phases.map(p=><div key={p.id} onClick={()=>{const nx=p.s==="VENTER"?"I GANG":p.s==="I GANG"?"KOMPLET":"VENTER";sD(d=>({...d,phases:d.phases.map(x=>x.id===p.id?{...x,s:nx}:x)}));lg(`F${p.id}:${nx}`)}} style={{flex:1,padding:"7px 3px",background:p.s==="I GANG"?"rgba(212,160,84,.04)":p.s==="KOMPLET"?"rgba(74,222,128,.04)":"var(--b2)",border:`1px solid ${p.s==="I GANG"?"var(--gd)":p.s==="KOMPLET"?"#1a4a2a":"var(--bd)"}`,textAlign:"center",cursor:"pointer",borderRadius:1,position:"relative"}}>
            {p.s==="I GANG"&&<div style={{position:"absolute",top:0,left:0,right:0,height:2,background:"var(--g)",animation:"glow 2s infinite"}}/>}
            {p.s==="KOMPLET"&&<div style={{position:"absolute",top:0,left:0,right:0,height:2,background:"var(--gn)"}}/>}
            <div style={{fontFamily:"var(--m)",fontSize:13,fontWeight:700,color:p.s==="I GANG"?"var(--g)":p.s==="KOMPLET"?"var(--gn)":"var(--t3)"}}>{p.id}</div>
            <div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)"}}>{p.n}</div></div>)}</div>
          <SH id="LOG" title="SENESTE" cnt={Math.min((D.log||[]).length,5)}/>
          {(D.log||[]).slice(0,5).map((l,i)=><div key={i} style={{padding:"3px 0",borderBottom:"1px solid rgba(26,26,36,.15)",display:"flex",gap:6,fontSize:9,fontFamily:"var(--m)",color:"var(--t2)"}}><span style={{color:"var(--t3)",width:100,flexShrink:0}}>{l.ts}</span><span style={{color:"var(--g)",width:35,flexShrink:0}}>{l.w}</span><span>{l.m}</span></div>)}
        </>}

        {sec==="all"&&!q.trim()&&<><SH id="ALL" title="ALLE" cnt={items.length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={items} showTp/></>}

        {/* TERMINAL */}
        {sec==="capture"&&!q.trim()&&<><SH id="⌨" title="TERMINAL CAPTURES" cnt={(D.captures||[]).length} act={<button className="b bp" onClick={()=>{sCap(true);setTimeout(()=>cR.current?.focus(),80)}}>+ CAPTURE</button>}/>
          <p style={{fontSize:10,color:"var(--t2)",marginBottom:10}}>Workflow: Kør kommando i terminal → kopiér output → <kbd className="kbd">⌘K</kbd> → paste → <kbd className="kbd">⌘Enter</kbd>. Auto-parser detekterer containere, porte, modeller.</p>
          {!cap&&<button className="b bp" onClick={()=>{sCap(true);setTimeout(()=>cR.current?.focus(),80)}} style={{width:"100%",padding:12,marginBottom:12}}>⌨ ÅBN CAPTURE (⌘K)</button>}
          {(D.captures||[]).map((c,i)=>{const p=parseTerm(c.text);return<div key={i} style={{marginBottom:10,animation:`fu .2s ease-out ${i*20}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}><span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--t3)"}}>{c.ts}</span><div style={{display:"flex",gap:3}}>{p.found.length>0&&<span style={{fontSize:8,color:"var(--gn)",fontFamily:"var(--m)"}}>{p.found.length} fundet</span>}<button className="b" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>cp(c.text)}>CP</button><button className="b bd" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>sD(d=>({...d,captures:(d.captures||[]).filter((_,j)=>j!==i)}))}>✕</button></div></div>
            <div className="trm" style={{maxHeight:160}}>{c.text}</div>
            {p.found.length>0&&<div style={{marginTop:4,padding:6,background:"rgba(74,222,128,.03)",border:"1px solid rgba(74,222,128,.1)",borderRadius:1,fontSize:9,fontFamily:"var(--m)"}}>
              {p.found.map((f,fi)=><div key={fi} style={{color:"var(--tx)"}}>{f.tp}: <span style={{color:"var(--cy)"}}>{f.nm}</span> {f.st&&<SB s={f.st}/>}{f.sz&&<span style={{color:"var(--t2)"}}> {f.sz}</span>}</div>)}
              {p.ports.length>0&&<div style={{color:"var(--t2)",marginTop:2}}>Porte: {p.ports.join(", ")}</div>}
            </div>}</div>})}
        </>}

        {/* TASKS */}
        {sec==="tasks"&&!q.trim()&&<><SH id="TSK" title="OPGAVER" cnt={(D.tasks||[]).length} act={<button className="b bp" onClick={()=>sMod("task")}>+ OPGAVE</button>}/>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8}}>
            {["TODO","I GANG","KOMPLET"].map(col=><div key={col}>
              <div style={{fontSize:9,fontFamily:"var(--m)",color:col==="TODO"?"var(--rd)":col==="I GANG"?"var(--g)":"var(--gn)",letterSpacing:1,marginBottom:6,paddingBottom:3,borderBottom:`1px solid ${col==="TODO"?"var(--rd)":col==="I GANG"?"var(--gd)":"#1a4a2a"}33`}}>{col} ({(D.tasks||[]).filter(t=>t.s===col).length})</div>
              {(D.tasks||[]).filter(t=>t.s===col).map((t,i)=>{const idx=(D.tasks||[]).indexOf(t);return<div key={i} style={{background:"var(--b2)",border:"1px solid var(--bd)",padding:"8px 10px",marginBottom:4,borderRadius:1,fontSize:11}}>
                <div style={{fontWeight:600,marginBottom:3}}>{t.title}</div>
                {t.desc&&<div style={{fontSize:9,color:"var(--t2)",marginBottom:4}}>{t.desc}</div>}
                <div style={{display:"flex",gap:3}}>{col!=="TODO"&&<button className="b" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>uTask(idx,"s",col==="I GANG"?"TODO":"I GANG")}>←</button>}{col!=="KOMPLET"&&<button className="b" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>uTask(idx,"s",col==="TODO"?"I GANG":"KOMPLET")}>→</button>}</div>
              </div>})}</div>)}
          </div>
        </>}

        {/* TYPE SECTIONS */}
        {sec==="services"&&!q.trim()&&<><SH id="SVC" title="SERVICES" cnt={byTp("SVC").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("SVC")}/></>}
        {sec==="platforms"&&!q.trim()&&<><SH id="PLT" title="PLATFORME" cnt={byTp("PLT").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("PLT")}/></>}
        {sec==="apis"&&!q.trim()&&<><SH id="API" title="API'ER" cnt={byTp("API").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("API")}/></>}
        {sec==="integrations"&&!q.trim()&&<><SH id="INT" title="INTEGRATIONER" cnt={byTp("INT").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("INT")}/></>}
        {sec==="containers"&&!q.trim()&&<><SH id="CTR" title="CONTAINERE" cnt={byTp("CTR").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("CTR")}/></>}
        {sec==="agents"&&!q.trim()&&<><SH id="AGT" title="AGENTER" cnt={byTp("AGT").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("AGT")}/></>}
        {sec==="databases"&&!q.trim()&&<><SH id="DB" title="DATABASER" cnt={byTp("DB").length} act={<button className="b bp" onClick={()=>sMod("item")}>+</button>}/><IT rows={byTp("DB")}/></>}

        {/* COMMANDS */}
        {sec==="commands"&&!q.trim()&&<><SH id="$" title="KOMMANDO-BIBLIOTEK" cnt={(D.cmds||[]).length}/>
          <p style={{fontSize:10,color:"var(--t2)",marginBottom:10}}>Klik KOPIÉR → paste i terminal → kør → kopiér output → <kbd className="kbd">⌘K</kbd> capture</p>
          {(D.cmds||[]).map((c,i)=><div key={c.id} style={{marginBottom:6,animation:`fu .2s ease-out ${i*20}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:2}}>
              <div style={{display:"flex",gap:6,alignItems:"center"}}><span style={{fontFamily:"var(--m)",fontSize:9,color:"var(--g)"}}>{c.id}</span><span style={{fontSize:11,fontWeight:600}}>{c.n}</span><span style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)",padding:"0 4px",background:"var(--b3)",borderRadius:1}}>{c.cat}</span></div>
              <button className="b" style={{fontSize:8,padding:"2px 6px"}} onClick={()=>cp(c.cmd)}>KOPIÉR</button></div>
            <div className="trm" style={{maxHeight:50,fontSize:10,cursor:"pointer"}} onClick={()=>cp(c.cmd)}>{c.cmd}</div></div>)}
        </>}

        {/* FILES */}
        {sec==="files"&&!q.trim()&&<><SH id="📁" title="FILER" cnt={(D.files||[]).length}/>
          <div className="dz" onDrop={e=>{e.preventDefault();e.currentTarget.classList.remove("ov");hFiles(e.dataTransfer.files)}} onDragOver={e=>{e.preventDefault();e.currentTarget.classList.add("ov")}} onDragLeave={e=>e.currentTarget.classList.remove("ov")} onClick={()=>fR.current?.click()}>
            <input ref={fR} type="file" multiple style={{display:"none"}} onChange={e=>hFiles(e.target.files)}/><div style={{fontSize:10,color:"var(--t2)",fontFamily:"var(--m)"}}>Drop filer eller klik</div></div>
          {(D.files||[]).map((f,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"6px 8px",borderBottom:"1px solid var(--bd)",fontSize:10}}>
            <span>{f.name} <span style={{color:"var(--t3)",fontFamily:"var(--m)",fontSize:8}}>{(f.size/1024).toFixed(1)}KB</span></span>
            <div style={{display:"flex",gap:3}}>{f.content&&<button className="b" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>sMod({tp:"file",f})}>VIS</button>}<button className="b bd" style={{fontSize:8,padding:"1px 5px"}} onClick={()=>sD(d=>({...d,files:(d.files||[]).filter(x=>x.name!==f.name)}))}>✕</button></div></div>)}
        </>}

        {/* BOGFORING */}
        {sec==="bogforing"&&!q.trim()&&<><SH id="A-J" title="BOGFØRINGSMAPPE" cnt={`${(D.bogforing||[]).reduce((s,b)=>s+b.f,0)} filer`}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["KAT","NAVN","FIL","LINJER","→MANUAL"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"5px 7px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.bogforing||[]).map((b,i)=><tr key={i}><td style={{...td,color:"var(--g)",fontWeight:800,fontSize:13}}>{b.c}</td><td style={td}>{b.n}</td><td style={{...td,textAlign:"center"}}>{b.f}</td><td style={{...td,textAlign:"right"}}>{b.l.toLocaleString()}</td><td style={{...td,color:"var(--cy)"}}>{b.m}</td></tr>)}</tbody></table>
        </>}

        {/* ERRORS */}
        {sec==="errors"&&!q.trim()&&<><SH id="ERR" title="FEJL" cnt={(D.errors||[]).length} act={<button className="b bp" onClick={()=>sMod("error")}>+ FEJL</button>}/>
          {(D.errors||[]).map((e,i)=><div key={e.id} style={{display:"grid",gridTemplateColumns:"55px 60px 1fr 70px 60px 24px",gap:4,padding:"6px 8px",borderBottom:"1px solid var(--bd)",fontSize:10,alignItems:"center"}}>
            <span style={{color:"var(--g)",fontSize:9}}>{e.id}</span><EF v={e.sr} onSave={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,sr:v}:x)}))}/><EF v={e.ds} onSave={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,ds:v}:x)}))}/>
            <SB s={e.sv}/><SF v={e.st} opts={["ÅBEN","I GANG","LUKKET"]} onSave={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,st:v}:x)}))}/><button className="b bd" style={{padding:"0 3px",fontSize:8}} onClick={()=>sD(d=>({...d,errors:d.errors.filter(x=>x.id!==e.id)}))}>✕</button></div>)}
        </>}

        {/* LEARNINGS */}
        {sec==="learnings"&&!q.trim()&&<><SH id="LRN" title="LEARNINGS" cnt={(D.learnings||[]).length} act={<button className="b bp" onClick={()=>sMod("learning")}>+</button>}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["ID","OMR","LEARNING","→ODIN"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"5px 7px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.learnings||[]).map((l,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{l.id}</td><td style={{...td,color:"var(--t2)"}}>{l.a}</td><td style={td}>{l.t}</td><td style={{...td,color:"var(--pr)",fontSize:8}}>{l.o}</td></tr>)}</tbody></table>
        </>}

        {/* RULES */}
        {sec==="rules"&&!q.trim()&&<><SH id="⛨" title="ODIN REGLER" cnt={(D.rules||[]).length}/>
          <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:10,fontFamily:"var(--m)"}}><thead><tr>{["ID","REGEL","KAT"].map((h,i)=><th key={i} style={{textAlign:"left",padding:"5px 7px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:8,background:"var(--b2)"}}>{h}</th>)}</tr></thead>
            <tbody>{(D.rules||[]).map((r,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{r.id}</td><td style={td}>{r.r}</td><td style={{...td,color:"var(--t2)"}}>{r.c}</td></tr>)}</tbody></table>
          <div style={{marginTop:8,padding:8,background:"rgba(248,113,113,.03)",border:"1px solid rgba(248,113,113,.1)",borderRadius:1,fontSize:10,color:"var(--rd)"}}>UFRAVIGELIGE</div>
        </>}

        {/* LOG */}
        {sec==="log"&&!q.trim()&&<><SH id="LOG" title="ÆNDRINGSLOG" cnt={(D.log||[]).length} act={<button className="b" onClick={exportJ}>EXP</button>}/>
          {(D.log||[]).map((l,i)=><div key={i} style={{padding:"3px 0",borderBottom:"1px solid rgba(26,26,36,.15)",display:"grid",gridTemplateColumns:"110px 40px 1fr",gap:5,fontSize:9,fontFamily:"var(--m)",color:"var(--t2)"}}><span style={{color:"var(--t3)"}}>{l.ts}</span><span style={{color:"var(--g)"}}>{l.w}</span><span>{l.m}</span></div>)}
        </>}
      </main>
    </div>

    {/* DETAIL PANEL */}
    {sel&&(()=>{const it=items.find(i=>i.id===sel);if(!it)return null;return<div style={{position:"fixed",inset:0,zIndex:200}} onClick={()=>sSel(null)}>
      <div style={{position:"absolute",inset:0,background:"rgba(0,0,0,.45)",backdropFilter:"blur(3px)"}}/>
      <div onClick={e=>e.stopPropagation()} style={{position:"absolute",right:0,top:0,width:400,height:"100vh",background:"var(--bg)",borderLeft:"1px solid var(--gd)",overflowY:"auto",padding:"16px 20px",animation:"si .18s ease-out"}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:14}}><div style={{display:"flex",gap:6,alignItems:"center"}}><span style={{fontFamily:"var(--m)",fontSize:11,color:"var(--g)",fontWeight:600}}>{it.id}</span><span onClick={()=>tPin(it.id)} style={{cursor:"pointer",fontSize:13}}>{it.pin?"⭐":"☆"}</span></div><div style={{display:"flex",gap:3}}><button className="b bd" onClick={()=>dI(it.id)}>SLET</button><button className="b" onClick={()=>sSel(null)}>ESC</button></div></div>
        <div style={{fontSize:17,fontWeight:700,marginBottom:12}}><EF v={it.nm} onSave={v=>uI(it.id,"nm",v)}/></div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:12}}>
          {[["TYPE",<SF v={it.tp} opts={TPS} onSave={v=>uI(it.id,"tp",v)}/>],["STATUS",<SF v={it.st} opts={STS} onSave={v=>uI(it.id,"st",v)}/>],["PORT",<EF v={it.pt} mono onSave={v=>uI(it.id,"pt",v)}/>],["KAT",<SF v={it.ct} opts={CTS} onSave={v=>uI(it.id,"ct",v)}/>],["FASE",<SF v={String(it.ph)} opts={["0","1","2","3","4","5","6","7"]} onSave={v=>uI(it.id,"ph",+v)}/>],["HEALTH",<EF v={it.hc} mono onSave={v=>uI(it.id,"hc",v)}/>]].map(([l,c],i)=><div key={i}><div style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.8,marginBottom:1}}>{l}</div>{c}</div>)}
        </div>
        {[["BOG","bg"],["AFHÆNGER","dp"],["BRUGES AF","db"]].map(([l,k])=><div key={k} style={{marginBottom:8}}><div style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.8,marginBottom:1}}>{l}</div><EF v={(it[k]||[]).join(", ")} mono onSave={v=>uI(it.id,k,v.split(",").map(s=>s.trim()).filter(Boolean))}/></div>)}
        <div style={{marginBottom:12}}><div style={{fontSize:8,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.8,marginBottom:1}}>NOTER</div><EF v={it.nt} multi onSave={v=>uI(it.id,"nt",v)}/></div>
        <div style={{borderTop:"1px solid var(--bd)",paddingTop:10}}>
          <div style={{fontSize:8,color:"var(--g)",fontFamily:"var(--m)",letterSpacing:1,marginBottom:4}}>ANNOTATIONER</div>
          <div style={{display:"flex",gap:3,marginBottom:6}}><input id="ann-in" placeholder="Tilføj..." style={{flex:1,padding:"5px 7px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",outline:0,borderRadius:1}} onKeyDown={e=>{if(e.key==="Enter"&&e.target.value.trim()){aAnn(it.id,e.target.value);e.target.value=""}}}/><button className="b" style={{fontSize:8}} onClick={()=>{const inp=document.getElementById("ann-in");if(inp?.value.trim()){aAnn(it.id,inp.value);inp.value=""}}}>+</button></div>
          {(it.ann||[]).map((a,i)=><div key={i} style={{fontSize:9,color:"var(--t2)",padding:"2px 0",borderBottom:"1px solid rgba(26,26,36,.15)"}}><span style={{color:"var(--t3)",fontFamily:"var(--m)",fontSize:8,marginRight:4}}>{a.ts}</span>{a.t}</div>)}
        </div>
      </div>
    </div>})()}

    {/* MODALS */}
    {mod==="item"&&<Md t="NYT ELEMENT" oc={()=>sMod(null)}><NI onAdd={it=>{aI(it);sMod(null)}} its={items}/></Md>}
    {mod==="error"&&<Md t="NY FEJL" oc={()=>sMod(null)}><NE onAdd={e=>{sD(d=>({...d,errors:[...d.errors,e]}));lg(`ERR:${e.ds}`);sMod(null)}} es={D.errors||[]}/></Md>}
    {mod==="learning"&&<Md t="NY LEARNING" oc={()=>sMod(null)}><NL onAdd={l=>{sD(d=>({...d,learnings:[...d.learnings,l]}));lg(`LRN:${l.t}`);sMod(null)}} ls={D.learnings||[]}/></Md>}
    {mod==="task"&&<Md t="NY OPGAVE" oc={()=>sMod(null)}><NT onAdd={t=>{aTask(t);sMod(null)}}/></Md>}
    {mod?.tp==="file"&&<Md t={mod.f.name} oc={()=>sMod(null)}><pre className="trm" style={{maxHeight:400}}>{mod.f.content}</pre></Md>}
    {toast&&<div className="tst">{toast}</div>}
  </>;
}

// Modal
function Md({t,oc,children}){useEffect(()=>{const h=e=>{if(e.key==="Escape")oc()};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[oc]);
return<div style={{position:"fixed",inset:0,zIndex:300,display:"flex",alignItems:"center",justifyContent:"center"}} onClick={oc}><div style={{position:"absolute",inset:0,background:"rgba(0,0,0,.55)",backdropFilter:"blur(3px)"}}/><div onClick={e=>e.stopPropagation()} style={{background:"var(--bg)",border:"1px solid var(--gd)",padding:"18px 22px",borderRadius:2,width:440,maxHeight:"75vh",overflowY:"auto",animation:"fu .15s ease-out"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:14}}><h3 style={{fontFamily:"var(--m)",fontSize:12,color:"var(--g)",letterSpacing:1}}>{t}</h3><button className="b" onClick={oc}>✕</button></div>{children}</div></div>}

const inp2={width:"100%",padding:"6px 8px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:10,fontFamily:"var(--m)",borderRadius:1,outline:0};
const fl2={display:"block",fontSize:8,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:.6,marginBottom:2,marginTop:7};

function NI({onAdd,its}){const[f,s]=useState({id:"",nm:"",tp:"SVC",pt:"",st:"AFVENTER SCAN",ct:"CORE",ph:0,bg:[],dp:[],db:[],hc:"",nt:"",pin:false,ann:[]});
return<><div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6}}><label style={fl2}>ID *<input value={f.id} onChange={e=>s({...f,id:e.target.value.toUpperCase()})} placeholder="SVC-009" style={inp2}/></label><label style={fl2}>NAVN *<input value={f.nm} onChange={e=>s({...f,nm:e.target.value})} style={inp2}/></label><label style={fl2}>TYPE<SF v={f.tp} opts={TPS} onSave={v=>s({...f,tp:v})}/></label><label style={fl2}>STATUS<SF v={f.st} opts={STS} onSave={v=>s({...f,st:v})}/></label><label style={fl2}>PORT<input value={f.pt} onChange={e=>s({...f,pt:e.target.value})} style={inp2}/></label><label style={fl2}>KAT<SF v={f.ct} opts={CTS} onSave={v=>s({...f,ct:v})}/></label></div>
<label style={fl2}>HEALTH<input value={f.hc} onChange={e=>s({...f,hc:e.target.value})} style={inp2}/></label>
<label style={fl2}>NOTER<textarea value={f.nt} onChange={e=>s({...f,nt:e.target.value})} rows={2} style={{...inp2,resize:"vertical"}}/></label>
<label style={fl2}>BOG<input value={f.bg.join(",")} onChange={e=>s({...f,bg:e.target.value.split(",").map(x=>x.trim()).filter(Boolean)})} placeholder="A4,B5" style={inp2}/></label>
<div style={{display:"flex",gap:4,marginTop:12,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.id||!f.nm)return alert("ID+Navn");if(its.find(i=>i.id===f.id))return alert("ID eksisterer");onAdd(f)}}>OPRET</button></div></>}

function NE({onAdd,es}){const[f,s]=useState({id:`E-${String(es.length+1).padStart(3,"0")}`,sr:"",ds:"",sv:"MIDDEL",st:"ÅBEN",fx:""});
return<><label style={fl2}>KILDE<input value={f.sr} onChange={e=>s({...f,sr:e.target.value})} style={inp2}/></label><label style={fl2}>BESKRIVELSE *<input value={f.ds} onChange={e=>s({...f,ds:e.target.value})} style={inp2}/></label><label style={fl2}>ALV<SF v={f.sv} opts={["KRITISK","HØJ","MIDDEL","LAV"]} onSave={v=>s({...f,sv:v})}/></label><label style={fl2}>FIX<input value={f.fx} onChange={e=>s({...f,fx:e.target.value})} style={inp2}/></label>
<div style={{display:"flex",gap:4,marginTop:12,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.ds)return alert("Beskrivelse");onAdd(f)}}>OPRET</button></div></>}

function NL({onAdd,ls}){const[f,s]=useState({id:`L-${String(ls.length+1).padStart(3,"0")}`,a:"INFRA",t:"",o:""});
return<><label style={fl2}>OMRÅDE<SF v={f.a} opts={["INFRA","PROMPT","PROCES"]} onSave={v=>s({...f,a:v})}/></label><label style={fl2}>LEARNING *<input value={f.t} onChange={e=>s({...f,t:e.target.value})} style={inp2}/></label><label style={fl2}>→ODIN<input value={f.o} onChange={e=>s({...f,o:e.target.value})} placeholder="rules/..." style={inp2}/></label>
<div style={{display:"flex",gap:4,marginTop:12,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.t)return alert("Tekst");onAdd(f)}}>OPRET</button></div></>}

function NT({onAdd}){const[f,s]=useState({title:"",desc:"",s:"TODO"});
return<><label style={fl2}>TITEL *<input value={f.title} onChange={e=>s({...f,title:e.target.value})} style={inp2}/></label><label style={fl2}>BESKRIVELSE<textarea value={f.desc} onChange={e=>s({...f,desc:e.target.value})} rows={2} style={{...inp2,resize:"vertical"}}/></label><label style={fl2}>STATUS<SF v={f.s} opts={["TODO","I GANG","KOMPLET"]} onSave={v=>s({...f,s:v})}/></label>
<div style={{display:"flex",gap:4,marginTop:12,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.title)return alert("Titel");onAdd(f)}}>OPRET</button></div></>}
