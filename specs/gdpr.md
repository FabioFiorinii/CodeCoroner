# Piano di implementazione GDPR + AI Act

Stato: **piano** — nessuna implementazione fatta. Copre tutti i punti mancanti identificati nell'audit (item 9) per rendere CodeCoroner compliant prima di un eventuale lancio pubblico multi-tenant, inclusi gli obblighi **AI Act (Reg. UE 2024/1689) Art. 50** in vigore dal 2 agosto 2026 (grace period Art. 50(2) marking fino al 2 dicembre 2026).

## Perché GDPR si applica

CodeCoroner è un SaaS (monorepo, multi-tenant) che tratterà dati personali di utenti (account) e, potenzialmente, dati dei loro repository/errori. Il titolare del trattamento è chi gestisce l'istanza. GDPR (Reg. UE 2016/679) si applica perché trattiamo dati di soggetti nell'UE.

**Rasserenamento sul grosso rischio AI**: gli LLM girano **in locale** via Ollama, dentro il nostro container. Nessun dato (nemmeno il codice dei clienti) viene inviato a terze parti (no OpenAI/Anthropic). Questo elimina la categoria più delicata di "processor" e i trasferimenti internazionali per l'inferenza.

## Inventario dati attuale (data map)

| Dato | Dove | Retention | Base giuridica candidata |
|---|---|---|---|
| Account: email, nome, hash password, date | `accounts.User` | Durata account | Contratto/legittimo interesse |
| Token JWT / refresh (hash) | `token_blacklist`, `accounts` | Finchè attivi/revocati | Contratto |
| Progetti, repo metadata, analisi, RCA, fix, report | `projects`, `repositories`, `analyses`, ... | `ANALYSIS_RETENTION_DAYS=90` (purge settimanale via Celery beat) | Contratto/legittimo interesse |
| Chunk + embedding del codice | `CodeChunk`, `ChunkEmbedding` | Ciclo di vita del repo | Contratto |
| Webhook secrets (cifrati Fernet) | `webhooks` | Ciclo di vita del webhook | Contratto |
| Log strutturati JSON | file con rotazione giornaliera | Da definire (vedi P2-4) | Legittimo interesse (sicurezza) |
| Tabelle axes (tentativi di login) | `axes_accessattempt` | Da definire (vedi P2-4) | Legittimo interesse (sicurezza) |
| Output AI (report, fix, RCA, localizzazione, log analysis) | `Report`, `FixSuggestion`, `BugLocalization`, `RootCause`, `LogAnalysis` | `ANALYSIS_RETENTION_DAYS=90` | Contratto/legittimo interesse |

## Punti mancanti e piano

Priorità: **P0** = prerequisito al lancio / scadenza AI Act 2 dic 2026, **P1** = diritti utente, **P2** = compliance operativa.

---

### P0 — Prerequisiti lancio + AI Act (scadenza 2 dic 2026)

#### P0-1 · Base giuridica e consenso (Art. 6, 7 GDPR)
- **Obiettivo**: per ogni finalità di trattamento, base giuridica documentata. Per il processing di errori/repo dei clienti serve un **contratto/ToS** esplicito (Art. 6(1)(b)); per newsletter/marketing, consenso separato (Art. 7) con opt-in e revoca.
- **Code**: nessuna modifica per ora (a parte eventuale flag `consent_marketing` sul `User`).
- **Processo**: redigere ToS + privacy policy (P0-2).
- **Effort**: M.

#### P0-2 · Privacy policy + Termini di servizio (include AI-4)
- **Obiettivo**: documenti pubblici (es. `/legal/privacy`, `/legal/terms`) che dichiarino: chi è il titolare, quali dati, per quale finalità, retention, diritti utente, come esercitarli, chi sono gli eventuali processor, contatti. **Sezione dedicata "Elaborazione AI"**: base giuridica (Art. 6(1)(b)), modelli locali (qwen2.5-coder, nomic-embed-text), finalità (analisi bug), retention output AI (90gg), diritti utente su output AI, riferimento Art. 50 AI Act.
- **Code**: due pagine statiche nel frontend + link nel footer; campo `accepted_tos_at` / `accepted_privacy_at` sul `User` (timestamp, per prova di consenso al contratto).
- **Processo**: testo legale (revisione avvocato), data di ultimo aggiornamento, versioning.
- **Effort**: L (più tempo legale che codice).

