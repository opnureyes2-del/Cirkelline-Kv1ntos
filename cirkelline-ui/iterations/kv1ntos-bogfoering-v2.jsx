import { useState, useMemo, useEffect, useRef, useCallback } from "react";

/* ══════════════════════════════════════════════════════════════════
   KV1NTOS BOGFØRINGSMAPPE v2.0 — ADMIRAL OPERATIONS CENTER
   Spil-kvalitet grafik. Alle detaljer. Intet udeladt.
   ══════════════════════════════════════════════════════════════════ */

// ─── COMPLETE SYSTEM DATA ───────────────────────────────────────
const D = {
  meta: { name:"KV1NTOS",version:"3.0.0",admiral:"Elle",created:"2026-02-11",phase:0,phaseName:"DISCOVERY",elements:238,verified:0,manualFiles:38,manualLines:4016,bogFiles:71,bogLines:64344 },
  phases: [
    {id:0,name:"DISCOVERY",status:"I GANG",desc:"Find ALT. Antag INTET.",verify:"Alle fund klassificeret + Admiral godkender",deps:"Ingen",output:"SCAN-RESULTAT.md + FUND-LISTE.md"},
    {id:1,name:"OPRYDNING",status:"VENTER",desc:"Fjern det ødelagte. Bevar det fungerende.",verify:"docker ps viser KUN nødvendige",deps:"Fase 0 komplet",output:"Rent Docker environment"},
    {id:2,name:"FUNDAMENT",status:"VENTER",desc:"Docker, netværk, Git, mapper.",verify:"Docker+Compose+netværk+Git rent",deps:"Fase 1 komplet",output:"Stabil base-infrastruktur"},
    {id:3,name:"OBSERVABILITY",status:"VENTER",desc:"Prometheus, Loki, Tempo, Grafana.",verify:"Grafana UDEN fejl, datasources grønne",deps:"Fase 2 komplet",output:"Fuld synlighed i Grafana"},
    {id:4,name:"AI-MODELLER",status:"VENTER",desc:"Ollama, Claude, Gemini — hver for sig.",verify:"Hver model svarer + rate-limiter aktiv",deps:"Fase 3 komplet",output:"AI klar med rate-limiting"},
    {id:5,name:"ODIN",status:"VENTER",desc:"Videnbase, regler, agent-register.",verify:"Admiral→ODIN→HQ→Agent→Resultat",deps:"Fase 4 komplet",output:"Komplet kommandokæde"},
    {id:6,name:"INTEGRATION",status:"VENTER",desc:"Forbind det der virker.",verify:"Alt snakker med alt, Grafana bekræfter",deps:"Fase 5 komplet",output:"Sammenhængende system"},
    {id:7,name:"PROJEKTER",status:"VENTER",desc:"BØRNESKABER, Three Realms, Gaming.",verify:"Projekter kører stabilt",deps:"Fase 6 komplet",output:"Live produktionsprojekter"},
  ],
  services: [
    {id:"SVC-001",name:"Docker Engine",port:"sock",status:"AFVENTER SCAN",cat:"CORE",phase:2,bog:["A4","B5","C7"],dep:[],depBy:["SVC-002","SVC-003","SVC-004","SVC-005","SVC-006","SVC-007","SVC-008"],health:"systemctl status docker"},
    {id:"SVC-002",name:"Prometheus",port:9090,status:"AFVENTER SCAN",cat:"OBSERVE",phase:3,bog:["A7","C10"],dep:["SVC-001"],depBy:["SVC-004"],health:"curl localhost:9090/-/healthy"},
    {id:"SVC-003",name:"Loki",port:3100,status:"AFVENTER SCAN",cat:"OBSERVE",phase:3,bog:["A7","C10"],dep:["SVC-001"],depBy:["SVC-004"],health:"curl localhost:3100/ready"},
    {id:"SVC-004",name:"Grafana",port:3000,status:"AFVENTER SCAN",cat:"OBSERVE",phase:3,bog:["A7","B7","C10"],dep:["SVC-001","SVC-002","SVC-003"],depBy:[],health:"curl localhost:3000/api/health"},
    {id:"SVC-005",name:"Tempo",port:3200,status:"AFVENTER SCAN",cat:"OBSERVE",phase:3,bog:["A7"],dep:["SVC-001"],depBy:["SVC-004"],health:"curl localhost:3200/ready"},
    {id:"SVC-006",name:"Alertmanager",port:9093,status:"AFVENTER SCAN",cat:"OBSERVE",phase:3,bog:["A7"],dep:["SVC-001","SVC-002"],depBy:[],health:"curl localhost:9093/-/healthy"},
    {id:"SVC-007",name:"n8n",port:5678,status:"AFVENTER SCAN",cat:"AUTO",phase:6,bog:[],dep:["SVC-001"],depBy:[],health:"curl localhost:5678/healthz"},
    {id:"SVC-008",name:"Ollama",port:11434,status:"AFVENTER SCAN",cat:"AI",phase:4,bog:[],dep:[],depBy:[],health:"curl localhost:11434"},
  ],
  platforms: [
    {id:"PLT-001",name:"Cirkelline System",port:7777,status:"AFVENTER SCAN",bog:["A2","B1","C1","D2"],db:"PostgreSQL:5533",phase:7},
    {id:"PLT-002",name:"Cosmic Library",port:7778,status:"AFVENTER SCAN",bog:["A2","B2","C2","D3"],db:"PostgreSQL:5534",phase:7},
    {id:"PLT-003",name:"CKC Gateway",port:7779,status:"AFVENTER SCAN",bog:["A2","B3","C3","D4"],db:null,phase:7},
    {id:"PLT-004",name:"Kommandør Gateway",port:7800,status:"AFVENTER SCAN",bog:["A2","B4","C4","D5"],db:null,phase:7},
    {id:"PLT-005",name:"BØRNESKABER",port:null,status:"IKKE STARTET",bog:[],db:null,phase:7,note:"Genesis-sekvens: farver, lyde, tegninger"},
    {id:"PLT-006",name:"Three Realms",port:null,status:"IKKE STARTET",bog:[],db:null,phase:7,note:"GPS+3 tidsperioder: 1825, nu, 2050"},
    {id:"PLT-007",name:"Gaming Platform",port:null,status:"IKKE STARTET",bog:[],db:null,phase:7,note:"Steam-kvalitet, brætspil, invitation-only"},
  ],
  apis: [
    {id:"API-001",name:"Claude (privat)",provider:"Anthropic",status:"AFVENTER TEST",bog:["C9"],models:["opus-4-6","sonnet-4-5","haiku-4-5"],limit:"Max 3 samtidige",phase:4,alias:"claude-admiral"},
    {id:"API-002",name:"Claude (firma)",provider:"Anthropic",status:"AFVENTER TEST",bog:["C9"],models:["opus-4-6","sonnet-4-5","haiku-4-5"],limit:"Max 3 samtidige",phase:4},
    {id:"API-003",name:"Gemini",provider:"Google",status:"AFVENTER TEST",bog:["C9"],models:["2.0-flash","2.0-pro"],limit:"TBD",phase:4,note:"Fleet Router"},
  ],
  integrations: [
    {id:"INT-001",name:"AI Fleet Manager",port:9800,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-002",name:"Family Orchestrator",port:9801,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-003",name:"Evolved Swarm",port:9802,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-004",name:"Cirkelline Evolved",port:9803,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-005",name:"CKC Gateway Evolved",port:9804,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-006",name:"Kommandør Evolved",port:9805,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-007",name:"Cosmic Evolved",port:9806,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-008",name:"Unified Brain",port:9807,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-009",name:"Admiral Hybrid Coord.",port:9808,status:"AFVENTER SCAN",bog:["J2"],phase:5},
    {id:"INT-010",name:"Production Dashboard",port:9809,status:"AFVENTER SCAN",bog:["J2"],phase:6},
    {id:"INT-011",name:"Family Message Bus",port:9010,status:"AFVENTER SCAN",bog:["J2","I4"],phase:6},
  ],
  agents: [
    {id:"AGT-KOM",name:"Kommandør",system:"Kommandør",count:21,reg:true,bog:["E3"],sub:[{n:"Managers",c:5,r:"M-001→M-005"},{n:"Specialists",c:5,r:"S-001→S-005"},{n:"Researchers",c:3,r:"R-001→R-003"},{n:"Analysts",c:4,r:"A-001→A-004"},{n:"Guardians",c:4,r:"G-001→G-004"}]},
    {id:"AGT-ELLE",name:"ELLE",system:"ELLE",count:122,reg:false,bog:["E1"],sub:[{n:"Health",c:30},{n:"Training",c:25},{n:"Monitoring",c:20},{n:"Other",c:47}]},
    {id:"AGT-CKC",name:"CKC",system:"CKC",count:5,reg:false,bog:["E3"],sub:[]},
    {id:"AGT-COS",name:"Cosmic",system:"Cosmic",count:9,reg:false,bog:["E4"],sub:[{n:"Research Team",c:9}]},
  ],
  databases: [
    {id:"DB-001",name:"PostgreSQL (Cirkelline)",port:5533,status:"AFVENTER SCAN",bog:["A5","C8"],plt:"PLT-001"},
    {id:"DB-002",name:"PostgreSQL (Cosmic)",port:5534,status:"AFVENTER SCAN",bog:["A5","C8"],plt:"PLT-002"},
    {id:"DB-003",name:"Redis",port:null,status:"AFVENTER SCAN",bog:["C5"],plt:null},
  ],
  containers: [
    {id:"CTR-001",name:"kv1ntos-prometheus",image:"prom/prometheus",port:9090,bog:["A4"]},
    {id:"CTR-002",name:"kv1ntos-loki",image:"grafana/loki",port:3100,bog:["A4"]},
    {id:"CTR-003",name:"kv1ntos-tempo",image:"grafana/tempo",port:3200,bog:["A4"]},
    {id:"CTR-004",name:"kv1ntos-grafana",image:"grafana/grafana",port:3000,bog:["A4"]},
    {id:"CTR-005",name:"kv1ntos-alertmanager",image:"prom/alertmanager",port:9093,bog:["A4"]},
    {id:"CTR-006",name:"kv1ntos-n8n",image:"n8nio/n8n",port:5678,bog:["A4"]},
  ],
  bogforing: [
    {c:"A",name:"STATUS",files:10,lines:8241,map:"01-discovery + 02-registrering",desc:"Hvad systemet ER NU"},
    {c:"B",name:"COMMANDS",files:10,lines:6671,map:"04-drift",desc:"Alle kommandoer"},
    {c:"C",name:"CONFIGURATION",files:10,lines:9850,map:"05-kontrol",desc:"Env + konfiguration"},
    {c:"D",name:"ARCHITECTURE",files:10,lines:16787,map:"03-genopbygning",desc:"Arkitektur + design"},
    {c:"E",name:"AGENTS",files:4,lines:5060,map:"02-registrering",desc:"157 agent templates"},
    {c:"F",name:"HISTORY",files:10,lines:707,map:"07-log",desc:"Historisk dokumentation"},
    {c:"G",name:"LAPTOP KATALOG",files:5,lines:1751,map:"01-discovery",desc:"Desktop mappestruktur"},
    {c:"H",name:"ADMIRAL FLEET",files:2,lines:642,map:"05-kontrol",desc:"Multi-Admiral workflow"},
    {c:"I",name:"OPS EXCELLENCE",files:8,lines:5320,map:"05-kontrol + 07-log",desc:"ODIN regler, compliance"},
    {c:"J",name:"META-DOK",files:2,lines:6300,map:"00-styring",desc:"Deep dive + oversigt"},
  ],
  manualDirs: [
    {dir:"00-styring",name:"STYRING",files:[{f:"MANUAL.md",l:131,t:"Overordnet styring"},{f:"MASTERPLAN.md",l:284,t:"7-faset plan"},{f:"STATUS.md",l:65,t:"Levende tracker"}]},
    {dir:"01-discovery",name:"DISCOVERY",files:[{f:"SCAN-PROCEDURE.md",l:292,t:"10 scan-blokke"},{f:"SCAN-RESULTAT.md",l:12,t:"Tom — afventer scan"},{f:"FUND-LISTE.md",l:115,t:"Klassificeringstabeller"}]},
    {dir:"02-registrering",name:"REGISTRERING",files:[{f:"REGISTER.md",l:141,t:"238+ elementer, krydsref"}]},
    {dir:"03-genopbygning",name:"GENOPBYGNING",files:[{f:"FASER-DETALJERET.md",l:250,t:"Alle faser detaljeret"},{f:"FASE-1-oprydning.md",l:128},{f:"FASE-2-fundament.md",l:56},{f:"FASE-3-observe.md",l:71},{f:"FASE-4-ai.md",l:64},{f:"FASE-5-odin.md",l:49},{f:"FASE-6-integration.md",l:42},{f:"FASE-7-projekter.md",l:44},{f:"DOCKER-COMPOSE-REFERENCE.md",l:222,t:"Komplet Compose"},{f:"ODIN-SETUP.md",l:215,t:"ODIN videnbase guide"}]},
    {dir:"04-drift",name:"DRIFT",files:[{f:"DAGLIG-TJEK.md",l:73,t:"5 min dagligt script"},{f:"UGENTLIG-TJEK.md",l:103,t:"15 min ugentligt"},{f:"FEJLFINDING.md",l:253,t:"Symptom→diagnose→fix"},{f:"NOEDPROCEDURE.md",l:102,t:"Alt er galt → gør dette"}]},
    {dir:"05-kontrol",name:"KONTROL",files:[{f:"HVEM-GJOER-HVAD.md",l:64,t:"Roller + adgangsmatrix"},{f:"SIKKERHED.md",l:141,t:"Nøgler, scanning, firewall"},{f:"AENDRINGSLOG.md",l:22,t:"Hvad ændredes, hvornår"},{f:"KVALITET.md",l:92,t:"Hvad kræves for godkendt"}]},
    {dir:"06-templates",name:"TEMPLATES",files:[{f:"ELEMENT.md",l:159,t:"Element-registreringsskabelon"},{f:"TASK.md",l:104,t:"Admiral→Agent opgave"},{f:"FEJLRAPPORT.md",l:67,t:"Fejllog-skabelon"},{f:"PROMPT-GENERAL.md",l:49},{f:"PROMPT-KODE.md",l:59},{f:"PROMPT-UI.md",l:64},{f:"PROMPT-SPIL.md",l:60},{f:"PROMPT-3D.md",l:53},{f:"PROMPT-SKABELONER.md",l:255,t:"Alle prompts samlet"}]},
    {dir:"07-log",name:"LOG",files:[{f:"CHANGELOG.md",l:34,t:"Alle ændringer"},{f:"ERRORS.md",l:9,t:"3 kendte fejl"},{f:"LEARNINGS.md",l:34,t:"12 learnings→ODIN"},{f:"TODO.md",l:38,t:"Prioriteret opgaveliste"}]},
  ],
  errors: [
    {id:"E-001",date:"2026-02-11",src:"Grafana",desc:"Fejl synlige i dashboards",sev:"HØJ",status:"ÅBEN",fix:"Afventer scan"},
    {id:"E-002",date:"2026-02",src:"API",desc:"Agenter udtømmer API kvoter samtidigt",sev:"KRITISK",status:"ÅBEN",fix:"Rate-limiter skal implementeres",learn:"Max 3 samtidige Claude-kald"},
    {id:"E-003",date:"2026-02",src:"Plugins",desc:"28 plugins, kun 16 aktive",sev:"MIDDEL",status:"ÅBEN",fix:"Scan identificerer plugins"},
  ],
  learnings: [
    {id:"L-001",a:"INFRA",l:"Agenter kalder API samtidigt → quota udtømt",o:"rules/api-limits.md"},
    {id:"L-002",a:"INFRA",l:"Containere uden restart-policy forsvinder",o:"rules/docker-regler.md"},
    {id:"L-003",a:"INFRA",l:"Grafana datasource URL: container-navn vs localhost",o:"knowledge/grafana.md"},
    {id:"L-004",a:"INFRA",l:"VRAM frigives IKKE automatisk ved crash",o:"rules/ollama-regler.md"},
    {id:"L-005",a:"INFRA",l:"nvidia-smi SKAL tjekkes FØR model load",o:"rules/ollama-regler.md"},
    {id:"L-010",a:"PROMPT",l:"Opus leverer minimum uden 'gå ud over det basale'",o:"knowledge/prompting.md"},
    {id:"L-011",a:"PROMPT",l:"XML-tags giver markant bedre output",o:"knowledge/prompting.md"},
    {id:"L-012",a:"PROMPT",l:"Ét eksempel > 100 ord instruktion",o:"knowledge/prompting.md"},
    {id:"L-013",a:"PROMPT",l:"Plan→godkendelse→kode (aldrig omvendt)",o:"knowledge/prompting.md"},
    {id:"L-014",a:"PROMPT",l:"Anti-cheat prompt forhindrer genveje",o:"knowledge/prompting.md"},
    {id:"L-020",a:"PROCES",l:"Konceptuelt overblik ≠ brugbar vejledning",o:"rules/kvalitet.md"},
    {id:"L-021",a:"PROCES",l:"Maskin-scan er BLOCKER — uden data er alt teori",o:"rules/discovery.md"},
    {id:"L-022",a:"PROCES",l:"Ét element ad gangen > mange parallelt",o:"rules/genopbygning.md"},
    {id:"L-023",a:"PROCES",l:"Alt i filer, intet i chat-historik",o:"rules/dokumentation.md"},
  ],
  rules: [
    {id:"R-01",r:"API-nøgler ALDRIG i Git",c:"SIKKERHED"},{id:"R-02",r:"Containere: restart + healthcheck + Loki",c:"DOCKER"},
    {id:"R-03",r:"Firewall aktiveret (UFW)",c:"SIKKERHED"},{id:"R-04",r:"Ugentlig scanning (ClamAV+rkhunter)",c:"SIKKERHED"},
    {id:"R-05",r:"Max 3 samtidige Claude API-kald",c:"API"},{id:"R-06",r:"Max 50 samtidige API-kald totalt",c:"API"},
    {id:"R-07",r:"Alle ændringer committes med besked",c:"GIT"},{id:"R-08",r:"Ugentlig backup, verificeret",c:"BACKUP"},
    {id:"R-09",r:"Docker images scannes med Trivy",c:"SIKKERHED"},{id:"R-10",r:"git-secrets scanner før push",c:"SIKKERHED"},
    {id:"R-11",r:"Alle porte binder til 127.0.0.1",c:"NETVÆRK"},{id:"R-12",r:"0 TODO, fejlhåndtering, validering",c:"KVALITET"},
    {id:"R-13",r:"nvidia-smi FØR Ollama model load",c:"AI"},
  ],
};

