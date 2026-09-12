# Privacy Policy — CodeCoroner

**Versione**: 1.0 | **Data entrata in vigore**: 2026-09-10 | **Ultimo aggiornamento**: 2026-09-10

---

## 1. Chi siamo

**Titolare del trattamento**: [Nome organizzazione legale]
**Sede legale**: [Indirizzo completo]
**Email privacy**: privacy@codecoroner.example
**PEC**: privacy@pec.codecoroner.example
**DPO (Data Protection Officer)**: [Nome DPO] — dpo@codecoroner.example

CodeCoroner è una piattaforma SaaS per l'analisi automatica di bug software (Root Cause Analysis) basata su Intelligenza Artificiale.

---

## 2. Quali dati raccogliamo e perché

### 2.1 Dati che ci fornisci direttamente
| Categoria | Esempi | Finalità | Base giuridica |
|---|---|---|---|
| **Account** | Email, nome, password (hash) | Autenticazione, identificazione, comunicazioni di servizio | Art. 6(1)(b) — Contratto |
| **Progetti/Repo** | Nome progetto, URL repository Git, branch, configurazioni analisi | Organizzazione lavoro, esecuzione analisi | Art. 6(1)(b) — Contratto |
| **Contesto errore** | Stacktrace, log, messaggio errore, descrizione, steps to reproduce | Input per analisi AI | Art. 6(1)(b) — Contratto |
| **Webhook** | URL endpoint, secret (cifrato), eventi sottoscritti | Notifiche eventi (analysis.completed, etc.) | Art. 6(1)(b) — Contratto |

### 2.2 Dati generati automaticamente
| Categoria | Esempi | Finalità | Base giuridica |
|---|---|---|---|
| **Analisi AI** | Bug localization, Root Cause, Fix Suggestion, Report | Output del servizio core | Art. 6(1)(b) — Contratto |
| **Embedding codice** | Vettori 768-dim (nomic-embed-text) dei chunk sorgente | Retrieval semantico per analisi | Art. 6(1)(b) — Contratto |
| **Log tecnici** | Timestamp, livello, request ID, user ID (se autenticato), errori | Debug, monitoring, sicurezza | Art. 6(1)(f) — Legittimo interesse |
| **Sicurezza (axes)** | Tentativi login, lockout, user agent | Prevenzione brute-force | Art. 6(1)(f) — Legittimo interesse |

### 2.3 Dati che NON raccogliamo
- **Nessun dato di pagamento** (gestito da provider esterni se applicabile)
- **Nessun dato biometrico / sensibile** (Art. 9 GDPR)
- **Nessun dato di minori** (servizio B2B per sviluppatori, >18 anni)
- **Nessun tracking pubblicitario / profiling commerciale**

---

## 3. Elaborazione mediante Intelligenza Artificiale (Art. 50 AI Act)

### 3.1 Cosa facciamo con l'AI
CodeCoroner utilizza **modelli linguistici locali (LLM)** per analizzare errori software e produrre:
- **Localizzazione bug** — quali file sono sospetti e perché
- **Root Cause Analysis** — file, riga, catena causale, confidence
- **Fix Suggestion** — diff unificato + piano implementazione + spiegazione
- **Report finale** — documento Markdown sintetico

### 3.2 Modelli utilizzati
| Modello | Ruolo | Hosting |
|---|---|---|
| **qwen2.5-coder** (3b / 7b / 14b parametri) | Generazione testo (RCA, fix, report) | **Locale** — container Ollama su stessa macchina |
| **nomic-embed-text** (768-dim) | Embedding chunk codice per retrieval | **Locale** — container Ollama |

**Punto chiave**: Tutti i modelli girano **in locale** (container Ollama nella stessa rete Docker). **Nessun dato esce dalla tua infrastruttura**. Nessuna chiamata a OpenAI, Anthropic, Google o altri provider cloud.

### 3.3 Trasparenza AI (Art. 50 AI Act)
In conformità al Regolamento UE 2024/1689 (AI Act) Art. 50:
- **Art. 50(1)** — Ogni output AI è etichettato con badge "🤖 AI-generated" + tooltip (modello, versione, data generazione)
- **Art. 50(2)** — Ogni output include metadati machine-readable: `ai_generated=true`, `model_name`, `model_version`, `generated_at`, `prompt_hash` (SHA-256)
- **Art. 50(5)** — Disclosure chiara, distinguibile, al primo contatto, accessibile (WCAG 2.1 AA)

### 3.4 I tuoi diritti sugli output AI
- **Accesso/Portabilità** — Esporta tutti i tuoi dati inclusi output AI (`GET /api/v1/me/export`)
- **Cancellazione** — Elimina account e tutti gli output associati (`DELETE /api/v1/me`)
- **Rettifica** — Modifica dati profilo
- **Nessuna decisione automatizzata vincolante** (Art. 22 GDPR) — Gli output AI sono **suggerimenti**; sei tu a decidere se applicare il fix

---

## 4. Condivisione e destinatari

