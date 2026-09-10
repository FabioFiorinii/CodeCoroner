# DPIA — Data Protection Impact Assessment per CodeCoroner (AI Processing)
**Versione**: 1.0 | **Data**: 2026-08-20 | **Stato**: Bozza per revisione/firma
**Titolare**: [Nome titolare / organizzazione] | **Referente privacy**: [Nome/email]
**Sistema**: CodeCoroner — Piattaforma AI per Root Cause Analysis & Bug Fixing
**Base giuridica**: Art. 6(1)(b) GDPR (contratto) + Art. 6(1)(f) (legittimo interesse sicurezza)
**AI Act classification**: Sistema AI a rischio limitato (Art. 50 transparency) — **NON high-risk** (Allegato III)
**Scadenza AI Act Art. 50(2) marking**: 2 dicembre 2026 (grace period per sistemi già sul mercato)

---

## 1. Descrizione del trattamento

### 1.1 Finalità
Analisi automatica di errori software (stacktrace, log, descrizione) per produrre:
- Localizzazione bug (file sospetti + score)
- Root Cause Analysis (file, riga, catena causale, confidence)
- Suggerimento fix (diff unificato, piano, spiegazione)
- Report finale (markdown)

### 1.2 Categorie di dati
| Categoria | Esempi | Sensibilità |
|---|---|---|
| Dati account | email, nome, hash password | Personali comuni |
| Contesto errore | stacktrace, log, messaggio errore, descrizione utente | Possono contenere PII accidentali (path file, variabili) |
| Codice sorgente | chunk di funzioni/classi dal repo indicizzato | Proprietà intellettuale cliente |
| Output AI | report, fix, RCA, localizzazione | Derivati, possono contenere IP/PII |

### 1.3 Flussi
1. Utente invia `error_context` → Django → ai-engine (HTTP, rete locale Docker)
2. ai-engine chiama Ollama (locale, stesso host) → LLM genera output strutturato JSON
3. Output validato (`parse_json_response`) → salvato su PostgreSQL (pgvector per embedding)
4. Frontend mostra output con disclosure AI

### 1.4 Modelli AI
- **Embedding**: `nomic-embed-text` (768-dim) — solo per retrieval, no generazione testo
- **LLM generazione**: `qwen2.5-coder` 3b/7b/14b (tier configurabile admin) — temperatura 0, `format=json`, `num_predict` limitato
- **Hosting**: 100% locale (Ollama container), **zero dati escono** dalla macchina

---

## 2. Necessità e proporzionalità

| Criterio | Valutazione |
|---|---|
| **Necessità** | L'analisi manuale richiede ore/giorni; AI riduce a minuti. Nessuna alternativa non-AI equivalente per comprensione semantica cross-file. |
| **Proporzionalità** | Dati minimi: solo chunk rilevanti (top-30, max 4000 char cadauno) inviati al LLM, non tutto il repo. Payload cap 200k char. Retention 90gg. |
| **Minimizzazione** | Solo chunk rilevanti inviati; embedding locale; zero log LLM raw (solo output parsato). |
| **Alternative** | Analisi statica pura (Semgrep/CodeQL) → non copre root cause semantica. Solo LLM dà ragionamento cross-file. |

---

## 3. Valutazione dei rischi

| Rischio | Likelihood | Impact | Mitigazione attuale | Residuo |
|---|---|---|---|---|
| **Data leakage via prompt** (PII nel contesto errore finisce nel LLM) | Medio | Alto | LLM locale (zero uscita rete); payload cap 200k; utente controlla cosa invia | Basso |
| **Hallucination / fix errato** | Medio | Medio | Output validato utente prima applicazione; disclosure "AI-generated"; fix non applicato automaticamente | Basso |
| **Prompt injection** | Basso | Alto | `format=json` forzato, `temperature=0`, `num_predict` limitato, parsing tollerante ma strutturato, payload cap | Basso |
| **Bias / discriminazione** | Basso | Medio | Modello addestrato su codice, non dati personali; no decisioni su persone | Basso |
| **Ritenzione eccessiva output AI** | Basso | Medio | Retention 90gg via `ANALYSIS_RETENTION_DAYS` + purge settimanale; export/cancellazione su richiesta | Basso |
| **Data leakage via embedding** (vector DB contiene chunk codice) | Basso | Medio | Embedding locale; pgvector su stesso host; isolamento tenant via FK; repo_cache volume read-only condiviso | Basso |
| **Re-identificazione da output AI** (fix/RCA contengono path/codice sensibile) | Basso | Medio | Isolamento tenant rigoroso (FK + policy); output visibile solo membri progetto | Basso |
| **Mancata disclosure AI Act** | Basso | Legale | Disclosure UI + metadati + privacy policy aggiornata (piano AI-1/2/4) | Basso |

---

## 4. Misure tecniche e organizzative (TOMs)

| Misura | Stato | Dettaglio |
|---|---|---|
| **Local-only LLM** | ✅ Implementato | Ollama container, rete Docker interna, zero egress |
| **Crittografia a riposo** | ✅ Implementato | Webhook secrets Fernet; password bcrypt; TLS nginx |
| **Isolamento tenant** | ✅ Implementato | FK + policy + test `test_tenant_isolation.py` |
| **Retention automatizzata** | ✅ Implementato | `ANALYSIS_RETENTION_DAYS=90`, purge Celery beat |
| **Minimizzazione payload** | ✅ Implementato | Cap 200k char, chunk troncati, retrieval top-30 |
| **Disclosure AI** | 🔄 In piano (AI-1) | Badge UI + tooltip |
| **Machine-readable marking** | 🔄 In piano (AI-2) | Campi `ai_generated`, `model_*`, `generated_at`, `prompt_hash` |
| **Export/cancellazione** | 🔄 In piano (P1-1/2) | Endpoint `/me/export`, `DELETE /me` |
| **Audit log** | 🔄 In piano (P2-3) | Retention axes + audit log azioni sensibili |
| **DPIA review periodica** | 🔄 Da definire | Ogni 12 mesi o a major release |

