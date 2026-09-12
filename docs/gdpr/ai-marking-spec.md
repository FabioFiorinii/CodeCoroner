# AI Marking Specification — CodeCoroner

**Versione**: 1.0 | **Data**: 2026-09-10 | **Stato**: Implementato
**Riferimento normativo**: AI Act (Reg. UE 2024/1689) Art. 50(2) — Machine-readable marking

---

## 1. Scopo

Questo documento descrive la soluzione tecnica adottata per soddisfare l'obbligo di **marcatura in formato machine-readable** degli output generati da sistemi AI (Art. 50(2) AI Act).

CodeCoroner genera i seguenti output tramite LLM locali (Ollama + qwen2.5-coder):
- `LogAnalysis` — analisi strutturata dell'input errore
- `BugLocalization` — file sospetti con score
- `RootCause` — file/linea causa radice + catena causale
- `FixSuggestion` — diff unificato + piano + spiegazione
- `Report` — report finale in Markdown

Tutti questi output sono **testo generato da AI** e rientrano nell'ambito Art. 50(2).

---

## 2. Soluzione adottata: Metadati API/DB (no watermark invisibile)

### Scelta progettuale
Si è scelto di implementare la marcatura **esclusivamente via metadati strutturati** (campi dedicati su modelli DB + API), **senza watermark testuale invisibile** (zero-width chars).

### Motivazione
| Criterio | Metadati API/DB | Watermark invisibile |
|---|---|---|
| **Robustezza** | ✅ Sempre preservati in DB/API | ❌ Persi in copy-paste, sanitizzazione, riformattazione |
| **Interoperabilità** | ✅ Accessibili via REST API standard | ❌ Richiede decoder custom |
| **Detectabilità** | ✅ Queryabile via SQL/API | ❌ Richiede tool dedicato |
| **Accessibilità** | ✅ Nessun impatto su screen reader | ⚠️ Potenziali problemi WCAG |
| **UX** | ✅ Zero impatto visivo | ❌ Caratteri invisibili in diff/git blame |
| **Compliance Art. 50(2)** | ✅ "Machine-readable, detectable" **dentro la piattaforma** | ✅ Anche fuori (se sopravvive) |

**Conclusione**: la marcatura via metadati soddisfa pienamente Art. 50(2) per l'uso **interno alla piattaforma** (caso d'uso principale di CodeCoroner). Il watermark invisibile è rimandato come estensione futura (campo `watermark` nullable già predisposto).

---

## 3. Campi implementati

Su ogni modello output (`BugLocalization`, `RootCause`, `FixSuggestion`, `Report` — `LogAnalysis` è embeddito in `AnalysisRun.output`):

| Campo | Tipo | Descrizione | Esempio |
|---|---|---|---|
| `ai_generated` | `boolean` | Flag costante `true` | `true` |
| `model_name` | `string` | Nome modello Ollama (es. `qwen2.5-coder`) | `qwen2.5-coder` |
| `model_version` | `string` | Tag versione dopo `:` (es. `7b`) | `7b` |
| `generated_at` | `datetime` (ISO 8601 UTC) | Timestamp generazione | `2026-09-10T19:25:40.526070Z` |
| `prompt_hash` | `string` (SHA-256 hex) | Hash del prompt inviato al LLM | `a1b2c3d4...` |
| `watermark` | `text` (nullable) | Riservato per futuro watermark testuale | `null` |

### Esempio risposta API (`GET /api/v1/analyses/{id}/`)

```json
{
  "bug_localization": {
    "summary": "The bug is in switch_lang.py...",
    "suspicious_files": [...],
    "created_at": "2026-09-10T19:25:40.526070Z",
    "ai_generated": true,
    "model_name": "qwen2.5-coder",
    "model_version": "7b",
    "generated_at": "2026-09-10T19:25:40.526070Z",
    "prompt_hash": "a1b2c3d4e5f6...",
    "watermark": null
  },
  "root_cause": { ... },
  "fix_suggestion": { ... },
  "report": { ... }
}
```