#### P0-3 · Registro dei trattamenti (Art. 30) (include integrazione AI)
- **Obiettivo**: documento (anche interno) che elenca ogni trattamento: finalità, categorie di dati, destinatari, trasferimenti, retention, misure di sicurezza. **Aggiungere riga**: "Elaborazione AI per analisi bug" — categorie: error_context, codice sorgente chunk, output AI; finalità: RCA/fix/report; base giuridica: Art. 6(1)(b); retention: 90gg; destinatari: nessuno (locale).
- **Code**: nessuno. **Processo**: compilare un template (es. `docs/gdpr/registro-trattamenti.md`).
- **Effort**: S-M.

#### P0-4 · Processor / accordi con fornitori (Art. 28)
- **Obiettivo**: mappare e contrattualizzare i sub-processor. Attualmente: host (dove gira), eventuali servizi cloud (MinIO, Postgres se gestito), no LLM esterni. Ogni processor deve avere un Data Processing Agreement (DPA).
- **Code**: nessuno. **Processo**: verifica fornitori + DPA firmati.
- **Effort**: S (essendo stack self-hosted, è poco).

#### AI-1 · UI Disclosure (Art. 50(1)+(5) AI Act)
- **Obiettivo**: badge "🤖 AI-generated" + tooltip su card Report, FixSuggestion, BugLocalization, RootCause, LogAnalysis. Non invadente, WCAG 2.1 AA. Disclosure al primo contatto/visibilità.
- **Code**: componente `AIBadge` in `frontend/src/components/`, integrazione pagine Report/Fix/RCA/LogAnalysis.
- **Effort**: M.

#### AI-2 · Machine-readable marking — metadati (Art. 50(2) AI Act)
- **Obiettivo**: campi `ai_generated` (bool), `model_name`, `model_version`, `generated_at`, `prompt_hash` su `Report`, `FixSuggestion`, `BugLocalization`, `RootCause`, `LogAnalysis`. Popolati da ai-engine, esposti via serializer. **Nessun watermark invisibile** per ora; predisporre campo `watermark` nullable per eventuale futura estensione.
- **Code**: 
  - `backend/analyses/models.py` — aggiunta campi
  - `ai-engine/agents/report_generator/generator.py`, `patch_generator/generator.py`, `bug_localizer/localizer.py`, `root_cause/rca_agent.py`, `log_analyzer/analyzer.py` — popolamento campi
  - `backend/analyses/serializers.py` — esposizione API
- **Effort**: M.

#### AI-3 · Documentazione tecnica marking (Art. 50(2) AI Act)
- **Obiettivo**: `docs/gdpr/ai-marking-spec.md` — descrive campi, formato, detection method, per audit.
- **Code**: nessuno. **Processo**: scrittura documento.
- **Effort**: S.

#### AI-5 · Valutazione high-risk AI (Allegato III AI Act)
- **Obiettivo**: documento `docs/gdpr/high-risk-assessment.md`: CodeCoroner **NON** ricade in sistemi ad alto rischio (non medical device, non recruitment, non credit scoring, non law enforcement, non critical infrastructure, non biometric identification, non education/vocational training, non essential services, non administration of justice).
- **Code**: nessuno. **Processo**: scrittura documento.
- **Effort**: S.

---

### P1 — Diritti utente