---

## 5. Diritti degli interessati (Art. 15-22 GDPR)

| Diritto | Implementazione |
|---|---|
| Accesso (Art. 15) | `GET /api/v1/me/export` (tutti dati + output AI) |
| Rettifica (Art. 16) | `PATCH /api/v1/me` (nome, email) |
| Cancellazione (Art. 17) | `DELETE /api/v1/me` (cascade FK) |
| Portabilità (Art. 20) | Export JSON + CSV |
| Limitazione (Art. 18) | Soft-delete flag + job pulizia differito |
| Opposizione (Art. 21) | Opt-out marketing (flag `consent_marketing`) |
| Non sottoposto a decisione automatizzata (Art. 22) | **Nessuna decisione automatizzata con effetti giuridici** — output AI è *suggerimento*, utente valida/applica |

---

## 6. Trasferimenti internazionali

**Nessuno**. Tutto gira on-premise / self-hosted. Ollama, PostgreSQL, Redis, MinIO, ai-engine, Django, nginx — tutti container nella stessa rete Docker. Nessun processore esterno (no OpenAI, no cloud AI).

---

## 7. Sub-processori

| Fornitore | Ruolo | DPA | Trasferimento |
|---|---|---|---|
| Hosting provider (es. Hetzner, AWS, self-hosted) | Infrastructure | Sì | UE (scelto in UE) |
| Ollama (software) | LLM runtime | N/A (software open source, run locale) | Nessuno |
| PostgreSQL / pgvector | Database | N/A (self-hosted) | Nessuno |

---

## 8. AI Act — Obblighi Art. 50 (Transparency)

| Articolo | Obbligo | Applicabilità | Stato |
|---|---|---|---|
| **Art. 50(1)** | Interaction transparency: informare che si interagisce con AI | ✅ SÌ — output AI mostrati all'utente | 🔄 AI-1 (UI badge) |
| **Art. 50(2)** | Machine-readable marking: output marcati in formato machine-readable, rilevabile, interoperabile | ✅ SÌ — Report, Fix, RCA, Localization, LogAnalysis sono testo AI | 🔄 AI-2 (metadati API/DB) |
| **Art. 50(3)** | Emotion recognition / biometric categorization | ❌ NO | N/A |
| **Art. 50(4)** | Deployer labeling: deepfake + testo pubblicato per interesse pubblico | ⚠️ Parziale — deepfake NO; report privati non "pubblicati per informare pubblico" | Escluso (report privati) |
| **Art. 50(5)** | Horizontal: disclosure chiara, distinguibile, primo contatto, accessibile | ✅ SÌ | 🔄 AI-1 (UI badge + tooltip) |

**Scadenze**: Art. 50 in vigore dal 2 agosto 2026. Grace period Art. 50(2) marking per sistemi già sul mercato: **2 dicembre 2026**.

---

## 9. Valutazione High-Risk AI (Allegato III AI Act)

CodeCoroner **NON** ricade in nessuna categoria di sistemi AI ad alto rischio (Allegato III):

| Categoria Allegato III | Applicabilità |
|---|---|
| 1. Biometric identification | ❌ NO |
| 2. Critical infrastructure | ❌ NO |
| 3. Education / vocational training | ❌ NO |
| 4. Employment / recruitment | ❌ NO |
| 5. Essential private/public services | ❌ NO |
| 6. Law enforcement | ❌ NO |
| 7. Migration / asylum / border control | ❌ NO |
| 8. Administration of justice | ❌ NO |

**Conclusione**: CodeCoroner è un sistema AI a **rischio limitato** soggetto solo agli obblighi di trasparenza Art. 50. Documento separato `docs/gdpr/high-risk-assessment.md` per audit trail.

---

## 10. Conclusione e piano d'azione

Il trattamento è **necessario, proporzionato, minimizzato**. I rischi residui sono **bassissimi** grazie a: LLM locale, isolamento tenant, retention breve, disclosure pianificata, zero trasferimenti esterni, no decisioni automatizzate con effetti giuridici.

**Azioni prioritarie (entro 2 dicembre 2026 per AI Act Art. 50(2))**:
1. Implementare **AI-1** (UI disclosure badge + tooltip) + **AI-2** (metadati marking su modelli + serializers)
2. Aggiornare **privacy policy / ToS** (AI-4: sezione "Elaborazione AI")
3. Finalizzare questo documento come DPIA formale e far firmare dal titolare
4. Documentare valutazione high-risk (AI-5) in `docs/gdpr/high-risk-assessment.md`
5. Completare documentazione tecnica marking (AI-3) in `docs/gdpr/ai-marking-spec.md`

**Piano di implementazione code** (prioritario per scadenza 2 dic 2026):
1. `backend/analyses/models.py` — aggiunta campi marking su 5 modelli
2. `ai-engine/agents/*/agent.py` (5 agenti) — popolamento campi
3. `backend/analyses/serializers.py` — esposizione campi
4. `frontend/src/components/AIBadge.tsx` + integrazione pagine
5. `docs/gdpr/ai-marking-spec.md` + `high-risk-assessment.md`

**Firma titolare**: ________________________  **Data**: _______________

**Firma referente privacy**: ________________________  **Data**: _______________