# Registro dei Trattamenti — CodeCoroner (Art. 30 GDPR)

**Versione**: 1.0 | **Data**: 2026-09-10 | **Stato**: Bozza
**Titolare**: [Nome organizzazione] | **DPO/Referente**: [Nome/email]

---

## 1. Trattamento: Gestione Account Utenti

| Campo | Dettaglio |
|---|---|
| **Finalità** | Autenticazione, autorizzazione, gestione profilo, sicurezza accessi |
| **Base giuridica** | Art. 6(1)(b) GDPR — Esecuzione contratto (ToS) |
| **Categorie dati** | Email, nome, hash password, timestamp creazione/ultimo accesso, flag superuser, gruppi |
| **Categorie interessati** | Utenti registrati (sviluppatori, admin, owner progetto) |
| **Destinatari** | Nessuno (dati non condivisi con terzi) |
| **Trasferimenti internazionali** | Nessuno (hosting UE) |
| **Retention** | Durata account + 30gg post-cancellazione (audit log) |
| **Misure sicurezza** | bcrypt hash, JWT con blacklist, lockout django-axes, TLS 1.2+ |

---

## 2. Trattamento: Gestione Progetti, Repository, Analisi

| Campo | Dettaglio |
|---|---|
| **Finalità** | Organizzazione lavoro, analisi bug, collaborazione team |
| **Base giuridica** | Art. 6(1)(b) GDPR — Esecuzione contratto |
| **Categorie dati** | Metadati progetto/repo, error_context (stacktrace, log, descrizione), risultati analisi (localizzazione, RCA, fix, report), timestamp |
| **Categorie interessati** | Utenti (owner, membri progetto), eventuali terzi citati in error_context |
| **Destinatari** | Membri stesso progetto/gruppo (isolamento tenant) |
| **Trasferimenti internazionali** | Nessuno |
| **Retention** | `ANALYSIS_RETENTION_DAYS=90` (configurabile) + purge settimanale |
| **Misure sicurezza** | Isolamento tenant (FK + policy), TLS, crittografia webhook secrets |

---

## 3. Trattamento: Elaborazione AI per Analisi Bug (Art. 50 AI Act)

| Campo | Dettaglio |
|---|---|
| **Finalità** | Generare localizzazione bug, root cause analysis, fix suggestion, report tramite LLM locale |
| **Base giuridica** | Art. 6(1)(b) — Esecuzione contratto (servizio core) + Art. 6(1)(f) — Legittimo interesse (sicurezza codice) |
| **Categorie dati** | **Input**: error_context (stacktrace, log, descrizione — possono contenere PII accidentali), chunk codice sorgente (top-30 rilevanti, max 4000 char cadauno) **Output**: LogAnalysis, BugLocalization, RootCause, FixSuggestion, Report (con metadati AI marking) |
| **Categorie interessati** | Utenti richiedenti analisi, eventuali autori codice nel repo |
| **Destinatari** | **Nessuno** — LLM gira in locale (Ollama container, rete Docker interna), zero egress |
| **Trasferimenti internazionali** | **Nessuno** — Modelli (qwen2.5-coder, nomic-embed-text) scaricati una volta, esecuzione locale |
| **Retention** | 90gg (come analisi) + metadati AI marking per audit Art. 50 |
| **Misure sicurezza** | LLM locale (zero uscita rete), payload cap 200k char, chunk troncati, retrieval top-30, temperature 0, format=json forzato, parsing tollerante |

---

## 4. Trattamento: Webhook & Integrazioni

