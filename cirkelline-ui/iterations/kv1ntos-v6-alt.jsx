import { useState, useMemo, useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════
   KV1NTOS v6 · DEFINITIVE ADMIRAL OPERATIONS CENTER
   Separate projekter · Dyb navigation · Templates · Prompts
   Skills · Frameworks · Import/Export rutine · Git/VSCode
   ═══════════════════════════════════════════════════════════════ */

const ts=()=>new Date().toISOString().slice(0,16);
const INIT={
  phases:[{id:0,n:"DISCOVERY",s:"I GANG"},{id:1,n:"OPRYDNING",s:"VENTER"},{id:2,n:"FUNDAMENT",s:"VENTER"},{id:3,n:"OBSERVABILITY",s:"VENTER"},{id:4,n:"AI-MODELLER",s:"VENTER"},{id:5,n:"ODIN",s:"VENTER"},{id:6,n:"INTEGRATION",s:"VENTER"},{id:7,n:"PROJEKTER",s:"VENTER"}],
  // ─── SERVICES ───
  services:[
    {id:"SVC-001",nm:"Docker Engine",pt:"socket",st:"AFVENTER SCAN",hc:"systemctl status docker",bg:["A4","B5","C7"],dp:[],db:["SVC-002","SVC-003","SVC-004","SVC-005","SVC-006","SVC-007","SVC-008"],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-002",nm:"Prometheus",pt:"9090",st:"AFVENTER SCAN",hc:"curl localhost:9090/-/healthy",bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-003",nm:"Loki",pt:"3100",st:"AFVENTER SCAN",hc:"curl localhost:3100/ready",bg:["A7","C10"],dp:["SVC-001"],db:["SVC-004"],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-004",nm:"Grafana",pt:"3000",st:"AFVENTER SCAN",hc:"curl localhost:3000/api/health",bg:["A7","B7","C10"],dp:["SVC-001","SVC-002","SVC-003"],db:[],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-005",nm:"Tempo",pt:"3200",st:"AFVENTER SCAN",hc:"curl localhost:3200/ready",bg:["A7"],dp:["SVC-001"],db:["SVC-004"],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-006",nm:"Alertmanager",pt:"9093",st:"AFVENTER SCAN",hc:"curl localhost:9093/-/healthy",bg:["A7"],dp:["SVC-001","SVC-002"],db:[],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-007",nm:"n8n",pt:"5678",st:"AFVENTER SCAN",hc:"curl localhost:5678/healthz",bg:[],dp:["SVC-001"],db:[],nt:"",pin:false,ann:[],docs:[]},
    {id:"SVC-008",nm:"Ollama",pt:"11434",st:"AFVENTER SCAN",hc:"curl localhost:11434",bg:[],dp:[],db:[],nt:"",pin:false,ann:[],docs:[]},
  ],
  // ─── APIS ───
  apis:[
    {id:"API-001",nm:"Claude (privat)",st:"AFVENTER TEST",bg:["C9"],nt:"opus-4-6/sonnet-4-5/haiku-4-5|max3",pin:false,ann:[],docs:[]},
    {id:"API-002",nm:"Claude (firma)",st:"AFVENTER TEST",bg:["C9"],nt:"opus-4-6/sonnet-4-5/haiku-4-5|max3",pin:false,ann:[],docs:[]},
    {id:"API-003",nm:"Gemini",st:"AFVENTER TEST",bg:["C9"],nt:"Fleet Router|2.0-flash/pro",pin:false,ann:[],docs:[]},
  ],
  // ─── CONTAINERS ───
  containers:[
    {id:"CTR-001",nm:"kv1ntos-prometheus",pt:"9090",img:"prom/prometheus",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
    {id:"CTR-002",nm:"kv1ntos-loki",pt:"3100",img:"grafana/loki",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
    {id:"CTR-003",nm:"kv1ntos-tempo",pt:"3200",img:"grafana/tempo",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
    {id:"CTR-004",nm:"kv1ntos-grafana",pt:"3000",img:"grafana/grafana",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
    {id:"CTR-005",nm:"kv1ntos-alertmanager",pt:"9093",img:"prom/alertmanager",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
    {id:"CTR-006",nm:"kv1ntos-n8n",pt:"5678",img:"n8nio/n8n",st:"AFVENTER SCAN",bg:["A4"],nt:"",pin:false,ann:[],docs:[]},
  ],
  // ─── INTEGRATIONER ───
  integrations:[
    {id:"INT-001",nm:"AI Fleet Manager",pt:"9800",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-002",nm:"Family Orchestrator",pt:"9801",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-003",nm:"Evolved Swarm",pt:"9802",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-004",nm:"Cirkelline Evolved",pt:"9803",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-005",nm:"CKC Evolved",pt:"9804",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-006",nm:"Kommandør Evolved",pt:"9805",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-007",nm:"Cosmic Evolved",pt:"9806",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-008",nm:"Unified Brain",pt:"9807",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-009",nm:"Admiral Hybrid",pt:"9808",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-010",nm:"Prod Dashboard",pt:"9809",st:"AFVENTER SCAN",bg:["J2"],nt:"",ann:[],docs:[]},
    {id:"INT-011",nm:"Family Msg Bus",pt:"9010",st:"AFVENTER SCAN",bg:["J2","I4"],nt:"",ann:[],docs:[]},
  ],
  databases:[
    {id:"DB-001",nm:"PostgreSQL (Cirkelline)",pt:"5533",st:"AFVENTER SCAN",bg:["A5","C8"],nt:"",ann:[],docs:[]},
    {id:"DB-002",nm:"PostgreSQL (Cosmic)",pt:"5534",st:"AFVENTER SCAN",bg:["A5","C8"],nt:"",ann:[],docs:[]},
    {id:"DB-003",nm:"Redis",pt:"",st:"AFVENTER SCAN",bg:["C5"],nt:"",ann:[],docs:[]},
  ],
  // ─── PROJEKTER (SEPARATE) ───
  projects:{
    cirkelline:{nm:"Cirkelline System",pt:"7777",db:"PostgreSQL:5533",st:"AFVENTER SCAN",bg:["A2","B1","C1","D2"],desc:"4-platform familie system",git:"~/kv1ntos/cirkelline",vsc:"code ~/kv1ntos/cirkelline",items:[],notes:"",ann:[],docs:[],templates:[],prompts:[]},
    cosmic:{nm:"Cosmic Library",pt:"7778",db:"PostgreSQL:5534",st:"AFVENTER SCAN",bg:["A2","B2","C2","D3"],desc:"Videns-platform",git:"~/kv1ntos/cosmic-library",vsc:"code ~/kv1ntos/cosmic-library",items:[],notes:"",ann:[],docs:[],templates:[],prompts:[]},
    ckc:{nm:"CKC Gateway",pt:"7779",st:"AFVENTER SCAN",bg:["A2","B3","C3","D4"],desc:"Central gateway",git:"~/kv1ntos/ckc-gateway",vsc:"code ~/kv1ntos/ckc-gateway",items:[],notes:"",ann:[],docs:[],templates:[],prompts:[]},
    kommandor:{nm:"Kommandør Gateway",pt:"7800",st:"AFVENTER SCAN",bg:["A2","B4","C4","D5"],desc:"Kommandør system",git:"~/kv1ntos/kommandor",vsc:"code ~/kv1ntos/kommandor",items:[],notes:"",ann:[],docs:[],templates:[],prompts:[]},
    bornskaber:{nm:"BØRNESKABER",pt:"",st:"IKKE STARTET",bg:[],desc:"Genesis-sekvens: farver, lyde, tegninger. Kreativt udtryk for børn.",git:"~/kv1ntos/bornskaber",vsc:"code ~/kv1ntos/bornskaber",items:[],notes:"Ikke traditionel edtech. Kreativt udtryk.",ann:[],docs:[],templates:[],prompts:[]},
    threerealms:{nm:"Three Realms",pt:"",st:"IKKE STARTET",bg:[],desc:"GPS-baseret spil. 3 tidsperioder: 1825, nu, 2050.",git:"~/kv1ntos/three-realms",vsc:"code ~/kv1ntos/three-realms",items:[],notes:"Location-based. Augmented reality overlay.",ann:[],docs:[],templates:[],prompts:[]},
    gaming:{nm:"Gaming Platform",pt:"",st:"IKKE STARTET",bg:[],desc:"Steam-kvalitet. Brætspil + social. Invitation-only.",git:"~/kv1ntos/gaming-platform",vsc:"code ~/kv1ntos/gaming-platform",items:[],notes:"Board games med networking.",ann:[],docs:[],templates:[],prompts:[]},
  },
  // ─── AGENTER (SEPARATE) ───
  agents:{
    kommandor:{nm:"Kommandør Agents",count:21,st:"REGISTRERET",bg:["E3"],structure:"M(5)+S(5)+R(3)+A(4)+G(4)",items:[],notes:"",ann:[],docs:[]},
    elle:{nm:"ELLE Agents",count:122,st:"AFVENTER REG.",bg:["E1"],structure:"Health(30)+Train(25)+Mon(20)+Other(47)",items:[],notes:"Største agent-gruppe",ann:[],docs:[]},
    ckc:{nm:"CKC Agents",count:5,st:"AFVENTER REG.",bg:["E3"],structure:"",items:[],notes:"",ann:[],docs:[]},
    cosmic:{nm:"Cosmic Agents",count:9,st:"AFVENTER REG.",bg:["E4"],structure:"Research Team",items:[],notes:"",ann:[],docs:[]},
  },
  // ─── TEMPLATES ───
  templates:[
    {id:"T-001",nm:"Docker Compose Service",cat:"INFRA",content:"services:\\n  {name}:\\n    image: {image}\\n    ports:\\n      - '{port}:{port}'\\n    restart: unless-stopped\\n    healthcheck:\\n      test: ['CMD','curl','-f','http://localhost:{port}/health']\\n    logging:\\n      driver: loki",ann:[]},
    {id:"T-002",nm:"Agent Registration",cat:"AGENT",content:"# Agent: {name}\\nID: {id}\\nType: {type}\\nParent: {parent}\\nCapabilities: {caps}\\nStatus: REGISTERED\\nHealth: /healthz",ann:[]},
    {id:"T-003",nm:"API Rate Limit Config",cat:"API",content:"rate_limits:\\n  {model}:\\n    max_concurrent: 3\\n    max_per_minute: 50\\n    cooldown_seconds: 60\\n    fallback: queue",ann:[]},
    {id:"T-004",nm:"Scan Report",cat:"DISCOVERY",content:"# SCAN RAPPORT\\nDato: {date}\\nAdmiral: Elle\\n\\n## Fund\\n{findings}\\n\\n## Status\\n{status}\\n\\n## Næste skridt\\n{next}",ann:[]},
  ],
  // ─── PROMPTS ───
  prompts:[
    {id:"P-001",nm:"Discovery Scan",model:"Claude Opus",content:"Du er en infrastruktur-scanner. Gennemgå følgende output og identificér:\\n1. Kørende services med porte\\n2. Fejl eller advarsler\\n3. Ressourceforbrug\\n4. Manglende healthchecks\\n\\nOutput:\\n{input}\\n\\nSvar i struktureret format med ID, navn, status, port, og anbefalinger.",cat:"DISCOVERY"},
    {id:"P-002",nm:"Fejlanalyse",model:"Claude Opus",content:"Analysér denne fejl fra {source}:\\n\\n{error}\\n\\nGiv:\\n1. Root cause\\n2. Påvirkning\\n3. Fix (specifik kommando)\\n4. Forebyggelse",cat:"DIAGNOSTIK"},
    {id:"P-003",nm:"Kode Review",model:"Claude Opus",content:"Review denne kode for {project}:\\n\\n{code}\\n\\nTjek for:\\n- Sikkerhed (API-nøgler, injection)\\n- Fejlhåndtering\\n- Performance\\n- ODIN-regeloverholdelse\\n\\nGiv konkrete fixes, ikke generelle råd.",cat:"REVIEW"},
    {id:"P-004",nm:"Agent Design",model:"Claude Opus",content:"Design en agent til {system} med følgende krav:\\n\\nFormål: {purpose}\\nIntegration: {integrations}\\nInput/Output: {io}\\n\\nDefiner: capabilities, healthcheck, dependencies, rate-limits.",cat:"DESIGN"},
  ],
  // ─── FRAMEWORKS ───
  frameworks:[
    {id:"FW-001",nm:"ODIN Kommandokæde",desc:"Admiral→ODIN→HQ→Agent→Resultat. Hierarkisk styring af alle operationer.",rules:["Ingen agent handler alene","Alt logges","Fejl eskaleres opad"],docs:[]},
    {id:"FW-002",nm:"Discovery Protocol",desc:"Systematisk scanning: Find → Klassificér → Dokumentér → Verificér → Godkend",rules:["Scan FØRST","Antag INTET","Alt i filer"],docs:[]},
    {id:"FW-003",nm:"API Resource Management",desc:"Rate-limiting, kvota-styring, fallback-strategier for Claude/Gemini/Ollama",rules:["Max 3 samtidige","Kvota-tracking","Graceful degradation"],docs:[]},
  ],
  // ─── SKILLS ───
  skills:[
    {id:"SK-001",nm:"Docker Diagnostik",level:"AVANCERET",desc:"Fejlfinding i containerized environments",cmds:["docker logs {name} --since 1h","docker inspect {name}","docker stats --no-stream"],docs:[]},
    {id:"SK-002",nm:"Grafana Dashboard",level:"MELLEM",desc:"Oprettelse og vedligeholdelse af dashboards",cmds:["curl localhost:3000/api/dashboards/db","curl -X POST localhost:3000/api/dashboards/import"],docs:[]},
    {id:"SK-003",nm:"Ollama Model Management",level:"AVANCERET",desc:"Load/unload, VRAM management, multi-model",cmds:["nvidia-smi","ollama ps","ollama pull {model}","ollama rm {model}"],docs:[]},
    {id:"SK-004",nm:"Git Workflow",level:"BASIS",desc:"Branch, commit, merge strategi for KV1NTOS",cmds:["git status -s","git log --oneline -10","git diff --stat"],docs:[]},
  ],
  // ─── STATIC ───
  errors:[{id:"E-001",sr:"Grafana",ds:"Dashboard fejl",sv:"HØJ",st:"ÅBEN"},{id:"E-002",sr:"API",ds:"Kvote-udtømning",sv:"KRITISK",st:"ÅBEN"},{id:"E-003",sr:"Plugins",ds:"28/16 aktive",sv:"MIDDEL",st:"ÅBEN"}],
  learnings:[{id:"L-001",a:"INFRA",t:"API simultant→quota"},{id:"L-002",a:"INFRA",t:"Restart-policy nødvendig"},{id:"L-003",a:"INFRA",t:"Grafana URL match"},{id:"L-004",a:"INFRA",t:"VRAM frigives ikke auto"},{id:"L-005",a:"INFRA",t:"nvidia-smi FØR load"},{id:"L-010",a:"PROMPT",t:"Ud over basale nødvendigt"},{id:"L-011",a:"PROMPT",t:"XML-tags→bedre"},{id:"L-020",a:"PROCES",t:"Scan er BLOCKER"},{id:"L-021",a:"PROCES",t:"Alt i filer"}],
  rules:[{id:"R-01",r:"API-nøgler ALDRIG i Git",c:"SIK"},{id:"R-02",r:"Restart+healthcheck+Loki",c:"DOC"},{id:"R-03",r:"UFW firewall",c:"SIK"},{id:"R-05",r:"Max 3 Claude-kald",c:"API"},{id:"R-06",r:"Max 50 API totalt",c:"API"},{id:"R-08",r:"Ugentlig backup",c:"BAK"},{id:"R-11",r:"127.0.0.1 only",c:"NET"},{id:"R-13",r:"nvidia-smi FØR",c:"AI"}],
  bogforing:[{c:"A",n:"STATUS",f:10,l:8241},{c:"B",n:"COMMANDS",f:10,l:6671},{c:"C",n:"CONFIG",f:10,l:9850},{c:"D",n:"ARCH",f:10,l:16787},{c:"E",n:"AGENTS",f:4,l:5060},{c:"F",n:"HISTORY",f:10,l:707},{c:"G",n:"LAPTOP",f:5,l:1751},{c:"H",n:"FLEET",f:2,l:642},{c:"I",n:"OPS",f:8,l:5320},{c:"J",n:"META",f:2,l:6300}],
  cmds:[
    {id:"C01",n:"Dagligt tjek",cmd:"docker ps -a --format '{{.Names}}: {{.Status}}' && free -h && nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader"},
    {id:"C02",n:"Healthcheck",cmd:"for p in 9090 3100 3200 3000 5678 11434 9093; do curl -s --max-time 2 http://localhost:$p >/dev/null && echo \"$p:OK\" || echo \"$p:NEDE\"; done"},
    {id:"C03",n:"Komplet scan",cmd:"docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' && free -h && df -h / && nvidia-smi 2>/dev/null && ollama ps 2>/dev/null"},
    {id:"C04",n:"Porte",cmd:"ss -tlnp | grep -E ':(3000|3100|3200|5678|9090|9093|11434|7777|7778|7779|7800|9800)' | sort"},
    {id:"C05",n:"Git alle",cmd:"find ~ -maxdepth 3 -name '.git' -type d | while read g; do r=$(dirname \"$g\"); echo \"=== $(basename $r) ===\"; git -C $r status -s; done"},
  ],
  tasks:[],captures:[],files:[],chatPastes:[],
  log:[{ts:ts(),w:"SYS",m:"KV1NTOS v6 DEFINITIVE init"}],
};

const STS=["AFVENTER SCAN","I GANG","VENTER","KOMPLET","ÅBEN","AFVENTER TEST","IKKE STARTET","REGISTRERET","AFVENTER REG.","LUKKET"];

function useS(k,i){const[d,sD]=useState(()=>{try{const s=window._kv?.[k];return s||JSON.parse(JSON.stringify(i))}catch{return JSON.parse(JSON.stringify(i))}});const s=useCallback(fn=>{sD(p=>{const n=typeof fn==="function"?fn(p):fn;if(!window._kv)window._kv={};window._kv[k]=n;return n})},[k]);return[d,s]}

const CSS=`@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Serif&family=Outfit:wght@300;400;500;600;700;800&display=swap');
:root{--bg:#050507;--b2:#0a0a0f;--b3:#111118;--bd:#1c1c28;--g:#d4a054;--gd:#6b5a3a;--gn:#4ade80;--rd:#f87171;--bl:#60a5fa;--pr:#c084fc;--cy:#22d3ee;--yl:#eab308;--tx:#e8e4dc;--t2:#999;--t3:#555;--f:'Outfit',sans;--m:'DM Mono',mono;--s:'Instrument Serif',serif}
*{box-sizing:border-box;margin:0;padding:0}::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--gd);border-radius:2px}
@keyframes fu{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}@keyframes si{from{opacity:0;transform:translateX(16px)}to{opacity:1;transform:none}}
@keyframes glow{0%,100%{box-shadow:0 0 4px rgba(212,160,84,.08)}50%{box-shadow:0 0 12px rgba(212,160,84,.18)}}@keyframes pl{0%,100%{opacity:1}50%{opacity:.35}}
.b{background:var(--b3);border:1px solid var(--bd);color:var(--t2);padding:4px 8px;font:500 9px var(--m);cursor:pointer;border-radius:1px;transition:all .1s;letter-spacing:.3px}.b:hover{border-color:var(--g);color:var(--g)}.bp{background:rgba(212,160,84,.06);border-color:var(--gd);color:var(--g)}.bd{color:var(--rd)}.b:active{transform:scale(.97)}
.e{background:0;border:1px solid transparent;color:inherit;font:inherit;padding:1px 3px;width:100%;outline:0;border-radius:1px;transition:border .1s}.e:hover{border-color:var(--bd)}.e:focus{border-color:var(--g);background:var(--b3)}
.trm{background:#07070b;border:1px solid var(--bd);border-radius:2px;font:10px/1.5 var(--m);color:var(--gn);padding:8px;white-space:pre-wrap;word-break:break-all;overflow:auto;max-height:200px;cursor:pointer}
.cb{background:var(--b2);border:1px solid var(--bd);border-left:3px solid var(--pr);padding:8px 10px;margin:3px 0;border-radius:0 2px 2px 0;font:10px/1.5 var(--m);color:var(--tx);white-space:pre-wrap}.cb:hover{border-left-color:var(--g)}.cb .mt{font-size:8px;color:var(--t3);margin-bottom:3px}
.rl{color:var(--cy);cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;font-size:9px}.rl:hover{color:var(--g)}
.tst{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:var(--g);color:#050507;padding:5px 16px;font:600 10px var(--m);border-radius:2px;z-index:999;animation:fu .1s}
.grain{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.02;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.sec-hd{display:flex;justify-content:space-between;align-items:center;padding:4px 0 6px;border-bottom:1px solid var(--bd);margin:16px 0 8px}
.sec-hd h2{font:italic 400 17px/1 var(--s);color:var(--tx)}
.sec-hd .id{font:500 9px var(--m);color:var(--g);letter-spacing:2px;margin-right:6px}
.stat{background:var(--b2);border:1px solid var(--bd);padding:8px 10px;border-radius:1px}.stat .v{font:700 18px var(--m);line-height:1}.stat .l{font-size:8px;color:var(--t2);margin-top:1px}
.dz{border:2px dashed var(--gd);padding:16px;text-align:center;border-radius:2px;cursor:pointer;font:10px var(--m);color:var(--t2)}.dz:hover{border-color:var(--g);background:rgba(212,160,84,.02)}
.project-card{background:var(--b2);border:1px solid var(--bd);padding:12px 14px;border-radius:2px;cursor:pointer;transition:all .12s}.project-card:hover{border-color:var(--gd);transform:translateY(-1px)}
.tmpl{background:var(--b2);border:1px solid var(--bd);padding:10px 12px;border-radius:2px;margin-bottom:6px}
.tmpl:hover{border-color:var(--gd)}`;

const SB=({s,oc})=>{const c={"AFVENTER SCAN":"var(--g)","I GANG":"var(--gn)","VENTER":"var(--bl)","KOMPLET":"var(--gn)","ÅBEN":"var(--rd)","AFVENTER TEST":"var(--g)","IKKE STARTET":"var(--t3)","KRITISK":"#f44","HØJ":"var(--yl)","MIDDEL":"var(--yl)","REGISTRERET":"var(--gn)","AFVENTER REG.":"var(--g)","LUKKET":"#666"}[s]||"#666";
return<span onClick={oc} style={{padding:"1px 5px",fontSize:8,fontFamily:"var(--m)",color:c,border:`1px solid ${c}33`,borderRadius:1,cursor:oc?"pointer":"default"}}>{s}</span>};

const EF=({v="",os,mn,ml})=>{const[ed,sE]=useState(false);const[val,sV]=useState(v);const r=useRef();
useEffect(()=>{sV(v)},[v]);useEffect(()=>{if(ed&&r.current)r.current.focus()},[ed]);
if(!ed)return<span onClick={()=>sE(true)} style={{cursor:"pointer",fontFamily:mn?"var(--m)":"inherit",borderBottom:"1px dashed transparent"}} onMouseEnter={e=>e.currentTarget.style.borderBottomColor="var(--gd)"} onMouseLeave={e=>e.currentTarget.style.borderBottomColor="transparent"}>{v||<i style={{color:"var(--t3)"}}>—</i>}</span>;
const sv=()=>{sE(false);if(val!==v)os(val)};
if(ml)return<textarea ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Escape"){sV(v);sE(false)}}} rows={3} style={{fontFamily:"var(--m)",fontSize:10,resize:"vertical"}}/>;
return<input ref={r} className="e" value={val} onChange={e=>sV(e.target.value)} onBlur={sv} onKeyDown={e=>{if(e.key==="Enter")sv();if(e.key==="Escape"){sV(v);sE(false)}}} style={{fontFamily:mn?"var(--m)":"var(--f)",fontSize:10}}/>};

const SF=({v,o,os})=><select value={v} onChange={e=>os(e.target.value)} style={{background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",padding:"1px 3px",fontSize:9,fontFamily:"var(--m)",borderRadius:1,cursor:"pointer"}}>{o.map(x=><option key={x}>{x}</option>)}</select>;

const Sec=({id,t,cnt,act,children})=><><div className="sec-hd"><div style={{display:"flex",alignItems:"baseline"}}><span className="id">{id}</span><h2>{t}</h2>{cnt!=null&&<span style={{fontFamily:"var(--m)",fontSize:8,color:"var(--t3)",marginLeft:6}}>({cnt})</span>}</div>{act}</div>{children}</>;

// ─── MAIN APP ───
export default function App(){
  const[D,sD]=useS("kv6",INIT);
  const[sec,sSec]=useState("overview");const[sub,sSub]=useState(null);const[q,sQ]=useState("");const[sel,sSel]=useState(null);const[mod,sMod]=useState(null);const[toast,sT]=useState("");const[cap,sCap]=useState(false);
  const sR=useRef();const cR=useRef();const fR=useRef();

  const lg=m=>sD(d=>({...d,log:[{ts:ts(),w:"ADM",m},...(d.log||[]).slice(0,299)]}));
  const fl=m=>{sT(m);setTimeout(()=>sT(""),1400)};
  const cp=t=>{navigator.clipboard?.writeText(t);fl("Kopieret")};
  const exportJ=()=>{const b=new Blob([JSON.stringify(D,null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=`kv1ntos-${ts().replace(/:/g,"")}.json`;a.click();fl("Export OK")};
  const aCap=c=>{sD(d=>({...d,captures:[{ts:ts(),text:c},...(d.captures||[])]}));lg("CAPTURE");fl("Gemt")};
  const aPaste=p=>{sD(d=>({...d,chatPastes:[{ts:ts(),...p},...(d.chatPastes||[])]}));lg(`PASTE:${p.source}`)};
  const hFiles=fs=>Array.from(fs).forEach(f=>{const r=new FileReader();r.onload=e=>{sD(d=>({...d,files:[...(d.files||[]),{name:f.name,size:f.size,dt:ts(),content:e.target.result}]}));lg(`FIL:${f.name}`)};r.readAsText(f)});

  useEffect(()=>{const h=e=>{const m=e.metaKey||e.ctrlKey;if(m&&e.key==="k"){e.preventDefault();sCap(p=>!p);setTimeout(()=>cR.current?.focus(),50)}if(m&&e.key==="n"){e.preventDefault();sMod("item")}if(m&&e.key==="f"){e.preventDefault();sR.current?.focus()}if(m&&e.key==="e"){e.preventDefault();exportJ()}if(m&&e.key==="p"){e.preventDefault();sMod("paste")}if(e.key==="Escape"){sSel(null);sMod(null);sCap(false);sSub(null)}};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[]);

  // Flatten all searchable items
  const allItems=useMemo(()=>[
    ...(D.services||[]).map(i=>({...i,_tp:"SVC"})),
    ...(D.apis||[]).map(i=>({...i,_tp:"API"})),
    ...(D.containers||[]).map(i=>({...i,_tp:"CTR"})),
    ...(D.integrations||[]).map(i=>({...i,_tp:"INT"})),
    ...(D.databases||[]).map(i=>({...i,_tp:"DB"})),
    ...(D.templates||[]).map(i=>({...i,_tp:"TMPL"})),
    ...(D.prompts||[]).map(i=>({...i,_tp:"PROMPT"})),
    ...(D.skills||[]).map(i=>({...i,_tp:"SKILL"})),
  ],[D]);

  const filtered=useMemo(()=>{if(!q.trim())return[];const ql=q.toLowerCase();return allItems.filter(i=>{const h=[i.id,i.nm,i._tp,i.pt||"",i.nt||"",...(i.bg||[])].join(" ").toLowerCase();if(h.includes(ql))return true;if(/^\d+$/.test(ql)&&(i.pt||"")=== ql)return true;if(/^[A-J]\d*$/i.test(ql)&&(i.bg||[]).some(b=>b.toLowerCase().startsWith(ql)))return true;if(ql.length>=3){const nm=(i.nm||"").toLowerCase();let qi=0;for(let ci=0;ci<nm.length&&qi<ql.length;ci++)if(nm[ci]===ql[qi])qi++;return qi===ql.length}return false})},[allItems,q]);

  const st={svc:(D.services||[]).length,api:(D.apis||[]).length,ctr:(D.containers||[]).length,int:(D.integrations||[]).length,db:(D.databases||[]).length,proj:Object.keys(D.projects||{}).length,agt:Object.values(D.agents||{}).reduce((s,a)=>s+a.count,0),err:(D.errors||[]).filter(e=>e.st==="ÅBEN").length,tmpl:(D.templates||[]).length,prm:(D.prompts||[]).length,sk:(D.skills||[]).length,fw:(D.frameworks||[]).length};
  const td={padding:"4px 6px",fontSize:9,borderBottom:"1px solid rgba(28,28,40,.15)"};

  // Item table for any collection
  const Tbl=({rows,cols})=><table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:9,fontFamily:"var(--m)",marginBottom:8}}><thead><tr>{cols.map((c,i)=><th key={i} style={{textAlign:"left",padding:"3px 6px",borderBottom:"1px solid var(--bd)",color:"var(--t3)",fontSize:7,fontWeight:600,letterSpacing:1,background:"var(--b2)"}}>{c}</th>)}</tr></thead><tbody>{rows}</tbody></table>;

  // NAV
  const NAV=[
    {g:"SYSTEM",items:[{id:"overview",l:"◈ OVERBLIK"},{id:"services",l:"● SERVICES"},{id:"apis",l:"⟡ API'ER"},{id:"containers",l:"▣ CONTAINERE"},{id:"integrations",l:"⊞ INT."},{id:"databases",l:"▥ DB"}]},
    {g:"PROJEKTER",items:[{id:"p-cirkelline",l:"◆ Cirkelline"},{id:"p-cosmic",l:"◆ Cosmic"},{id:"p-ckc",l:"◆ CKC"},{id:"p-kommandor",l:"◆ Kommandør"},{id:"p-bornskaber",l:"◇ BØRNESKABER"},{id:"p-threerealms",l:"◇ Three Realms"},{id:"p-gaming",l:"◇ Gaming"}]},
    {g:"AGENTER",items:[{id:"a-kommandor",l:"◎ Kommandør(21)"},{id:"a-elle",l:"◎ ELLE(122)"},{id:"a-ckc",l:"◎ CKC(5)"},{id:"a-cosmic",l:"◎ Cosmic(9)"}]},
    {g:"VÆRKTØJER",items:[{id:"templates",l:"📐 TEMPLATES"},{id:"prompts",l:"💬 PROMPTS"},{id:"frameworks",l:"🏗 FRAMEWORKS"},{id:"skills",l:"🎯 SKILLS"}]},
    {g:"DRIFT",items:[{id:"paste",l:"📋 CHAT PASTE"},{id:"capture",l:"⌨ TERMINAL"},{id:"tasks",l:"☐ OPGAVER"},{id:"commands",l:"$ CMDS"},{id:"files",l:"📁 FILER"},{id:"bogforing",l:"A-J BOG."}]},
    {g:"REFERENCE",items:[{id:"errors",l:"⚠ FEJL"},{id:"learnings",l:"◆ LEARN"},{id:"rules",l:"⛨ ODIN"},{id:"log",l:"✎ LOG"}]},
  ];

  // ─── PROJECT DETAIL VIEW ───
  const ProjectView=({pk})=>{const p=D.projects?.[pk];if(!p)return null;
    const upP=(f,v)=>sD(d=>({...d,projects:{...d.projects,[pk]:{...d.projects[pk],[f]:v}}}));
    return<>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:12}}>
        <div><h1 style={{fontFamily:"var(--s)",fontSize:22,fontStyle:"italic",color:"var(--tx)"}}>{p.nm}</h1><p style={{fontSize:9,color:"var(--t2)",marginTop:2}}>{p.desc}</p></div>
        <SB s={p.st} oc={()=>{const ci=STS.indexOf(p.st);upP("st",STS[(ci+1)%STS.length])}}/>
      </div>
      {/* Quick actions */}
      <div style={{display:"flex",gap:4,marginBottom:12,flexWrap:"wrap"}}>
        {p.pt&&<div className="stat" style={{minWidth:70}}><div className="v" style={{color:"var(--cy)"}}>{p.pt}</div><div className="l">PORT</div></div>}
        {p.db&&<div className="stat" style={{minWidth:90}}><div className="v" style={{color:"var(--pr)",fontSize:11}}>{p.db}</div><div className="l">DATABASE</div></div>}
        {(p.bg||[]).map((b,i)=><span key={i} className="rl" style={{padding:"4px 6px",background:"var(--b2)",border:"1px solid var(--bd)"}}>{b}</span>)}
      </div>
      {/* Git/VSCode */}
      <div style={{display:"flex",gap:4,marginBottom:12}}>
        <button className="b" onClick={()=>cp(`cd ${p.git} && git status`)}>📂 Git Status</button>
        <button className="b" onClick={()=>cp(`cd ${p.git} && git log --oneline -10`)}>📜 Git Log</button>
        <button className="b" onClick={()=>cp(p.vsc)}>💻 VSCode</button>
        <button className="b" onClick={()=>cp(`cd ${p.git}`)}>📁 cd</button>
        <button className="b bp" onClick={()=>sMod("paste")}>💬 Paste</button>
      </div>
      {/* Notes */}
      <Sec id="NOTER" t="Noter"><div style={{marginBottom:8}}><EF v={p.notes} ml os={v=>{upP("notes",v);lg(`${pk}.notes`)}}/></div></Sec>
      {/* Annotations */}
      <Sec id="ANN" t="Annotationer" cnt={(p.ann||[]).length}>
        <div style={{display:"flex",gap:3,marginBottom:6}}><input placeholder="Tilføj annotation..." style={{flex:1,padding:"4px 6px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:9,fontFamily:"var(--m)",outline:0}} onKeyDown={e=>{if(e.key==="Enter"&&e.target.value.trim()){upP("ann",[{ts:ts(),t:e.target.value},...(p.ann||[])]);e.target.value="";lg(`${pk}.ann`)}}}/><button className="b" style={{fontSize:7}} onClick={()=>{/* handled by enter */}}>+</button></div>
        {(p.ann||[]).map((a,i)=><div key={i} style={{fontSize:8,color:"var(--t2)",padding:"2px 0",borderBottom:"1px solid rgba(28,28,40,.1)"}}><span style={{color:"var(--t3)",fontFamily:"var(--m)",fontSize:7,marginRight:3}}>{a.ts}</span>{a.t}</div>)}
      </Sec>
      {/* Docs */}
      <Sec id="DOC" t="Dokumenter" cnt={(p.docs||[]).length}>
        {(p.docs||[]).map((d,i)=><div key={i} className="cb"><div className="mt">{d.ts} · {d.title}</div>{d.text?.slice(0,200)}</div>)}
      </Sec>
      {/* Templates for this project */}
      <Sec id="TMPL" t="Projekt Templates" cnt={(p.templates||[]).length} act={<button className="b bp" onClick={()=>{const nm=prompt("Template navn:");if(nm){upP("templates",[...(p.templates||[]),{nm,content:"",ts:ts()}]);lg(`${pk}.tmpl:${nm}`)}}}  >+</button>}>
        {(p.templates||[]).map((t,i)=><div key={i} className="tmpl"><div style={{fontSize:10,fontWeight:600,marginBottom:2}}>{t.nm}</div><EF v={t.content} ml mn os={v=>{const tl=[...(p.templates||[])];tl[i]={...tl[i],content:v};upP("templates",tl)}}/></div>)}
      </Sec>
      {/* Prompts for this project */}
      <Sec id="PRM" t="Projekt Prompts" cnt={(p.prompts||[]).length} act={<button className="b bp" onClick={()=>{const nm=prompt("Prompt navn:");if(nm){upP("prompts",[...(p.prompts||[]),{nm,content:"",ts:ts()}]);lg(`${pk}.prompt:${nm}`)}}}  >+</button>}>
        {(p.prompts||[]).map((pr,i)=><div key={i} className="tmpl"><div style={{display:"flex",justifyContent:"space-between"}}><span style={{fontSize:10,fontWeight:600}}>{pr.nm}</span><button className="b" style={{fontSize:7}} onClick={()=>cp(pr.content)}>KOPIÉR</button></div><EF v={pr.content} ml mn os={v=>{const pl=[...(p.prompts||[])];pl[i]={...pl[i],content:v};upP("prompts",pl)}}/></div>)}
      </Sec>
    </>};

  // ─── AGENT DETAIL VIEW ───
  const AgentView=({ak})=>{const a=D.agents?.[ak];if(!a)return null;
    const upA=(f,v)=>sD(d=>({...d,agents:{...d.agents,[ak]:{...d.agents[ak],[f]:v}}}));
    return<>
      <h1 style={{fontFamily:"var(--s)",fontSize:22,fontStyle:"italic"}}>{a.nm}</h1>
      <div style={{display:"flex",gap:6,margin:"8px 0 12px"}}>
        <div className="stat"><div className="v" style={{color:"var(--cy)"}}>{a.count}</div><div className="l">AGENTER</div></div>
        <div className="stat"><div className="v" style={{fontSize:10}}><SB s={a.st}/></div><div className="l">STATUS</div></div>
        {a.structure&&<div className="stat"><div className="v" style={{fontSize:10,color:"var(--pr)"}}>{a.structure}</div><div className="l">STRUKTUR</div></div>}
      </div>
      <Sec id="NOTER" t="Noter"><EF v={a.notes} ml os={v=>{upA("notes",v);lg(`${ak}.notes`)}}/></Sec>
      <Sec id="ANN" t="Annotationer" cnt={(a.ann||[]).length}>
        <div style={{display:"flex",gap:3,marginBottom:4}}><input placeholder="Tilføj..." style={{flex:1,padding:"4px 6px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:9,fontFamily:"var(--m)",outline:0}} onKeyDown={e=>{if(e.key==="Enter"&&e.target.value.trim()){upA("ann",[{ts:ts(),t:e.target.value},...(a.ann||[])]);e.target.value=""}}}/></div>
        {(a.ann||[]).map((an,i)=><div key={i} style={{fontSize:8,color:"var(--t2)",padding:"2px 0"}}><span style={{color:"var(--t3)",fontSize:7,marginRight:3}}>{an.ts}</span>{an.t}</div>)}
      </Sec>
      <Sec id="DOC" t="Dokumenter" cnt={(a.docs||[]).length}>
        {(a.docs||[]).map((d,i)=><div key={i} className="cb"><div className="mt">{d.ts} · {d.title}</div>{d.text?.slice(0,200)}</div>)}
      </Sec>
    </>};

  return<>
    <style>{CSS}</style>
    <div className="grain"/>
    <div style={{display:"flex",minHeight:"100vh",background:"var(--bg)",color:"var(--tx)",fontFamily:"var(--f)",position:"relative",zIndex:2}}>
      {/* SIDEBAR */}
      <nav style={{width:155,borderRight:"1px solid var(--bd)",position:"fixed",top:0,left:0,height:"100vh",overflowY:"auto",background:"rgba(5,5,7,.97)",zIndex:50,display:"flex",flexDirection:"column"}}>
        <div style={{padding:"8px 10px 6px",borderBottom:"1px solid var(--bd)"}}>
          <div style={{fontFamily:"var(--s)",fontSize:16,color:"var(--g)",fontStyle:"italic"}}>KV1NTOS</div>
          <div style={{fontSize:7,color:"var(--t3)",fontFamily:"var(--m)"}}>OPERATIONS v6 DEFINITIVE</div>
          <div style={{marginTop:2,display:"flex",gap:3,alignItems:"center"}}><span style={{width:4,height:4,borderRadius:"50%",background:"var(--gn)",animation:"pl 2s infinite"}}/><span style={{fontSize:7,color:"var(--t2)",fontFamily:"var(--m)"}}>F0 DISCOVERY</span></div>
        </div>
        {/* Import/Export RUTINE — altid synlig */}
        <div style={{padding:"4px 10px",borderBottom:"1px solid var(--bd)",display:"flex",gap:2}}>
          <button className="b bp" style={{flex:1,fontSize:7,padding:"3px"}} onClick={exportJ}>↓ EXPORT</button>
          <label className="b" style={{flex:1,fontSize:7,padding:"3px",cursor:"pointer",textAlign:"center"}}>↑ IMPORT<input type="file" accept=".json" style={{display:"none"}} onChange={e=>{if(e.target.files[0]){const r=new FileReader();r.onload=ev=>{try{sD(JSON.parse(ev.target.result));fl("Import OK")}catch{alert("Ugyldig JSON")}};r.readAsText(e.target.files[0])}}}/></label>
        </div>
        <div style={{flex:1,overflowY:"auto"}}>
          {NAV.map(g=><div key={g.g}>
            <div style={{padding:"5px 10px 2px",fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",letterSpacing:1.5,fontWeight:600}}>{g.g}</div>
            {g.items.map(n=><button key={n.id} onClick={()=>{sSec(n.id);sSub(null);sSel(null);sQ("")}} style={{display:"block",width:"100%",padding:"3px 10px",background:sec===n.id?"rgba(212,160,84,.04)":"transparent",border:"none",borderLeft:sec===n.id?"2px solid var(--g)":"2px solid transparent",color:sec===n.id?"var(--tx)":"var(--t3)",cursor:"pointer",fontSize:8,fontFamily:"var(--m)",textAlign:"left",transition:"all .06s"}} onMouseEnter={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t2)"}} onMouseLeave={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--t3)"}}>{n.l}</button>)}
          </div>)}
        </div>
        <div style={{padding:"4px 10px",borderTop:"1px solid var(--bd)",fontSize:7,fontFamily:"var(--m)",color:"var(--t3)",textAlign:"center"}}>⌘K cap · ⌘P paste · ⌘N ny · ⌘E exp</div>
      </nav>

      {/* MAIN */}
      <main style={{flex:1,marginLeft:155,padding:"8px 18px 40px",maxWidth:860,overflowY:"auto"}}>
        {/* SEARCH + TOP BAR */}
        <div style={{display:"flex",gap:3,marginBottom:10}}>
          <input ref={sR} value={q} onChange={e=>sQ(e.target.value)} placeholder="Søg: navn, ID, port, A7, fuzzy..." style={{flex:1,padding:"5px 8px",background:"var(--b2)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:9,fontFamily:"var(--m)",outline:0,borderRadius:1}}/>
          <button className="b bp" onClick={()=>sMod("paste")} title="⌘P">💬</button>
          <button className="b" onClick={()=>{sCap(p=>!p);setTimeout(()=>cR.current?.focus(),50)}} title="⌘K">⌨</button>
        </div>
        {/* CAPTURE */}
        {cap&&<div style={{marginBottom:10,background:"var(--b2)",border:"1px solid var(--gd)",borderRadius:2,padding:8,animation:"fu .1s"}}>
          <textarea ref={cR} placeholder="Paste terminal output..." style={{width:"100%",minHeight:40,background:"#07070b",border:"1px solid var(--bd)",color:"var(--gn)",fontFamily:"var(--m)",fontSize:9,padding:6,borderRadius:1,resize:"vertical",outline:0}} onKeyDown={e=>{if((e.metaKey||e.ctrlKey)&&e.key==="Enter"&&cR.current.value.trim()){aCap(cR.current.value);cR.current.value=""}}}/>
          <div style={{display:"flex",justifyContent:"flex-end",marginTop:2}}><button className="b bp" style={{fontSize:7}} onClick={()=>{if(cR.current?.value.trim()){aCap(cR.current.value);cR.current.value=""}}}>GEM (⌘Enter)</button></div>
        </div>}

        {/* SEARCH RESULTS */}
        {q.trim()&&<Sec id="SØG" t={`"${q}"`} cnt={filtered.length}><Tbl cols={["ID","NAVN","TYPE","PORT","STATUS"]} rows={filtered.map((r,i)=><tr key={i} style={{animation:`fu .15s ${i*10}ms both`,cursor:"pointer"}} onClick={()=>fl(r.id)}><td style={{...td,color:"var(--g)"}}>{r.id}</td><td style={td}>{r.nm}</td><td style={{...td,color:"var(--t2)"}}>{r._tp}</td><td style={{...td,color:"var(--cy)"}}>{r.pt||"—"}</td><td style={td}><SB s={r.st}/></td></tr>)}/></Sec>}

        {/* ═══ OVERVIEW ═══ */}
        {sec==="overview"&&!q.trim()&&<>
          <h1 style={{fontFamily:"var(--s)",fontSize:24,fontStyle:"italic",animation:"fu .2s"}}>KV1NTOS Operations</h1>
          <p style={{fontSize:9,color:"var(--t2)",marginBottom:12,fontFamily:"var(--m)"}}>{st.svc} services · {st.proj} projekter · {st.agt} agenter · {st.err} fejl · {st.tmpl} templates · {st.prm} prompts</p>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(85px,1fr))",gap:3,marginBottom:14}}>
            {[{l:"SERVICES",v:st.svc},{l:"API'ER",v:st.api},{l:"CONTAINERE",v:st.ctr},{l:"INT.",v:st.int,c:"var(--bl)"},{l:"PROJEKTER",v:st.proj,c:"var(--pr)"},{l:"AGENTER",v:st.agt,c:"var(--cy)"},{l:"FEJL",v:st.err,c:"var(--rd)"},{l:"TEMPLATES",v:st.tmpl,c:"var(--yl)"},{l:"PROMPTS",v:st.prm,c:"var(--gn)"},{l:"SKILLS",v:st.sk},{l:"FRAMEWORKS",v:st.fw}].map((s,i)=>
              <div key={i} className="stat" style={{animation:`fu .2s ${i*15}ms both`}}><div className="v" style={{color:s.c||"var(--g)"}}>{s.v}</div><div className="l">{s.l}</div></div>)}
          </div>
          {/* FASER */}
          <div style={{display:"flex",gap:2,marginBottom:14}}>{D.phases.map(p=><div key={p.id} onClick={()=>{const nx=p.s==="VENTER"?"I GANG":p.s==="I GANG"?"KOMPLET":"VENTER";sD(d=>({...d,phases:d.phases.map(x=>x.id===p.id?{...x,s:nx}:x)}))}} style={{flex:1,padding:"5px 2px",background:p.s==="I GANG"?"rgba(212,160,84,.03)":"var(--b2)",border:`1px solid ${p.s==="I GANG"?"var(--gd)":p.s==="KOMPLET"?"#1a4a2a":"var(--bd)"}`,textAlign:"center",cursor:"pointer",borderRadius:1,position:"relative"}}>
            {p.s==="I GANG"&&<div style={{position:"absolute",top:0,left:0,right:0,height:2,background:"var(--g)",animation:"glow 2s infinite"}}/>}
            <div style={{fontFamily:"var(--m)",fontSize:11,fontWeight:700,color:p.s==="I GANG"?"var(--g)":p.s==="KOMPLET"?"var(--gn)":"var(--t3)"}}>{p.id}</div>
            <div style={{fontSize:6,color:"var(--t3)",fontFamily:"var(--m)"}}>{p.n}</div></div>)}</div>
          {/* OPSUMMERING */}
          <Sec id="OPSM" t="Opsummering">
            <div style={{fontSize:10,color:"var(--t2)",lineHeight:1.6}}>
              <b style={{color:"var(--g)"}}>Fase 0 DISCOVERY</b> er aktiv. {st.svc} services registreret, afventer scan. {st.proj} projekter defineret — heraf 4 platforme (Cirkelline, Cosmic, CKC, Kommandør) og 3 nye (BØRNESKABER, Three Realms, Gaming). {st.agt} agenter fordelt på 4 grupper. {st.err} åbne fejl kræver opmærksomhed. {st.tmpl} templates, {st.prm} prompts, {st.sk} skills og {st.fw} frameworks klar til brug.
            </div>
          </Sec>
        </>}

        {/* ═══ SERVICES ═══ */}
        {sec==="services"&&!q.trim()&&<Sec id="SVC" t="Services" cnt={st.svc}><Tbl cols={["ID","NAVN","PORT","STATUS","HEALTH","BOG"]} rows={(D.services||[]).map((s,i)=><tr key={s.id} style={{animation:`fu .15s ${i*10}ms both`}}><td style={{...td,color:"var(--g)"}}>{s.id}</td><td style={td}><EF v={s.nm} os={v=>sD(d=>({...d,services:d.services.map(x=>x.id===s.id?{...x,nm:v}:x)}))}/></td><td style={{...td,color:"var(--cy)"}}>{s.pt}</td><td style={td}><SB s={s.st} oc={()=>{const ci=STS.indexOf(s.st);sD(d=>({...d,services:d.services.map(x=>x.id===s.id?{...x,st:STS[(ci+1)%STS.length]}:x)}))}}/></td><td style={td}>{s.hc&&<span className="trm" style={{padding:"1px 4px",maxHeight:20,fontSize:8,cursor:"pointer"}} onClick={()=>cp(s.hc)}>{s.hc.slice(0,30)}</span>}</td><td style={{...td,fontSize:7}}>{(s.bg||[]).join(",")}</td></tr>)}/></Sec>}

        {/* ═══ APIS ═══ */}
        {sec==="apis"&&!q.trim()&&<Sec id="API" t="API'er" cnt={st.api}><Tbl cols={["ID","NAVN","STATUS","NOTER"]} rows={(D.apis||[]).map((a,i)=><tr key={a.id} style={{animation:`fu .15s ${i*10}ms both`}}><td style={{...td,color:"var(--g)"}}>{a.id}</td><td style={td}>{a.nm}</td><td style={td}><SB s={a.st}/></td><td style={{...td,color:"var(--t2)",fontSize:8}}>{a.nt}</td></tr>)}/></Sec>}

        {/* ═══ CONTAINERS ═══ */}
        {sec==="containers"&&!q.trim()&&<Sec id="CTR" t="Containere" cnt={st.ctr}><Tbl cols={["ID","NAVN","PORT","IMAGE","STATUS"]} rows={(D.containers||[]).map((c,i)=><tr key={c.id} style={{animation:`fu .15s ${i*10}ms both`}}><td style={{...td,color:"var(--g)"}}>{c.id}</td><td style={td}>{c.nm}</td><td style={{...td,color:"var(--cy)"}}>{c.pt}</td><td style={{...td,color:"var(--pr)",fontSize:8}}>{c.img}</td><td style={td}><SB s={c.st}/></td></tr>)}/></Sec>}

        {sec==="integrations"&&!q.trim()&&<Sec id="INT" t="Integrationer" cnt={st.int}><Tbl cols={["ID","NAVN","PORT","STATUS"]} rows={(D.integrations||[]).map((x,i)=><tr key={x.id} style={{animation:`fu .15s ${i*10}ms both`}}><td style={{...td,color:"var(--g)"}}>{x.id}</td><td style={td}>{x.nm}</td><td style={{...td,color:"var(--cy)"}}>{x.pt}</td><td style={td}><SB s={x.st}/></td></tr>)}/></Sec>}

        {sec==="databases"&&!q.trim()&&<Sec id="DB" t="Databaser" cnt={st.db}><Tbl cols={["ID","NAVN","PORT","STATUS"]} rows={(D.databases||[]).map((x,i)=><tr key={x.id} style={{animation:`fu .15s ${i*10}ms both`}}><td style={{...td,color:"var(--g)"}}>{x.id}</td><td style={td}>{x.nm}</td><td style={{...td,color:"var(--cy)"}}>{x.pt||"—"}</td><td style={td}><SB s={x.st}/></td></tr>)}/></Sec>}

        {/* ═══ PROJEKTER (INDIVIDUELLE) ═══ */}
        {sec.startsWith("p-")&&!q.trim()&&<ProjectView pk={sec.slice(2)}/>}

        {/* ═══ AGENTER (INDIVIDUELLE) ═══ */}
        {sec.startsWith("a-")&&!q.trim()&&<AgentView ak={sec.slice(2)}/>}

        {/* ═══ TEMPLATES ═══ */}
        {sec==="templates"&&!q.trim()&&<Sec id="TMPL" t="Templates" cnt={st.tmpl}>
          {(D.templates||[]).map((t,i)=><div key={i} className="tmpl" style={{animation:`fu .15s ${i*15}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><div><span style={{color:"var(--g)",fontFamily:"var(--m)",fontSize:8}}>{t.id}</span> <span style={{fontSize:11,fontWeight:600}}>{t.nm}</span> <span style={{fontSize:7,color:"var(--t3)"}}>{t.cat}</span></div><button className="b" style={{fontSize:7}} onClick={()=>cp(t.content)}>KOPIÉR</button></div>
            <pre className="trm" style={{maxHeight:80}}>{t.content}</pre>
          </div>)}
        </Sec>}

        {/* ═══ PROMPTS ═══ */}
        {sec==="prompts"&&!q.trim()&&<Sec id="PRM" t="Prompts" cnt={st.prm}>
          {(D.prompts||[]).map((p,i)=><div key={i} className="tmpl" style={{animation:`fu .15s ${i*15}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><div><span style={{color:"var(--g)",fontFamily:"var(--m)",fontSize:8}}>{p.id}</span> <span style={{fontSize:11,fontWeight:600}}>{p.nm}</span> <span style={{fontSize:7,color:"var(--pr)"}}>{p.model}</span> <span style={{fontSize:7,color:"var(--t3)"}}>{p.cat}</span></div><button className="b" style={{fontSize:7}} onClick={()=>cp(p.content)}>KOPIÉR</button></div>
            <pre className="trm" style={{maxHeight:100}}>{p.content}</pre>
          </div>)}
        </Sec>}

        {/* ═══ FRAMEWORKS ═══ */}
        {sec==="frameworks"&&!q.trim()&&<Sec id="FW" t="Frameworks" cnt={st.fw}>
          {(D.frameworks||[]).map((f,i)=><div key={i} className="tmpl" style={{animation:`fu .15s ${i*15}ms both`}}>
            <div style={{fontSize:12,fontWeight:600,marginBottom:3}}>{f.nm}</div>
            <div style={{fontSize:9,color:"var(--t2)",marginBottom:4}}>{f.desc}</div>
            {(f.rules||[]).map((r,j)=><div key={j} style={{fontSize:9,color:"var(--rd)",padding:"1px 0"}}>• {r}</div>)}
          </div>)}
        </Sec>}

        {/* ═══ SKILLS ═══ */}
        {sec==="skills"&&!q.trim()&&<Sec id="SK" t="Skills" cnt={st.sk}>
          {(D.skills||[]).map((s,i)=><div key={i} className="tmpl" style={{animation:`fu .15s ${i*15}ms both`}}>
            <div style={{display:"flex",justifyContent:"space-between"}}><div><span style={{color:"var(--g)",fontFamily:"var(--m)",fontSize:8}}>{s.id}</span> <span style={{fontSize:11,fontWeight:600}}>{s.nm}</span></div><span style={{fontSize:7,color:"var(--cy)"}}>{s.level}</span></div>
            <div style={{fontSize:9,color:"var(--t2)",margin:"3px 0"}}>{s.desc}</div>
            {(s.cmds||[]).map((c,j)=><div key={j} className="trm" style={{maxHeight:25,marginBottom:2,padding:"2px 6px",fontSize:9}} onClick={()=>cp(c)}>{c}</div>)}
          </div>)}
        </Sec>}

        {/* ═══ CHAT PASTE ═══ */}
        {sec==="paste"&&!q.trim()&&<Sec id="💬" t="Chat Paste" cnt={(D.chatPastes||[]).length} act={<button className="b bp" onClick={()=>sMod("paste")}>+ PASTE (⌘P)</button>}>
          <p style={{fontSize:9,color:"var(--t2)",marginBottom:8}}>Kopiér fra Claude/Gemini/ChatGPT → paste → vælg sektion → GEM & BOGFØR</p>
          {(D.chatPastes||[]).map((p,i)=><div key={i} className="cb" style={{animation:`fu .12s ${i*10}ms both`}}><div className="mt">{p.ts} · <span style={{color:"var(--pr)"}}>{p.source}</span>{p.target&&<> · →{p.target}</>}{p.section&&<> · 📋{p.section}</>}</div>{p.text?.slice(0,300)}{p.text?.length>300&&"..."}<div style={{marginTop:3}}><button className="b" style={{fontSize:7}} onClick={()=>cp(p.text)}>CP</button></div></div>)}
        </Sec>}

        {sec==="capture"&&!q.trim()&&<Sec id="⌨" t="Terminal" cnt={(D.captures||[]).length}>{!cap&&<button className="b bp" onClick={()=>{sCap(true);setTimeout(()=>cR.current?.focus(),50)}} style={{width:"100%",padding:8,marginBottom:8}}>⌨ CAPTURE (⌘K)</button>}{(D.captures||[]).map((c,i)=><div key={i} style={{marginBottom:6}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}><span style={{fontSize:7,color:"var(--t3)"}}>{c.ts}</span><div style={{display:"flex",gap:2}}><button className="b" style={{fontSize:6}} onClick={()=>cp(c.text)}>CP</button><button className="b bd" style={{fontSize:6}} onClick={()=>sD(d=>({...d,captures:d.captures.filter((_,j)=>j!==i)}))}>✕</button></div></div><pre className="trm" style={{maxHeight:100}}>{c.text}</pre></div>)}</Sec>}

        {sec==="tasks"&&!q.trim()&&<Sec id="☐" t="Opgaver" cnt={(D.tasks||[]).length} act={<button className="b bp" onClick={()=>sMod("task")}>+</button>}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:5}}>
            {["TODO","I GANG","KOMPLET"].map(col=><div key={col}><div style={{fontSize:7,fontFamily:"var(--m)",color:col==="TODO"?"var(--rd)":col==="I GANG"?"var(--g)":"var(--gn)",letterSpacing:1,marginBottom:3,paddingBottom:2,borderBottom:"1px solid currentColor"}}>{col}</div>
              {(D.tasks||[]).filter(t=>t.s===col).map((t,i)=>{const idx=(D.tasks||[]).indexOf(t);return<div key={i} style={{background:"var(--b2)",border:"1px solid var(--bd)",padding:"6px 7px",marginBottom:3,borderRadius:1,fontSize:9}}><div style={{fontWeight:600}}>{t.title}</div><div style={{display:"flex",gap:2,marginTop:2}}>{col!=="TODO"&&<button className="b" style={{fontSize:6,padding:"1px 3px"}} onClick={()=>sD(d=>({...d,tasks:d.tasks.map((x,j)=>j===idx?{...x,s:col==="I GANG"?"TODO":"I GANG"}:x)}))}>←</button>}{col!=="KOMPLET"&&<button className="b" style={{fontSize:6,padding:"1px 3px"}} onClick={()=>sD(d=>({...d,tasks:d.tasks.map((x,j)=>j===idx?{...x,s:col==="TODO"?"I GANG":"KOMPLET"}:x)}))}>→</button>}</div></div>})}</div>)}
          </div>
        </Sec>}

        {sec==="commands"&&!q.trim()&&<Sec id="$" t="Kommandoer" cnt={(D.cmds||[]).length}>{(D.cmds||[]).map((c,i)=><div key={c.id} style={{marginBottom:5,animation:`fu .12s ${i*12}ms both`}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:1}}><span style={{fontSize:9}}><span style={{color:"var(--g)",fontSize:7}}>{c.id}</span> {c.n}</span><button className="b" style={{fontSize:6}} onClick={()=>cp(c.cmd)}>KOPIÉR</button></div><pre className="trm" style={{maxHeight:35,fontSize:9}} onClick={()=>cp(c.cmd)}>{c.cmd}</pre></div>)}</Sec>}

        {sec==="files"&&!q.trim()&&<Sec id="📁" t="Filer" cnt={(D.files||[]).length}>
          <div className="dz" onDrop={e=>{e.preventDefault();hFiles(e.dataTransfer.files)}} onDragOver={e=>e.preventDefault()} onClick={()=>fR.current?.click()}><input ref={fR} type="file" multiple style={{display:"none"}} onChange={e=>hFiles(e.target.files)}/>Drop filer fra desktop</div>
          {(D.files||[]).map((f,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"4px 6px",borderBottom:"1px solid var(--bd)",fontSize:9}}><span>{f.name}</span><div style={{display:"flex",gap:2}}>{f.content&&<button className="b" style={{fontSize:6}} onClick={()=>sMod({tp:"file",f})}>VIS</button>}<button className="b bd" style={{fontSize:6}} onClick={()=>sD(d=>({...d,files:d.files.filter(x=>x.name!==f.name)}))}>✕</button></div></div>)}
        </Sec>}

        {sec==="bogforing"&&!q.trim()&&<Sec id="A-J" t="Bogføringsmappe" cnt={`${(D.bogforing||[]).reduce((s,b)=>s+b.f,0)} filer`}><Tbl cols={["KAT","NAVN","FIL","LINJER"]} rows={(D.bogforing||[]).map((b,i)=><tr key={i}><td style={{...td,color:"var(--g)",fontWeight:800,fontSize:13}}>{b.c}</td><td style={td}>{b.n}</td><td style={{...td,textAlign:"center"}}>{b.f}</td><td style={{...td,textAlign:"right"}}>{b.l.toLocaleString()}</td></tr>)}/></Sec>}

        {sec==="errors"&&!q.trim()&&<Sec id="⚠" t="Fejl" cnt={st.err}>{(D.errors||[]).map((e,i)=><div key={e.id} style={{display:"flex",gap:4,padding:"4px 0",borderBottom:"1px solid var(--bd)",fontSize:9,alignItems:"center"}}><span style={{color:"var(--g)",width:40}}>{e.id}</span><span style={{width:50}}>{e.sr}</span><span style={{flex:1}}>{e.ds}</span><SB s={e.sv}/><SF v={e.st} o={["ÅBEN","I GANG","LUKKET"]} os={v=>sD(d=>({...d,errors:d.errors.map(x=>x.id===e.id?{...x,st:v}:x)}))}/></div>)}</Sec>}

        {sec==="learnings"&&!q.trim()&&<Sec id="◆" t="Learnings" cnt={(D.learnings||[]).length}><Tbl cols={["ID","OMR","LEARNING"]} rows={(D.learnings||[]).map((l,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{l.id}</td><td style={{...td,color:"var(--t2)"}}>{l.a}</td><td style={td}>{l.t}</td></tr>)}/></Sec>}

        {sec==="rules"&&!q.trim()&&<Sec id="⛨" t="ODIN Regler" cnt={(D.rules||[]).length}><Tbl cols={["ID","REGEL","KAT"]} rows={(D.rules||[]).map((r,i)=><tr key={i}><td style={{...td,color:"var(--g)"}}>{r.id}</td><td style={td}>{r.r}</td><td style={{...td,color:"var(--t2)"}}>{r.c}</td></tr>)}/><div style={{marginTop:4,padding:5,border:"1px solid rgba(248,113,113,.1)",borderRadius:1,fontSize:8,color:"var(--rd)"}}>UFRAVIGELIGE</div></Sec>}

        {sec==="log"&&!q.trim()&&<Sec id="✎" t="Log" cnt={(D.log||[]).length} act={<button className="b" onClick={exportJ}>EXP</button>}>{(D.log||[]).slice(0,60).map((l,i)=><div key={i} style={{padding:"2px 0",borderBottom:"1px solid rgba(28,28,40,.1)",display:"grid",gridTemplateColumns:"95px 30px 1fr",gap:3,fontSize:8,fontFamily:"var(--m)",color:"var(--t2)"}}><span style={{color:"var(--t3)"}}>{l.ts}</span><span style={{color:"var(--g)"}}>{l.w}</span><span>{l.m}</span></div>)}</Sec>}
      </main>
    </div>

    {/* MODALS */}
    {mod==="paste"&&<Md t="💬 Chat Paste" oc={()=>sMod(null)}><NP onAdd={p=>{aPaste(p);sMod(null)}} proj={Object.entries(D.projects||{}).map(([k,v])=>({k,nm:v.nm}))}/></Md>}
    {mod==="task"&&<Md t="Ny opgave" oc={()=>sMod(null)}><NTk onAdd={t=>{sD(d=>({...d,tasks:[...(d.tasks||[]),t]}));lg("TASK:"+t.title);sMod(null)}}/></Md>}
    {mod?.tp==="file"&&<Md t={mod.f.name} oc={()=>sMod(null)}><pre className="trm" style={{maxHeight:350}}>{mod.f.content}</pre></Md>}
    {toast&&<div className="tst">{toast}</div>}
  </>;
}

function Md({t,oc,children}){useEffect(()=>{const h=e=>{if(e.key==="Escape")oc()};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[oc]);
return<div style={{position:"fixed",inset:0,zIndex:300,display:"flex",alignItems:"center",justifyContent:"center"}} onClick={oc}><div style={{position:"absolute",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(3px)"}}/><div onClick={e=>e.stopPropagation()} style={{background:"var(--bg)",border:"1px solid var(--gd)",padding:"14px 18px",borderRadius:2,width:440,maxHeight:"78vh",overflowY:"auto",animation:"fu .1s"}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:10}}><h3 style={{fontFamily:"var(--s)",fontSize:15,color:"var(--g)",fontStyle:"italic"}}>{t}</h3><button className="b" onClick={oc}>✕</button></div>{children}</div></div>}

const ip={width:"100%",padding:"4px 6px",background:"var(--b3)",border:"1px solid var(--bd)",color:"var(--tx)",fontSize:9,fontFamily:"var(--m)",borderRadius:1,outline:0};
const fl2={display:"block",fontSize:7,color:"var(--t3)",fontFamily:"var(--m)",marginBottom:1,marginTop:5};

function NP({onAdd,proj}){const[f,s]=useState({text:"",source:"Claude",target:"",section:""});
return<><label style={fl2}>KILDE<SF v={f.source} o={["Claude","Gemini","ChatGPT","Ollama","Andet"]} os={v=>s({...f,source:v})}/></label>
<label style={fl2}>TEKST *<textarea value={f.text} onChange={e=>s({...f,text:e.target.value})} rows={5} placeholder="Paste chat-output..." style={{...ip,resize:"vertical",minHeight:80}}/></label>
<label style={fl2}>TILKNYT PROJEKT<select value={f.target} onChange={e=>s({...f,target:e.target.value})} style={ip}><option value="">— Intet —</option>{proj.map(p=><option key={p.k} value={p.k}>{p.nm}</option>)}</select></label>
<label style={fl2}>SEKTION<input value={f.section} onChange={e=>s({...f,section:e.target.value})} placeholder="DISCOVERY, CONFIG..." style={ip}/></label>
<div style={{display:"flex",gap:3,marginTop:8,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.text.trim())return alert("Tekst");onAdd(f)}}>GEM & BOGFØR</button></div></>}

function NTk({onAdd}){const[f,s]=useState({title:"",s:"TODO"});
return<><label style={fl2}>TITEL *<input value={f.title} onChange={e=>s({...f,title:e.target.value})} style={ip}/></label>
<div style={{display:"flex",gap:3,marginTop:8,justifyContent:"flex-end"}}><button className="b bp" onClick={()=>{if(!f.title)return alert("Titel");onAdd(f)}}>OPRET</button></div></>}