| Destinatario | Dati condivisi | Base giuridica | Salvaguardie |
|---|---|---|---|
| **Membri stesso progetto/gruppo** | Analisi, report, repo assegnati | Art. 6(1)(b) — Contratto | Isolamento tenant (FK + policy) |
| **Webhook configurati da te** | Eventi (analysis.completed, etc.) | Art. 6(1)(b) — Contratto | Secret cifrato, HTTPS, solo superuser creano |
| **Hosting provider (es. Hetzner, AWS EU)** | Infrastruttura (VM, storage, network) | Art. 28 — Processor | DPA firmato, data center UE |
| **Autorità (su richiesta legale)** | Dati strettamente necessari | Art. 6(1)(c) — Obbligo legale | Minimizzazione, canali sicuri |

**Nessuna vendita dati. Nessun advertising. Nessun trasferimento extra-UE senza tua istruzione.**

---

## 5. Trasferimenti internazionali

**Non trasferiamo dati fuori dallo Spazio Economico Europeo (SEE)** se non su tua istruzione esplicita (es. webhook verso endpoint extra-UE configurato da te — in tal caso sei responsabile della conformità Art. 44-49 GDPR).

L'infrastruttura (VM, database, object storage) risiede in **data center UE** (es. Hetzner Falkenstein/Nuremberg, AWS eu-central-1).

---

## 6. Retention e cancellazione

| Categoria | Retention | Cancellazione |
|---|---|---|
| Account & profilo | Durata account + 30gg post-cancellazione | `DELETE /api/v1/me` (cascade FK) |
| Analisi & output AI | 90 giorni (configurabile `ANALYSIS_RETENTION_DAYS`) | Purge automatico settimanale + cancellazione manuale |
| Embedding codice | Ciclo vita repository | Cancellazione repo → purge embedding |
| Webhook secrets | Ciclo vita webhook | Cancellazione webhook |
| Log tecnici / sicurezza | 30-90 giorni (rotazione giornaliera) | Purge automatico |

**Diritto all'oblio**: Puoi richiedere cancellazione completa in qualsiasi momento (`DELETE /api/v1/me` o email a privacy@codecoroner.example). I backup (pg_dump + repo volume) vengono purgati entro 7 giorni (`RETENTION_DAYS=7` default).

---

## 6. Sicurezza

| Misura | Dettaglio |
|---|---|
| **Crittografia in transito** | TLS 1.2+ ovunque (nginx :8443, HSTS opt-in, security headers) |
| **Crittografia a riposo** | Webhook secrets → Fernet (chiave da `WEBHOOK_SECRET_KEY`); Password → bcrypt |
| **Autenticazione** | JWT access/refresh token (blacklist revoca), lockout django-axes (5 tentativi → 1h) |
| **Isolamento tenant** | Foreign Key + policy Django + test automatizzati (`test_tenant_isolation.py`) |
| **LLM locale** | Zero egress — Ollama su rete Docker interna, nessun dato esce |
| **Minimizzazione payload** | Cap 200k char, chunk troncati (max 4000 char), retrieval top-30 |
| **Backup & DR** | `make backup` (pg_dump -Fc + repo volume) / `make restore` — testato su macchina fresh |

---

## 7. I tuoi diritti (Art. 15-22 GDPR)

| Diritto | Come esercitarlo |
|---|---|
| **Accesso** (Art. 15) | `GET /api/v1/me/export` — scarica tutti i tuoi dati (JSON/CSV) |
| **Rettifica** (Art. 16) | `PATCH /api/v1/me` — modifica nome/email |
| **Cancellazione** (Art. 17) | `DELETE /api/v1/me` — hard-delete cascade (account, progetti, analisi, embedding) |
| **Portabilità** (Art. 20) | Export JSON/CSV via `/me/export` |
| **Limitazione** (Art. 18) | Soft-delete + job differito (su richiesta) |
| **Opposizione** (Art. 21) | Opt-out marketing (flag `consent_marketing` su profilo) |
| **Non decisione automatizzata** (Art. 22) | Garantito — output AI = suggerimenti, validazione umana richiesta |

**Tempi di risposta**: entro 30 giorni (prorogabili a 60 per complessità). Contatto: privacy@codecoroner.example

---

## 7. Reclami

Puoi presentare reclamo all'autorità di controllo competente:
- **Italia**: Garante per la Protezione dei Dati Personali — www.garanteprivacy.it
- **Altri paesi UE**: Autorità nazionale competente

---

## 8. Modifiche a questa policy

Eventuali modifiche saranno pubblicate su questa pagina con data aggiornamento. Per modifiche sostanziali, ti informeremo via email e/o banner in-app almeno 30 giorni prima.

---

## 9. Contatti

**Titolare**: [Organizzazione] — [Indirizzo] — privacy@codecoroner.example
**DPO**: [Nome] — dpo@codecoroner.example
**PEC**: privacy@pec.codecoroner.example

---

*Ultimo aggiornamento: 2026-09-10 — Versione 1.0*