| Campo | Dettaglio |
|---|---|
| **Finalità** | Notifiche eventi (analysis.completed, analysis.failed, repository.indexed) a sistemi esterni |
| **Base giuridica** | Art. 6(1)(b) — Esecuzione contratto (funzionalità richiesta da utente) |
| **Categorie dati** | Event type, analysis ID, project ID, timestamp, secret webhook (cifrato) |
| **Categorie interessati** | Utenti configuranti webhook, sistemi riceventi |
| **Destinatari** | URL configurati dall'utente (solo superuser possono creare webhook) |
| **Trasferimenti internazionali** | Secondo configurazione utente (responsabilità utente) |
| **Retention** | Ciclo vita webhook + log consegna (da definire) |
| **Misure sicurezza** | Secret cifrato Fernet (chiave da `WEBHOOK_SECRET_KEY` o `DJANGO_SECRET_KEY`), HTTPS enforced |

---

## 5. Trattamento: Logging & Sicurezza (django-axes)

| Campo | Dettaglio |
|---|---|
| **Finalità** | Prevenzione brute-force, audit accessi, compliance sicurezza |
| **Base giuridica** | Art. 6(1)(f) — Legittimo interesse (sicurezza sistemi) |
| **Categorie dati** | IP (non memorizzato da axes per design), username, timestamp, user agent, success/fallimento, lockout status |
| **Categorie interessati** | Chiunque tenti login |
| **Destinatari** | Nessuno |
| **Retention** | Da definire (piano P2-3: purge dedicato in `common/cleanup.py`) |
| **Misure sicurezza** | Lockout per username (5 tentativi → 1h), no IP tracking per evitare falsi positivi NAT |

---

## 6. Trattamento: Log Strutturati Applicazione

| Campo | Dettaglio |
|---|---|
| **Finalità** | Debug, monitoring, audit trail, compliance |
| **Base giuridica** | Art. 6(1)(f) — Legittimo interesse (operatività/sicurezza) |
| **Categorie dati** | Timestamp, livello, logger, messaggio, request ID, user ID (se autenticato), traceback (se errore) — **no PII sensibili** |
| **Destinatari** | Nessuno (file locale + stdout) |
| **Retention** | Rotazione giornaliera, retention file da definire (piano P2-3: 30-90gg) |
| **Misure sicurezza** | JSON strutturato, no segreti in log, rotazione automatica |

---

## 7. Sub-processori (Art. 28 GDPR)

| Fornitore | Ruolo | DPA | Trasferimento | Note |
|---|---|---|---|---|
| **Hosting provider** (es. Hetzner, AWS EU, self-hosted) | Infrastructure (VM, storage, network) | Sì | UE (scelto in UE) | Contratto DPA firmato |
| **Ollama** (software open source) | LLM runtime | N/A (software, non servizio) | Nessuno | Esecuzione locale in container |
| **PostgreSQL / pgvector** | Database | N/A (self-hosted) | Nessuno | Container locale |
| **Redis** | Cache / Celery broker | N/A (self-hosted) | Nessuno | Container locale |
| **MinIO** | Object storage (webhook payloads, artifacts) | N/A (self-hosted) | Nessuno | Container locale |

---

## 8. Diritti degli interessati — Punti di contatto

| Diritto | Endpoint / Procedura |
|---|---|
| Accesso (Art. 15) | `GET /api/v1/me/export` (piano P1-1) |
| Rettifica (Art. 16) | `PATCH /api/v1/me` (nome, email) |
| Cancellazione (Art. 17) | `DELETE /api/v1/me` (piano P1-2, cascade FK) |
| Portabilità (Art. 20) | Export JSON/CSV via `/me/export` |
| Limitazione (Art. 18) | Soft-delete flag + job differito |
| Opposizione (Art. 21) | Opt-out marketing (flag `consent_marketing`) |
| Reclamo autorità | Contatto DPO + link autorità nazionale |

---

## 9. Contatti

- **Titolare**: [Nome organizzazione], [Indirizzo], [Email PEC]
- **DPO / Referente privacy**: [Nome], [Email], [Telefono]
- **Responsabile sicurezza**: [Nome], [Email]

---

**Ultimo aggiornamento**: 2026-09-10 | **Prossima revisione**: 2027-03-10 (o a major release)