// ─── PARTICLE CANVAS ─────────────────────────────────────────────
function ParticleBG() {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d");
    let w, h, pts = [], af;
    const resize = () => { w = c.width = c.offsetWidth; h = c.height = c.offsetHeight; };
    resize(); window.addEventListener("resize", resize);
    for (let i = 0; i < 60; i++) pts.push({ x: Math.random()*2000, y: Math.random()*2000, vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3, r: Math.random()*1.5+0.5, a: Math.random()*0.4+0.1 });
    const draw = () => {
      ctx.clearRect(0,0,w,h);
      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle = `rgba(212,160,84,${p.a})`; ctx.fill();
      });
      // connection lines
      for (let i=0;i<pts.length;i++) for (let j=i+1;j<pts.length;j++) {
        const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y, d=Math.sqrt(dx*dx+dy*dy);
        if (d<120) { ctx.beginPath(); ctx.moveTo(pts[i].x,pts[i].y); ctx.lineTo(pts[j].x,pts[j].y);
          ctx.strokeStyle=`rgba(212,160,84,${0.06*(1-d/120)})`; ctx.stroke(); }
      }
      af = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(af); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={ref} style={{position:"fixed",inset:0,width:"100%",height:"100%",zIndex:0,pointerEvents:"none"}} />;
}