#### P1-1 · Diritto di accesso e portabilità — endpoint export (Art. 15, 20)
- **Obiettivo**: l'utente scarica tutti i propri dati in formato leggibile e riutilizzabile (JSON + CSV). **Include output AI** (Report, FixSuggestion, BugLocalization, RootCause, LogAnalysis con i nuovi campi metadati).
- **Code**:
  - `GET /api/v1/me/export` in `accounts/views.py`: raccoglie profilo + progetti + repo + analisi + report + output AI (i dati dell'utente, non quelli di altri tenant — riusare i filtri di isolamento già esistenti).
  - Generazione **asincrona** (Celery task, come la pipeline) per dataset grandi: l'endpoint restituisce un job id; download via link temporaneo firmato.
  - Test: `accounts/tests/test_export.py` (contenuto corretto, isolamento tenant, formato).
- **Effort**: L.

#### P1-2 · Diritto alla cancellazione — eliminazione account (Art. 17)
- **Obiettivo**: `DELETE /api/v1/me` con hard-delete a cascata di tutti i dati collegati (progetti, repo, analisi, webhook, embedding, **output AI**).
- **Code**:
  - Endpoint `DELETE /api/v1/me` in `accounts/views.py`; distacco anche i repo dal volume `repo_cache` (via task asincrona `purge_user_repos`).
  - **Conflitto retention/legittimo interesse**: le analisi più vecchie di 90gg sono già cancellate dal purge; per le più recenti, valutare se serve conservazione anonimizzata (vedi P1-2a) o cancellazione totale.
  - Considerare **soft-delete + job di pulizia** (flag `is_deleted` + task) per dare l'opzione "ripristina entro X giorni", ma la cancellazione GDPR deve essere effettiva.
  - Test: `accounts/tests/test_erasure.py` (cascata completa, niente residui).
- **Effort**: L.

#### P1-2a · Anonimizzazione dove la conservazione è obbligatoria
- **Obiettivo**: se serve tenere dati per fini legali/contabili, devono essere resi non riconducibili all'utente (anonimizzazione o pseudonimizzazione).
- **Code**: task `anonymize_orphaned_rows` che svuota i campi personali (email→anonima, nome→vuoto) su righe non cancellabili.
- **Effort**: M.

#### P1-3 · Diritto di rettifica (Art. 16)
- **Obiettivo**: l'utente modifica i propri dati (nome, email) — già parzialmente possibile.
- **Code**: verificare che l'endpoint profilo (`PATCH /api/v1/me`) permetta la modifica di nome/email; aggiungere email change con conferma.
- **Effort**: S.

#### P1-4 · Retention documentata ed esposta (Art. 5(1)(e))
- **Obiettivo**: l'utente deve sapere quanto vengono conservati i suoi dati.
- **Code**: la retention analisi (90gg, configurabile via `ANALYSIS_RETENTION_DAYS`) va **esposta nella UI** (es. pagina "Privacy / Data retention") e letta dal settings, non hardcoded.
- **Processo**: definire retention esplicite per log e axes (vedi P2-4).
- **Effort**: S.

---

### P2 — Compliance operativa

#### P2-1 · DPIA per AI (Art. 35 GDPR + Art. 50 AI Act) — sostituita da `docs/gdpr/dpia-ai.md`
- **Obiettivo**: DPIA completa che copre rischi GDPR + obblighi AI Act Art. 50. Documento `docs/gdpr/dpia-ai.md` (già redatto come bozza completa).
- **Code**: nessuno. **Processo**: finalizzare, far firmare, revisione periodica (12 mesi o major release).
- **Effort**: M (documento già redatto).

#### P2-2 · Playbook di notifica violazione (Art. 33, 34)
- **Obiettivo**: procedura per rilevare, contenere e notificare una violazione all'autorità (72h) e agli interessati (rischio alto).
- **Code**: (facoltativo) endpoint interno `/api/v1/health/` già monitora lo stato; aggiungere alerting (vedi osservabilità).
- **Processo**: documento operativo `docs/gdpr/playbook-violazione.md`: chi chiama, template di notifica, registro delle violazioni.
- **Effort**: S.

#### P2-3 · Log di accesso e sicurezza (Art. 5(2), 32)
- **Obiettivo**: accountability — sapere chi ha fatto cosa.
- **Code**:
  - Retention esplicita per `axes_accessattempt`/`axes_accessfailurelog` (oggi crescono senza limite): purge dedicato nel task settimanale (`common/cleanup.py`).
  - Valutare audit log per azioni sensibili (modifica ruoli, export dati, cancellazione).
  - I log JSON hanno già rotazione giornaliera; definire retention file (es. 30-90gg).
- **Effort**: M.

#### P2-4 · Data minimization review (Art. 5(1)(c))
- **Obiettivo**: raccogliere solo il minimo necessario.
- **Code**: audit di ciò che finisce nei payload verso l'ai-engine e nei webhook. I webhook inviano già solo id/titolo/status. Gli error_context sono scelti dall'utente.
- **Processo**: verificare che i log JSON non contengano dati personali superflui (es. email nei payload).
- **Effort**: S.

#### P2-5 · Valutazione DPO (Art. 37)
- **Obiettivo**: capire se serve un Data Protection Officer. Obbligatorio solo se >250 dipendenti o trattamenti su larga scala di dati sensibili.
- **Processo**: verifica al momento del lancio; se non obbligatorio, documentare la decisione e nominare comunque un referente privacy.
- **Effort**: S.

---

## Riepilogo effort

| ID | Punto | Priorità | Effort | Tipo |
|---|---|---|---|---|
| P0-1 | Base giuridica + consenso | P0 | M | Processo |
| P0-2 | Privacy policy + ToS (+ AI-4) | P0 | L | Processo + codice (S) |
| P0-3 | Registro trattamenti (+ AI) | P0 | S-M | Documento |
| P0-4 | Accordi processor | P0 | S | Processo |
| **AI-1** | **UI Disclosure (Art. 50(1)+(5))** | **P0** | **M** | **Codice (frontend)** |
| **AI-2** | **Machine-readable marking — metadati (Art. 50(2))** | **P0** | **M** | **Codice (modelli + agenti + serializer)** |
| **AI-3** | **Documentazione tecnica marking** | **P0** | **S** | **Documento** |
| **AI-4** | **Privacy policy sezione AI** | **P0** | **S** | **Processo + codice (S)** |
| **AI-5** | **Valutazione high-risk (NO)** | **P0** | **S** | **Documento** |
| **AI-6** | **DPIA per AI** | **P0** | **M** | **Documento (dpia-ai.md)** |
| P1-1 | Export dati | P1 | L | Codice |
| P1-2 | Cancellazione account | P1 | L | Codice |
| P1-2a | Anonimizzazione | P1 | M | Codice |
| P1-3 | Rettifica profilo | P1 | S | Codice |
| P1-4 | Retention esposta | P1 | S | Codice + UI |
| P2-2 | Playbook violazione | P2 | S | Documento |
| P2-3 | Log accesso + retention | P2 | M | Codice |
| P2-4 | Data minimization | P2 | S | Audit |
| P2-5 | DPO | P2 | S | Processo |

**Totale stimato**: ~7-8 giornate di codice (P1 + AI-1/2 + parte P2-3) + ~4-5 giornate di documentazione/legale (P0 + AI-3/4/5/6 + P2-1/2/5).

---

## Cosa c'è già (non rifare)

- Retention 90gg con purge settimanale (`ANALYSIS_RETENTION_DAYS`, `common/cleanup.py`)
- Eliminazione in cascata via FK
- LLM **locale** (nessun processor esterno per l'inferenza)
- Secret webhook cifrati (Fernet), password hashate, JWT con blacklist
- Isolamento multi-tenant testato (`common/tests/test_tenant_isolation.py`)
- Minimi dati raccolti sul profilo
- Payload cap 200k, chunk troncati, retrieval top-30
- TLS nginx + security headers + HSTS opt-in
- DLQ Celery, queue hardening, lockout django-axes

---

## Ordine consigliato di esecuzione

1. **P0-2 + P0-3 + P0-1 + AI-1 + AI-2 + AI-3 + AI-4 + AI-5** (prerequisiti lancio + compliance AI Act entro 2 dic 2026)
2. **P1-1 + P1-2 + AI-1 (frontend integration) + AI-2 (model changes + agenti)**
3. **P1-4 + P1-3 + AI-4 (legal pages)**
4. **P2-3 + P2-2 + P2-4 + P2-5 + AI-6 (DPIA finale)**

---

## File da modificare (code changes)

| File | Modifica |
|---|---|
| `backend/analyses/models.py` | Aggiungere `ai_generated`, `model_name`, `model_version`, `generated_at`, `prompt_hash`, `watermark` (nullable) su `Report`, `FixSuggestion`, `BugLocalization`, `RootCause`, `LogAnalysis` |
| `ai-engine/agents/report_generator/generator.py` | Popolare nuovi campi nel result |
| `ai-engine/agents/patch_generator/generator.py` | Popolare nuovi campi nel result |
| `ai-engine/agents/bug_localizer/localizer.py` | Popolare nuovi campi nel result |
| `ai-engine/agents/root_cause/rca_agent.py` | Popolare nuovi campi nel result |
| `ai-engine/agents/log_analyzer/analyzer.py` | Popolare nuovi campi nel result |
| `backend/analyses/serializers.py` | Esporre nuovi campi nelle API |
| `frontend/src/components/AIBadge.tsx` | Nuovo componente badge "🤖 AI-generated" + tooltip |
| `frontend/src/pages/Report/`, `Fix/`, `RCA/`, `BugLocalization/`, `LogAnalysis/` | Integrazione `AIBadge` |
| `backend/common/models.py` (PlatformSetting) | (Opzionale futuro) Toggle disclosure AI per B2B — non ora |
| `docs/gdpr/ai-marking-spec.md` | Nuovo: spec tecnica marking |
| `docs/gdpr/dpia-ai.md` | Nuovo: DPIA completa per AI |
| `docs/gdpr/high-risk-assessment.md` | Nuovo: valutazione non high-risk |
| `docs/gdpr/registro-trattamenti.md` | Nuovo: registro trattamenti |
| `docs/gdpr/playbook-violazione.md` | Nuovo: playbook violazione |
| `frontend/src/pages/Legal/` | Privacy policy + ToS con sezione AI |