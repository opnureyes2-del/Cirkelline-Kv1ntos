# Cleanup Rutine Template

**Formål:** Systematisk oprydning efter hver 3. CKC audit

---

## Cleanup Tjekliste

### 1. Midlertidige Filer
- [ ] `__pycache__/` mapper
- [ ] `.pyc` filer
- [ ] `*.log` filer (tomme)
- [ ] `.DS_Store` filer (macOS)
- [ ] `node_modules/` (hvis ikke nødvendige)
- [ ] `.venv/` backup kopier

### 2. Duplikater
- [ ] Identificer identiske filer på tværs af versioner
- [ ] Sammenlign snapshot versioner
- [ ] Marker kandidater til sletning

### 3. Forældede Filer
- [ ] Gammel dokumentation
- [ ] Ubrugte konfigurationsfiler
- [ ] Forældede migrations

### 4. Mappestruktur
- [ ] Verificer alle mapper har formål
- [ ] Identificer tomme mapper
- [ ] Tjek for misplacerede filer

### 5. Log Output
- [ ] Notér alle slettede filer
- [ ] Dokumenter beslutninger
- [ ] Opdater cleanup log

---

## Cleanup Kommandoer

```bash
# Find __pycache__ mapper
find . -type d -name "__pycache__" -exec echo "DELETE: {}" \;

# Find tomme filer
find . -type f -empty -exec echo "EMPTY: {}" \;

# Find .log filer
find . -name "*.log" -size 0 -exec echo "EMPTY LOG: {}" \;

# Find duplikater (md5sum)
find . -type f -exec md5sum {} \; | sort | uniq -d -w32
```

---

## Beslutningskriterier

| Fil Type | Handling | Begrundelse |
|----------|----------|-------------|
| `__pycache__/` | SLET | Kan regenereres |
| Tom `.log` | SLET | Ingen data |
| Snapshot duplikat | EVALUER | Kan være backup |
| Gammel version | ARKIVER | Historisk værdi |
| Ubrugt config | EVALUER | Mulig fremtidig brug |

---

**Template Version:** 1.0
**Oprettet:** 2025-12-14