// ─── ANIMATED COUNTER ────────────────────────────────────────────
function Counter({end,dur=1200,prefix="",suffix="",style:s}) {
  const [v,setV]=useState(0);
  useEffect(()=>{
    let start=0;const t0=performance.now();
    const step=(t)=>{const p=Math.min((t-t0)/dur,1);setV(Math.floor(p*end));if(p<1)requestAnimationFrame(step);};
    requestAnimationFrame(step);
  },[end,dur]);
  return <span style={s}>{prefix}{typeof end==="number"&&end>999?v.toLocaleString():v}{suffix}</span>;
}

// ─── STYLES ──────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root {
  --bg: #060608; --bg2: #0c0c10; --bg3: #12121a; --border: #1a1a24;
  --gold: #d4a054; --gold2: #e8c07a; --gold-dim: #6b5a3a;
  --green: #4ade80; --red: #f87171; --blue: #60a5fa; --purple: #c084fc; --cyan: #22d3ee;
  --text: #e2ddd4; --text2: #999; --text3: #555;
  --font: 'Outfit', sans-serif; --mono: 'JetBrains Mono', monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--gold-dim); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }
@keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
@keyframes slideIn { from { opacity:0; transform:translateX(40px); } to { opacity:1; transform:translateX(0); } }
@keyframes glow { 0%,100% { box-shadow:0 0 8px rgba(212,160,84,0.15); } 50% { box-shadow:0 0 20px rgba(212,160,84,0.3); } }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
@keyframes scanline { 0% { transform:translateY(-100%); } 100% { transform:translateY(100vh); } }
.grain { position:fixed; inset:0; z-index:1; pointer-events:none; opacity:0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
.scanline { position:fixed; left:0; width:100%; height:2px; background:linear-gradient(90deg,transparent,rgba(212,160,84,0.06),transparent);
  z-index:1; pointer-events:none; animation:scanline 8s linear infinite; }
`;

// ─── STATUS BADGE ────────────────────────────────────────────────
const SB = ({s}) => {
  const m = {"AFVENTER SCAN":{bg:"#1c1810",fg:"var(--gold)",b:"var(--gold-dim)"},"I GANG":{bg:"#0c1a10",fg:"var(--green)",b:"#1a4a2a"},"VENTER":{bg:"#10101c",fg:"var(--blue)",b:"#1a1a4a"},"KOMPLET":{bg:"#0c1a0c",fg:"#4ade80",b:"#1a4a1a"},"ÅBEN":{bg:"#1c0c0c",fg:"var(--red)",b:"#4a1a1a"},"AFVENTER TEST":{bg:"#1c1810",fg:"var(--gold)",b:"var(--gold-dim)"},"IKKE STARTET":{bg:"#0c0c0c",fg:"#444",b:"#222"},"KRITISK":{bg:"#2a0808",fg:"#ff4444",b:"#5a1010"},"HØJ":{bg:"#1c1208",fg:"#f59e0b",b:"#4a3010"},"MIDDEL":{bg:"#1c1c08",fg:"#eab308",b:"#4a4a10"}};
  const c=m[s]||{bg:"#0c0c0c",fg:"#666",b:"#222"};
  return <span style={{display:"inline-block",padding:"3px 10px",fontSize:10,fontFamily:"var(--mono)",fontWeight:500,background:c.bg,color:c.fg,border:`1px solid ${c.b}`,letterSpacing:0.8,textTransform:"uppercase",borderRadius:2,whiteSpace:"nowrap"}}>{s}</span>;
};

// ─── SECTION HEADER ──────────────────────────────────────────────
const SH = ({id,title,count,sub}) => (
  <div style={{marginTop:32,marginBottom:14,animation:"fadeUp 0.4s ease-out",paddingBottom:10,borderBottom:"1px solid var(--border)",position:"relative"}}>
    <div style={{position:"absolute",bottom:-1,left:0,width:60,height:1,background:"var(--gold)"}} />
    <div style={{display:"flex",alignItems:"baseline",gap:10}}>
      <span style={{fontFamily:"var(--mono)",fontSize:11,color:"var(--gold)",letterSpacing:2,fontWeight:600}}>{id}</span>
      <h2 style={{fontSize:18,fontWeight:600,color:"var(--text)",letterSpacing:0.3,fontFamily:"var(--font)"}}>{title}</h2>
      {count!=null&&<span style={{fontFamily:"var(--mono)",fontSize:11,color:"var(--text3)"}}>({count})</span>}
    </div>
    {sub&&<p style={{fontSize:12,color:"var(--text2)",marginTop:4}}>{sub}</p>}
  </div>
);

// ─── DATA TABLE ──────────────────────────────────────────────────
const TBL = ({cols,rows,onRow}) => (
  <div style={{overflowX:"auto",marginBottom:16,animation:"fadeUp 0.5s ease-out"}}>
    <table style={{width:"100%",borderCollapse:"separate",borderSpacing:0,fontSize:12,fontFamily:"var(--mono)"}}>
      <thead><tr>{cols.map((c,i)=><th key={i} style={{textAlign:"left",padding:"8px 12px",borderBottom:"1px solid var(--border)",color:"var(--text3)",fontSize:10,fontWeight:600,letterSpacing:1.2,textTransform:"uppercase",whiteSpace:"nowrap",position:"sticky",top:0,background:"var(--bg2)",zIndex:2}}>{c.h}</th>)}</tr></thead>
      <tbody>{rows.map((r,ri)=>(
        <tr key={ri} onClick={()=>onRow?.(r)} style={{cursor:onRow?"pointer":"default",transition:"all 0.15s",borderBottom:"1px solid rgba(26,26,36,0.5)",animationDelay:`${ri*30}ms`,animation:"fadeUp 0.3s ease-out both"}}
          onMouseEnter={e=>{if(onRow){e.currentTarget.style.background="rgba(212,160,84,0.04)";e.currentTarget.style.transform="translateX(2px)"}}}
          onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.transform="translateX(0)"}}>
          {cols.map((c,ci)=><td key={ci} style={{padding:"9px 12px",color:"var(--text)",whiteSpace:c.nw?"nowrap":"normal",maxWidth:c.mw||"none",overflow:"hidden",textOverflow:"ellipsis",borderBottom:"1px solid rgba(26,26,36,0.3)"}}>{c.r?c.r(r):r[c.k]}</td>)}
        </tr>
      ))}</tbody>
    </table>
  </div>
);

// ─── STAT CARD ───────────────────────────────────────────────────
const SC = ({label,value,sub,color,delay=0}) => (
  <div style={{background:"var(--bg2)",border:"1px solid var(--border)",padding:"16px 18px",position:"relative",overflow:"hidden",animation:`fadeUp 0.5s ease-out ${delay}ms both`,transition:"all 0.25s",borderRadius:2}}
    onMouseEnter={e=>{e.currentTarget.style.borderColor="var(--gold-dim)";e.currentTarget.style.transform="translateY(-2px)"}}
    onMouseLeave={e=>{e.currentTarget.style.borderColor="var(--border)";e.currentTarget.style.transform="translateY(0)"}}>
    <div style={{position:"absolute",top:0,left:0,right:0,height:1,background:`linear-gradient(90deg,transparent,${color||"var(--gold)"},transparent)`,opacity:0.4}} />
    <Counter end={typeof value==="number"?value:0} style={{fontFamily:"var(--mono)",fontSize:28,fontWeight:700,color:color||"var(--gold)",lineHeight:1,display:"block"}} />
    {typeof value==="string"&&<span style={{fontFamily:"var(--mono)",fontSize:28,fontWeight:700,color:color||"var(--gold)",lineHeight:1}}>{value}</span>}
    <div style={{fontSize:11,color:"var(--text2)",marginTop:6,letterSpacing:0.5,fontFamily:"var(--font)"}}>{label}</div>
    {sub&&<div style={{fontSize:10,color:"var(--text3)",marginTop:2,fontFamily:"var(--mono)"}}>{sub}</div>}
  </div>
);

// ─── DETAIL PANEL ────────────────────────────────────────────────
const Detail = ({item:it,onClose}) => {
  if(!it) return null;
  const Field = ({l,v,color}) => v ? <div style={{marginBottom:12}}><div style={{fontSize:10,color:"var(--text3)",letterSpacing:1,textTransform:"uppercase",marginBottom:3,fontFamily:"var(--mono)"}}>{l}</div><div style={{fontSize:13,color:color||"var(--text)",fontFamily:"var(--font)"}}>{typeof v==="object"&&Array.isArray(v)?v.join(", "):String(v)}</div></div> : null;
  return (
    <div style={{position:"fixed",inset:0,zIndex:200,display:"flex",justifyContent:"flex-end"}} onClick={onClose}>
      <div style={{position:"absolute",inset:0,background:"rgba(0,0,0,0.6)",backdropFilter:"blur(4px)"}} />
      <div onClick={e=>e.stopPropagation()} style={{width:440,height:"100vh",background:"var(--bg)",borderLeft:"1px solid var(--gold-dim)",overflowY:"auto",padding:"24px 28px",position:"relative",animation:"slideIn 0.3s ease-out",boxShadow:"-8px 0 40px rgba(0,0,0,0.5)"}}>
        <div style={{position:"absolute",top:0,left:0,width:1,height:"100%",background:"linear-gradient(180deg,var(--gold),transparent)"}} />
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
          <span style={{fontFamily:"var(--mono)",fontSize:12,color:"var(--gold)",letterSpacing:1,fontWeight:600}}>{it.id}</span>
          <button onClick={onClose} style={{background:"none",border:"1px solid var(--border)",color:"var(--text2)",padding:"5px 14px",cursor:"pointer",fontFamily:"var(--mono)",fontSize:11,borderRadius:2,transition:"all 0.15s"}}
            onMouseEnter={e=>{e.currentTarget.style.borderColor="var(--gold)";e.currentTarget.style.color="var(--gold)"}}
            onMouseLeave={e=>{e.currentTarget.style.borderColor="var(--border)";e.currentTarget.style.color="var(--text2)"}}>ESC</button>
        </div>
        <h3 style={{fontSize:20,fontWeight:700,color:"var(--text)",marginBottom:20,fontFamily:"var(--font)"}}>{it.name}</h3>
        <Field l="STATUS" v={it.status} /><Field l="PORT" v={it.port} color="var(--cyan)" />
        <Field l="KATEGORI" v={it.cat||it.category} /><Field l="FASE" v={it.phase!=null?`FASE ${it.phase}: ${D.phases[it.phase]?.name}`:null} />
        <Field l="BESKRIVELSE" v={it.desc||it.note} /><Field l="DATABASE" v={it.db} color="var(--blue)" />
        <Field l="PROVIDER" v={it.provider} /><Field l="MODELLER" v={it.models} color="var(--purple)" />
        <Field l="RATE LIMIT" v={it.limit||it.rateLimit} color="var(--gold)" />
        <Field l="HEALTHCHECK" v={it.health} color="var(--cyan)" /><Field l="FIX" v={it.fix} />
        <Field l="LEARNING" v={it.learn||it.learning} color="var(--green)" />
        <Field l="→ ODIN" v={it.o||it.odinTarget} color="var(--purple)" />
        {(it.bog||it.bogRef)?.length>0&&<div style={{marginBottom:12}}><div style={{fontSize:10,color:"var(--text3)",letterSpacing:1,marginBottom:6,fontFamily:"var(--mono)"}}>BOGFØRINGSMAPPE REF</div><div style={{display:"flex",gap:6,flexWrap:"wrap"}}>{(it.bog||it.bogRef).map((r,i)=><span key={i} style={{padding:"3px 8px",background:"rgba(192,132,252,0.08)",border:"1px solid rgba(192,132,252,0.2)",color:"var(--purple)",fontSize:11,fontFamily:"var(--mono)",borderRadius:2}}>{r}</span>)}</div></div>}
        {(it.dep||it.depends)?.length>0&&<Field l="AFHÆNGER AF" v={it.dep||it.depends} />}
        {(it.depBy||it.dependedBy)?.length>0&&<Field l="BRUGES AF" v={it.depBy||it.dependedBy} />}
        {it.sub?.length>0&&<div style={{marginBottom:12}}><div style={{fontSize:10,color:"var(--text3)",letterSpacing:1,marginBottom:6,fontFamily:"var(--mono)"}}>UNDERGRUPPER</div>{it.sub.map((s,i)=><div key={i} style={{padding:"6px 10px",background:"var(--bg2)",border:"1px solid var(--border)",marginBottom:4,fontSize:12,color:"var(--text)",fontFamily:"var(--mono)",borderRadius:2,display:"flex",justifyContent:"space-between"}}><span>{s.n||s.name}</span><span style={{color:"var(--purple)"}}>{s.c||s.count}</span></div>)}</div>}
      </div>
    </div>
  );
};

// ─── NAV ITEMS ───────────────────────────────────────────────────
const NAV=[
  {id:"overview",l:"OVERBLIK",i:"◈"},{id:"phases",l:"FASER",i:"▸"},{id:"services",l:"SERVICES",i:"●"},
  {id:"platforms",l:"PLATFORME",i:"◻"},{id:"apis",l:"API'ER",i:"⟡"},{id:"integrations",l:"INTEGRATIONER",i:"⊞"},
  {id:"agents",l:"AGENTER",i:"◎"},{id:"containers",l:"CONTAINERE",i:"▣"},{id:"databases",l:"DATABASER",i:"▥"},
  {id:"manual",l:"MANUAL FILER",i:"📄"},{id:"bogforing",l:"BOGFØRING A-J",i:"📋"},
  {id:"errors",l:"FEJL",i:"⚠"},{id:"learnings",l:"LEARNINGS",i:"◆"},{id:"rules",l:"ODIN REGLER",i:"⛨"},
];

// ═══════════════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════════════
export default function App() {
  const [sec,setSec]=useState("overview");
  const [q,setQ]=useState("");
  const [sel,setSel]=useState(null);
  const [filt,setFilt]=useState("ALL");
  const totalAgents=D.agents.reduce((s,g)=>s+g.count,0);
  const all=[...D.services,...D.platforms,...D.apis,...D.integrations,...D.databases,...D.containers];

  const filtered=useMemo(()=>{
    let items=all;
    if(filt!=="ALL") items=items.filter(i=>i.status===filt);
    if(q.trim()){const ql=q.toLowerCase();items=items.filter(i=>i.name.toLowerCase().includes(ql)||i.id.toLowerCase().includes(ql)||(i.cat||"").toLowerCase().includes(ql));}
    return items;
  },[q,filt]);

  const statusCounts=useMemo(()=>{const c={};all.forEach(e=>{if(e.status)c[e.status]=(c[e.status]||0)+1});return c;},[]);

  useEffect(()=>{const h=e=>{if(e.key==="Escape")setSel(null)};window.addEventListener("keydown",h);return()=>window.removeEventListener("keydown",h)},[]);

  return (
    <>
      <style>{CSS}</style>
      <ParticleBG />
      <div className="grain" />
      <div className="scanline" />

      <div style={{display:"flex",minHeight:"100vh",position:"relative",zIndex:10,fontFamily:"var(--font)"}}>
        {/* ═══ SIDEBAR ═══ */}
        <nav style={{width:210,borderRight:"1px solid var(--border)",flexShrink:0,position:"fixed",top:0,left:0,height:"100vh",overflowY:"auto",background:"rgba(6,6,8,0.95)",backdropFilter:"blur(12px)",zIndex:50}}>
          <div style={{padding:"18px 18px 14px",borderBottom:"1px solid var(--border)"}}>
            <div style={{fontFamily:"var(--mono)",fontSize:13,color:"var(--gold)",letterSpacing:3,fontWeight:700}}>KV1NTOS</div>
            <div style={{fontSize:10,color:"var(--text3)",marginTop:2,fontFamily:"var(--mono)",letterSpacing:0.5}}>BOGFØRINGSMAPPE v2.0</div>
            <div style={{marginTop:8,display:"flex",gap:6}}>
              <span style={{fontSize:10,color:"var(--green)",fontFamily:"var(--mono)",animation:"pulse 2s infinite"}}>● FASE 0</span>
              <span style={{fontSize:10,color:"var(--text3)",fontFamily:"var(--mono)"}}>DISCOVERY</span>
            </div>
          </div>
          <div style={{padding:"8px 0"}}>
            {NAV.map((n,i)=>(
              <button key={n.id} onClick={()=>{setSec(n.id);setSel(null);setQ("")}}
                style={{display:"flex",alignItems:"center",gap:10,width:"100%",padding:"8px 18px",background:sec===n.id?"rgba(212,160,84,0.06)":"transparent",border:"none",borderLeft:sec===n.id?"2px solid var(--gold)":"2px solid transparent",color:sec===n.id?"var(--text)":"var(--text3)",cursor:"pointer",fontSize:11,fontFamily:"var(--mono)",textAlign:"left",letterSpacing:0.3,transition:"all 0.2s",animationDelay:`${i*40}ms`,animation:"fadeUp 0.4s ease-out both"}}
                onMouseEnter={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--text2)"}}
                onMouseLeave={e=>{if(sec!==n.id)e.currentTarget.style.color="var(--text3)"}}>
                <span style={{width:16,textAlign:"center",fontSize:11,opacity:sec===n.id?1:0.4}}>{n.i}</span>{n.l}
              </button>
            ))}
          </div>
          <div style={{padding:"12px 18px",borderTop:"1px solid var(--border)",position:"absolute",bottom:0,left:0,right:0,background:"rgba(6,6,8,0.95)"}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:4,fontSize:10,fontFamily:"var(--mono)"}}>
              <span style={{color:"var(--text3)"}}>Elementer</span><span style={{color:"var(--gold)",textAlign:"right"}}>{D.meta.elements}</span>
              <span style={{color:"var(--text3)"}}>Verificeret</span><span style={{color:"var(--red)",textAlign:"right"}}>{D.meta.verified}</span>
              <span style={{color:"var(--text3)"}}>Manual</span><span style={{color:"var(--text2)",textAlign:"right"}}>{D.meta.manualFiles} filer</span>
              <span style={{color:"var(--text3)"}}>Bogføring</span><span style={{color:"var(--purple)",textAlign:"right"}}>{D.meta.bogFiles} filer</span>
            </div>
          </div>
        </nav>

        {/* ═══ MAIN ═══ */}
        <main style={{flex:1,marginLeft:210,padding:"20px 32px 60px",maxWidth:1000}}>
          {/* SEARCH */}
          <div style={{display:"flex",gap:8,marginBottom:24,animation:"fadeUp 0.3s ease-out"}}>
            <div style={{flex:1,position:"relative"}}>
              <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Søg: navn, ID, kategori..."
                style={{width:"100%",padding:"10px 14px 10px 36px",background:"var(--bg2)",border:"1px solid var(--border)",color:"var(--text)",fontSize:12,fontFamily:"var(--mono)",outline:"none",borderRadius:2,transition:"border-color 0.2s"}}
                onFocus={e=>e.target.style.borderColor="var(--gold-dim)"} onBlur={e=>e.target.style.borderColor="var(--border)"} />
              <span style={{position:"absolute",left:12,top:"50%",transform:"translateY(-50%)",color:"var(--text3)",fontSize:14}}>⌕</span>
            </div>
            <select value={filt} onChange={e=>setFilt(e.target.value)}
              style={{padding:"10px 14px",background:"var(--bg2)",border:"1px solid var(--border)",color:"var(--text2)",fontSize:11,fontFamily:"var(--mono)",borderRadius:2,cursor:"pointer"}}>
              <option value="ALL">ALLE ({all.length})</option>
              {Object.entries(statusCounts).sort().map(([s,c])=><option key={s} value={s}>{s} ({c})</option>)}
            </select>
          </div>

          {/* SEARCH RESULTS */}
          {q.trim()&&<><SH id="SØG" title={`"${q}"`} count={filtered.length} /><TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Port",r:r=><span style={{color:"var(--cyan)"}}>{r.port||"—"}</span>,nw:1},{h:"Status",r:r=><SB s={r.status} />,nw:1}]} rows={filtered} onRow={setSel} /></>}

          {/* ═══ OVERVIEW ═══ */}
          {sec==="overview"&&!q.trim()&&<>
            <div style={{animation:"fadeUp 0.4s ease-out",marginBottom:28}}>
              <h1 style={{fontSize:26,fontWeight:800,color:"var(--text)",letterSpacing:-0.5}}>KV1NTOS OPERATIONS CENTER</h1>
              <p style={{fontSize:13,color:"var(--text2)",marginTop:4}}>Komplet bogføring af Cirkelline Ecosystem — {D.meta.elements} elementer, {D.meta.manualFiles} manual-filer, {D.meta.bogFiles} bogføringsfiler</p>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))",gap:10,marginBottom:28}}>
              <SC label="ELEMENTER" value={D.meta.elements} sub="kendte" delay={0} />
              <SC label="VERIFICERET" value={D.meta.verified} sub={`af ${D.meta.elements}`} color="var(--red)" delay={60} />
              <SC label="SERVICES" value={D.services.length} sub="core" delay={120} />
              <SC label="PLATFORME" value={D.platforms.length} delay={180} />
              <SC label="AGENTER" value={totalAgents} sub="4 systemer" color="var(--purple)" delay={240} />
              <SC label="INTEGRATIONER" value={D.integrations.length} delay={300} />
              <SC label="CONTAINERE" value={D.containers.length} sub="Docker" color="var(--cyan)" delay={360} />
              <SC label="FEJL" value={D.errors.length} sub="åbne" color="var(--red)" delay={420} />
              <SC label="ODIN REGLER" value={D.rules.length} sub="ufravigelige" color="var(--green)" delay={480} />
              <SC label="MANUAL" value={D.meta.manualFiles} sub={`${D.meta.manualLines.toLocaleString()} linjer`} color="var(--blue)" delay={540} />
              <SC label="BOGFØRING" value={D.meta.bogFiles} sub={`${D.meta.bogLines.toLocaleString()} linjer`} color="var(--purple)" delay={600} />
              <SC label="LEARNINGS" value={D.learnings.length} sub="→ ODIN" color="var(--green)" delay={660} />
            </div>

            {/* FASE PROGRESS */}
            <SH id="FASE" title="GENOPBYGNINGSFASER" count={8} sub="Ingen fase startes før forrige er komplet" />
            <div style={{display:"flex",gap:3,marginBottom:24}}>
              {D.phases.map((p,i)=>(
                <div key={i} style={{flex:1,padding:"10px 8px",background:p.status==="I GANG"?"rgba(212,160,84,0.08)":"var(--bg2)",border:`1px solid ${p.status==="I GANG"?"var(--gold-dim)":"var(--border)"}`,borderRadius:2,textAlign:"center",transition:"all 0.3s",animation:`fadeUp 0.4s ease-out ${i*60}ms both`,cursor:"pointer",position:"relative",overflow:"hidden"}}
                  onClick={()=>setSel(p)}
                  onMouseEnter={e=>{e.currentTarget.style.borderColor="var(--gold-dim)";e.currentTarget.style.transform="translateY(-2px)"}}
                  onMouseLeave={e=>{e.currentTarget.style.borderColor=p.status==="I GANG"?"var(--gold-dim)":"var(--border)";e.currentTarget.style.transform="translateY(0)"}}>
                  {p.status==="I GANG"&&<div style={{position:"absolute",top:0,left:0,right:0,height:2,background:"var(--gold)",animation:"glow 2s infinite"}} />}
                  <div style={{fontFamily:"var(--mono)",fontSize:16,fontWeight:700,color:p.status==="I GANG"?"var(--gold)":p.status==="KOMPLET"?"var(--green)":"var(--text3)"}}>{p.id}</div>
                  <div style={{fontSize:9,color:p.status==="I GANG"?"var(--text)":"var(--text3)",marginTop:2,fontFamily:"var(--mono)",letterSpacing:0.5}}>{p.name}</div>
                </div>
              ))}
            </div>

            {/* QUICK REF: BOGFØRING */}
            <SH id="A-J" title="BOGFØRINGSMAPPE KRYDSREF" count={`${D.bogforing.reduce((s,b)=>s+b.files,0)} filer`} sub={`${D.bogforing.reduce((s,b)=>s+b.lines,0).toLocaleString()} linjer total`} />
            <TBL cols={[
              {h:"Kat",r:r=><span style={{fontFamily:"var(--mono)",fontWeight:700,color:"var(--gold)",fontSize:15}}>{r.c}</span>,nw:1},
              {h:"Navn",k:"name",nw:1},{h:"Filer",k:"files",nw:1},
              {h:"Linjer",r:r=><span style={{fontFamily:"var(--mono)"}}>{r.lines.toLocaleString()}</span>,nw:1},
              {h:"→ Manual",r:r=><span style={{color:"var(--cyan)",fontSize:11}}>{r.map}</span>},
              {h:"Beskrivelse",k:"desc",mw:200},
            ]} rows={D.bogforing} />
          </>}

          {/* ═══ PHASES DETAIL ═══ */}
          {sec==="phases"&&!q.trim()&&<>
            <SH id="FASER" title="GENOPBYGNINGSFASER" count={8} sub="7-faset plan: Discovery → Oprydning → Fundament → Observe → AI → ODIN → Integration → Projekter" />
            {D.phases.map((p,i)=>(
              <div key={i} onClick={()=>setSel(p)} style={{display:"grid",gridTemplateColumns:"50px 140px 1fr 130px",gap:12,padding:"14px 16px",background:p.status==="I GANG"?"rgba(212,160,84,0.04)":"transparent",borderLeft:p.status==="I GANG"?"2px solid var(--gold)":"2px solid transparent",alignItems:"center",cursor:"pointer",transition:"all 0.2s",animation:`fadeUp 0.3s ease-out ${i*50}ms both`,borderBottom:"1px solid var(--border)"}}
                onMouseEnter={e=>e.currentTarget.style.background="rgba(212,160,84,0.03)"}
                onMouseLeave={e=>e.currentTarget.style.background=p.status==="I GANG"?"rgba(212,160,84,0.04)":"transparent"}>
                <span style={{fontFamily:"var(--mono)",fontSize:18,fontWeight:800,color:p.status==="I GANG"?"var(--gold)":"var(--text3)"}}>F{p.id}</span>
                <span style={{fontSize:14,fontWeight:600,color:p.status==="I GANG"?"var(--text)":"var(--text2)"}}>{p.name}</span>
                <div><div style={{fontSize:12,color:"var(--text2)"}}>{p.desc}</div><div style={{fontSize:10,color:"var(--text3)",marginTop:2}}>Krav: {p.deps}</div></div>
                <SB s={p.status} />
              </div>
            ))}
          </>}

          {/* ═══ SERVICES ═══ */}
          {sec==="services"&&!q.trim()&&<><SH id="SVC" title="CORE SERVICES" count={D.services.length} sub="8 services: Docker, Prometheus, Loki, Grafana, Tempo, Alertmanager, n8n, Ollama" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Port",r:r=><span style={{color:"var(--cyan)",fontWeight:600}}>{r.port}</span>,nw:1},{h:"Kat",k:"cat",nw:1},{h:"Fase",r:r=><span>F{r.phase}</span>,nw:1},{h:"Status",r:r=><SB s={r.status} />,nw:1},{h:"Bog",r:r=>(r.bog||[]).join(", ")||"—"}]} rows={D.services} onRow={setSel} /></>}

          {/* ═══ PLATFORMS ═══ */}
          {sec==="platforms"&&!q.trim()&&<><SH id="PLT" title="PLATFORME" count={D.platforms.length} sub="4 aktive + 3 kommende: BØRNESKABER, Three Realms, Gaming" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Port",r:r=>r.port?<span style={{color:"var(--cyan)"}}>{r.port}</span>:"—",nw:1},{h:"Database",r:r=>r.db||"—"},{h:"Status",r:r=><SB s={r.status} />,nw:1},{h:"Bog",r:r=>(r.bog||[]).join(", ")||"—"}]} rows={D.platforms} onRow={setSel} /></>}

          {/* ═══ APIS ═══ */}
          {sec==="apis"&&!q.trim()&&<><SH id="API" title="EKSTERNE API'ER" count={D.apis.length} sub="Claude (privat+firma) + Gemini Fleet Router" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Provider",k:"provider",nw:1},{h:"Modeller",r:r=><span style={{color:"var(--purple)",fontSize:11}}>{r.models.join(", ")}</span>},{h:"Limit",r:r=><span style={{color:"var(--gold)"}}>{r.limit}</span>},{h:"Status",r:r=><SB s={r.status} />,nw:1}]} rows={D.apis} onRow={setSel} /></>}

          {/* ═══ INTEGRATIONS ═══ */}
          {sec==="integrations"&&!q.trim()&&<><SH id="INT" title="INTEGRATIONS-SYSTEMER" count={D.integrations.length} sub="11 systemer: Fleet Manager, Orchestrator, Swarm, Evolved-serien, Brain, Coordinator, Dashboard, Message Bus" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Port",r:r=><span style={{color:"var(--cyan)"}}>{r.port}</span>,nw:1},{h:"Fase",r:r=>`F${r.phase}`,nw:1},{h:"Status",r:r=><SB s={r.status} />,nw:1}]} rows={D.integrations} onRow={setSel} /></>}

          {/* ═══ AGENTS ═══ */}
          {sec==="agents"&&!q.trim()&&<><SH id="AGT" title="AGENTER" count={totalAgents} sub={`4 systemer: Kommandør (21), ELLE (122), CKC (5), Cosmic (9)`} />
            {D.agents.map((g,i)=>(
              <div key={g.id} onClick={()=>setSel(g)} style={{marginBottom:12,padding:"18px 20px",background:"var(--bg2)",border:"1px solid var(--border)",cursor:"pointer",transition:"all 0.25s",borderRadius:2,animation:`fadeUp 0.4s ease-out ${i*80}ms both`,position:"relative",overflow:"hidden"}}
                onMouseEnter={e=>{e.currentTarget.style.borderColor="var(--gold-dim)";e.currentTarget.style.transform="translateY(-2px)"}}
                onMouseLeave={e=>{e.currentTarget.style.borderColor="var(--border)";e.currentTarget.style.transform="translateY(0)"}}>
                <div style={{position:"absolute",top:0,left:0,width:`${(g.count/totalAgents)*100}%`,height:2,background:`linear-gradient(90deg,var(--gold),var(--purple))`,opacity:0.6}} />
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
                  <div style={{display:"flex",alignItems:"center",gap:10}}>
                    <span style={{fontFamily:"var(--mono)",fontSize:11,color:"var(--gold)",fontWeight:600}}>{g.id}</span>
                    <span style={{fontSize:16,fontWeight:600,color:"var(--text)"}}>{g.name}</span>
                    <span style={{fontSize:11,color:"var(--text3)"}}>{g.reg?"REGISTRERET":"AFVENTER REG."}</span>
                  </div>
                  <span style={{fontFamily:"var(--mono)",fontSize:28,fontWeight:800,color:"var(--purple)"}}>{g.count}</span>
                </div>
                <div style={{fontSize:11,color:"var(--text3)",fontFamily:"var(--mono)"}}>System: {g.system} | Bog: {g.bog.join(", ")}</div>
                {g.sub.length>0&&<div style={{marginTop:10,display:"flex",gap:6,flexWrap:"wrap"}}>
                  {g.sub.map((s,j)=><span key={j} style={{padding:"4px 10px",background:"var(--bg3)",border:"1px solid var(--border)",fontSize:11,color:"var(--text2)",fontFamily:"var(--mono)",borderRadius:2}}>{s.n}: <span style={{color:"var(--purple)",fontWeight:600}}>{s.c}</span></span>)}
                </div>}
              </div>
            ))}
          </>}

          {/* ═══ CONTAINERS ═══ */}
          {sec==="containers"&&!q.trim()&&<><SH id="CTR" title="DOCKER CONTAINERE" count={D.containers.length} sub="Kendte containere — scan vil afsløre alle 18+" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Container",k:"name"},{h:"Image",k:"image"},{h:"Port",r:r=><span style={{color:"var(--cyan)"}}>{r.port}</span>,nw:1},{h:"Bog",r:r=>(r.bog||[]).join(", ")}]} rows={D.containers} onRow={setSel} /></>}

          {/* ═══ DATABASES ═══ */}
          {sec==="databases"&&!q.trim()&&<><SH id="DB" title="DATABASER" count={D.databases.length} sub="PostgreSQL + Redis — scan viser alle" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Navn",k:"name"},{h:"Port",r:r=>r.port?<span style={{color:"var(--cyan)"}}>{r.port}</span>:"—",nw:1},{h:"Platform",k:"plt"},{h:"Status",r:r=><SB s={r.status} />,nw:1},{h:"Bog",r:r=>(r.bog||[]).join(", ")}]} rows={D.databases} onRow={setSel} /></>}

          {/* ═══ MANUAL FILES ═══ */}
          {sec==="manual"&&!q.trim()&&<><SH id="MAN" title="OPERATIONS-MANUAL FILER" count={`${D.meta.manualFiles} filer`} sub={`${D.meta.manualLines.toLocaleString()} linjer i 8 mapper`} />
            {D.manualDirs.map((dir,di)=>(
              <div key={dir.dir} style={{marginBottom:16,animation:`fadeUp 0.4s ease-out ${di*60}ms both`}}>
                <div style={{display:"flex",alignItems:"baseline",gap:10,padding:"8px 0",borderBottom:"1px solid var(--border)",marginBottom:6}}>
                  <span style={{fontFamily:"var(--mono)",fontSize:12,color:"var(--gold)",fontWeight:600,letterSpacing:1}}>{dir.dir}/</span>
                  <span style={{fontSize:13,fontWeight:600,color:"var(--text)"}}>{dir.name}</span>
                  <span style={{fontSize:10,color:"var(--text3)",fontFamily:"var(--mono)"}}>{dir.files.length} filer, {dir.files.reduce((s,f)=>s+f.l,0)} linjer</span>
                </div>
                {dir.files.map((f,fi)=>(
                  <div key={fi} style={{display:"grid",gridTemplateColumns:"260px 60px 1fr",gap:8,padding:"5px 12px",fontSize:12,fontFamily:"var(--mono)",borderBottom:"1px solid rgba(26,26,36,0.3)",alignItems:"center"}}
                    onMouseEnter={e=>e.currentTarget.style.background="rgba(212,160,84,0.03)"}
                    onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                    <span style={{color:"var(--cyan)"}}>{f.f}</span>
                    <span style={{color:"var(--text3)",textAlign:"right"}}>{f.l}L</span>
                    <span style={{color:"var(--text2)",fontSize:11}}>{f.t||""}</span>
                  </div>
                ))}
              </div>
            ))}
          </>}

          {/* ═══ BOGFORING ═══ */}
          {sec==="bogforing"&&!q.trim()&&<><SH id="A-J" title="BOGFØRINGSMAPPE (A-J) KRYDSHENVISNINGER" count={`${D.bogforing.reduce((s,b)=>s+b.files,0)} filer`} sub={`${D.bogforing.reduce((s,b)=>s+b.lines,0).toLocaleString()} linjer — komplet system-dokumentation`} />
            <TBL cols={[
              {h:"Kat",r:r=><span style={{fontFamily:"var(--mono)",fontWeight:800,color:"var(--gold)",fontSize:16}}>{r.c}</span>,nw:1},
              {h:"Navn",k:"name",nw:1},{h:"Filer",k:"files",nw:1},
              {h:"Linjer",r:r=><span style={{fontFamily:"var(--mono)"}}>{r.lines.toLocaleString()}</span>,nw:1},
              {h:"→ Manual",r:r=><span style={{color:"var(--cyan)"}}>{r.map}</span>},{h:"Beskrivelse",k:"desc"},
            ]} rows={D.bogforing} />
            <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginTop:16}}>
              <SC label="KATEGORIER" value={10} color="var(--gold)" /><SC label="TOTAL FILER" value={D.bogforing.reduce((s,b)=>s+b.files,0)} /><SC label="TOTAL LINJER" value={D.bogforing.reduce((s,b)=>s+b.lines,0)} color="var(--purple)" />
            </div>
            <div style={{marginTop:16,padding:16,background:"var(--bg2)",border:"1px solid var(--border)",borderRadius:2,fontSize:12,color:"var(--text2)"}}>
              <strong style={{color:"var(--gold)"}}>PRINCIP:</strong> Bogføringsmappen = hvad systemet VAR og SKAL være. Manualen = hvordan vi VERIFICERER og GENOPBYGGER det.
            </div>
          </>}

          {/* ═══ ERRORS ═══ */}
          {sec==="errors"&&!q.trim()&&<><SH id="ERR" title="KENDTE FEJL" count={D.errors.length} sub="Åbne fejl der kræver handling" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Kilde",k:"src",nw:1},{h:"Beskrivelse",k:"desc"},{h:"Alvorlighed",r:r=><SB s={r.sev} />,nw:1},{h:"Status",r:r=><SB s={r.status} />,nw:1},{h:"Fix",k:"fix"}]} rows={D.errors} onRow={setSel} /></>}

          {/* ═══ LEARNINGS ═══ */}
          {sec==="learnings"&&!q.trim()&&<><SH id="LRN" title="LEARNINGS → ODIN" count={D.learnings.length} sub="Hvad vi har lært — hardcodes i ODIN regler og videnbase" />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Område",k:"a",nw:1},{h:"Learning",k:"l"},{h:"→ ODIN",r:r=><span style={{color:"var(--purple)",fontSize:10}}>{r.o}</span>}]} rows={D.learnings} onRow={setSel} /></>}

          {/* ═══ RULES ═══ */}
          {sec==="rules"&&!q.trim()&&<><SH id="ODIN" title="ODIN REGLER (UFRAVIGELIGE)" count={D.rules.length} sub="Disse regler brydes ALDRIG. Hverken af agenter, HQ, eller Opus." />
            <TBL cols={[{h:"ID",k:"id",nw:1},{h:"Regel",k:"r"},{h:"Kategori",k:"c",nw:1}]} rows={D.rules} />
            <div style={{marginTop:12,padding:14,background:"rgba(248,113,113,0.05)",border:"1px solid rgba(248,113,113,0.15)",borderRadius:2,fontSize:12,color:"var(--red)",fontWeight:500}}>
              ⚠ UFRAVIGELIGE — ingen undtagelser, ingen omgåelse, ingen forhandling
            </div>
          </>}
        </main>
      </div>

      {/* DETAIL PANEL */}
      <Detail item={sel} onClose={()=>setSel(null)} />
    </>
  );
}
