# CLA E2E Test Plan

## Version 0.1.0 | December 2024

---

## 1. Test Kategorier

### 1.1 Funktionelle Tests

| Test ID | Beskrivelse | Forventet Resultat |
|---------|-------------|-------------------|
| F001 | Start applikation | App starter uden fejl |
| F002 | Indstillinger gemmes | Settings persisteres lokalt |
| F003 | Resource monitoring | CPU/RAM metrics opdateres |
| F004 | Embedding generation | Returner 384-dim vektor |
| F005 | Transskription (Whisper) | Returnerer tekst fra audio |
| F006 | OCR (Tesseract) | Returnerer tekst fra billede |
| F007 | Sync med CKC | Data synkroniseres korrekt |
| F008 | Offline mode | App fungerer uden netværk |

### 1.2 UI Tests

| Test ID | Beskrivelse | Forventet Resultat |
|---------|-------------|-------------------|
| U001 | Vindue åbner | 400x600 vindue vises |
| U002 | Min-størrelse respekteres | Kan ikke gå under 320x480 |
| U003 | System tray | Ikon vises i system tray |
| U004 | Indstillinger panel | Settings UI loader |
| U005 | Status indikator | Viser aktuel status |

### 1.3 Integration Tests

| Test ID | Beskrivelse | Forventet Resultat |
|---------|-------------|-------------------|
| I001 | CKC API connection | Succesfuld forbindelse |
| I002 | Token validation | JWT valideres korrekt |
| I003 | Data sync upload | Lokale data sendes til CKC |
| I004 | Data sync download | CKC data modtages lokalt |
| I005 | Model download | ONNX modeller downloades |

### 1.4 Performance Tests

| Test ID | Beskrivelse | Forventet Resultat |
|---------|-------------|-------------------|
| P001 | Startup tid | < 3 sekunder |
| P002 | Embedding latency | < 100ms |
| P003 | Idle CPU brug | < 2% |
| P004 | Memory footprint | < 300MB baseline |
| P005 | Batch inference | 100 tekster < 10s |

---

## 2. Sikkerhedstest Strategi

### 2.1 Data Sikkerhed

| Test ID | Beskrivelse | Verifikation |
|---------|-------------|--------------|
| S001 | Lokal kryptering | AES-256-GCM verificeret |
| S002 | Key derivation | Argon2 med korrekte parametre |
| S003 | Token opbevaring | Krypteret i secure storage |
| S004 | Memory clearing | Sensitive data nulstilles |

### 2.2 Netværk Sikkerhed

| Test ID | Beskrivelse | Verifikation |
|---------|-------------|--------------|
| S005 | HTTPS enforcement | Kun TLS 1.3 tilladt |
| S006 | Certificate pinning | CKC cert valideres |
| S007 | CSP headers | XSS beskyttelse aktiv |
| S008 | Rate limiting | Burst beskyttelse |

### 2.3 Input Validation

| Test ID | Beskrivelse | Verifikation |
|---------|-------------|--------------|
| S009 | Path traversal | Blokeret |
| S010 | SQL injection | N/A (ingen SQL) |
| S011 | Command injection | Blokeret |
| S012 | XSS i content | Sanitized |

---

## 3. Test Udførelse

### 3.1 Automatiserede Tests

```bash
# Kør unit tests
cargo test

# Kør integration tests
cargo test --features integration

# Performance benchmarks
cargo bench
```

### 3.2 Manuel Test Procedure

1. **Build release**: `cargo build --release`
2. **Start app**: `./target/release/cirkelline-local-agent`
3. **Verificer startup log**
4. **Test hver funktion manuelt**
5. **Dokumenter resultater**

### 3.3 Test Miljø

| Krav | Specifikation |
|------|---------------|
| OS | Linux (Ubuntu 22.04+), macOS 10.15+, Windows 10+ |
| RAM | Min 4GB |
| Disk | Min 500MB ledig |
| CPU | x86_64 med SSE4.2 |

---

## 4. Test Rapportering

### 4.1 Rapport Format

```
Test ID: FXXX
Dato: YYYY-MM-DD
Tester: [Navn]
Status: PASS/FAIL
Detaljer: [Beskrivelse]
Screenshots: [Links]
```

### 4.2 Bug Rapportering

- Kritisk (P1): System crash, data tab
- Høj (P2): Funktionsfejl
- Medium (P3): UI fejl
- Lav (P4): Kosmetisk

---

## 5. Acceptance Criteria

### 5.1 Release Readiness

- [ ] Alle F-tests PASS
- [ ] Alle S-tests PASS
- [ ] P001-P004 PASS
- [ ] Ingen P1/P2 bugs
- [ ] Security audit gennemført

### 5.2 Sign-off

| Rolle | Navn | Dato | Signatur |
|-------|------|------|----------|
| Dev Lead | | | |
| QA Lead | | | |
| Security | | | |