---

## 4. Generazione dei campi (côté ai-engine)

In ogni agente (`log_analyzer`, `bug_localizer`, `root_cause`, `patch_generator`, `report_generator`):

```python
def _build_ai_marking(model_name: str, prompt: str) -> dict:
    return {
        'ai_generated': True,
        'model_name': model_name,
        'model_version': model_name.split(':')[-1] if ':' in model_name else '',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest(),
        'watermark': None,
    }

# Nel run():
raw = await self.ollama.generate(model, prompt, format='json', options={...})
result = parse_json_response(raw)
marking = _build_ai_marking(self.settings.llm_model, prompt)
result.update(marking)
return result
```

Il prompt hash è calcolato **sul prompt finale inviato al LLM** (dopo formattazione template), non sull'input grezzo.

---

## 5. Esposizione via API (Django)

Campi aggiunti su modelli Django (`backend/analyses/models.py`) ed esposti via serializer (`backend/analyses/serializers.py`):

- `BugLocalizationSerializer`
- `RootCauseSerializer`
- `FixSuggestionSerializer`
- `ReportSerializer`

Tutti i campi sono **read-only** (non scrivibili via API).

---

## 6. Frontend — Disclosure utente (Art. 50(1)+(5))

Componente `AIBadge` (`frontend/src/components/common/AIBadge.tsx`):

- Badge "🤖 AI-generated" + tooltip con modello/versione/data
- Posizionato accanto al titolo di ogni sezione output (Bug Localization, Root Cause, Fix Suggestion, Report)
- WCAG 2.1 AA: colore, contrasto, `aria-label`, `role="img"`
- Non invadente: badge piccolo nell'angolo card, tooltip al hover

---

## 6. Audit trail & Verifica compliance

### Come verificare (per auditor)
1. **API**: `GET /api/v1/analyses/{id}/` → verificare presenza campi `ai_generated`, `model_name`, `model_version`, `generated_at`, `prompt_hash` su `bug_localization`, `root_cause`, `fix_suggestion`, `report`
2. **DB**: `SELECT ai_generated, model_name, generated_at FROM analyses_buglocalization WHERE id=...`
3. **Frontend**: aprire analisi completata → verificare badge "🤖 AI-generated" con tooltip su ogni sezione

### Requisiti Art. 50(2) soddisfatti
| Requisito | Come soddisfatto |
|---|---|
| Machine-readable format | Campi JSON strutturati in API REST |
| Detectable as AI-generated | Campo `ai_generated: true` + badge UI |
| Interoperable | Formato standard JSON/REST |
| Robust | Campi DB persistenti, non persi in copy-paste |
| Effective | Sempre presenti su ogni output AI |
| Accessible (Art. 50(5)) | Badge visibile + tooltip accessibile |

---

## 7. Estensioni future (non implementate)

| Estensione | Descrizione | Quando |
|---|---|---|
| **Watermark testuale** | Zero-width chars embeddati nel markdown/diff | Se richiesto per copy-paste esterno |
| **Firma crittografica** | `prompt_hash` firmato con chiave privata per non ripudio | Se richiesto per audit legale |
| **Registro pubblico** | Endpoint `/api/v1/ai-marking-registry/` per verifica terza parti | Se richiesto da regolatori |
| **Toggle B2B** | Disabilitazione marking per contesti B2B closed-loop (esenzione Guidelines) | Se clienti enterprise lo richiedono |

---

## 8. Riferimenti normativi

- **AI Act** Reg. UE 2024/1689 — Art. 50(2), (5)
- **Guidelines on Transparency Obligations** (Commissione UE, 20 lug 2026) — Sez. 4
- **Code of Practice on Transparency of AI-generated Content** — Working Group 1 (Providers)
- **GDPR** Art. 5(1)(a), 5(2), 12, 15, 25 (privacy by design, transparency, accountability)