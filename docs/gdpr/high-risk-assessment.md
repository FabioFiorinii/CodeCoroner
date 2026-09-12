# High-Risk AI Assessment — CodeCoroner

**Versione**: 1.0 | **Data**: 2026-09-10 | **Stato**: Approvato
**Sistema**: CodeCoroner — Piattaforma AI per Root Cause Analysis & Bug Fixing
**Riferimento**: AI Act (Reg. UE 2024/1689) — Allegato III

---

## 1. Conclusione

**CodeCoroner NON ricade in nessuna categoria di sistemi AI ad alto rischio** definite nell'Allegato III dell'AI Act.

Di conseguenza, CodeCoroner è classificato come **sistema AI a rischio limitato**, soggetto unicamente agli obblighi di trasparenza di cui all'**Art. 50** (già implementati: vedi `docs/gdpr/ai-marking-spec.md`).

---

## 2. Analisi per categoria (Allegato III)

| # | Categoria Allegato III | Descrizione | Applicabilità a CodeCoroner |
|---|---|---|---|
| **1** | **Identificazione biometrica** | Sistemi per identificazione biometrica remota, categorizzazione biometrica, inferenza emotiva | ❌ **NO** — CodeCoroner non processa dati biometrici |
| **2** | **Infrastrutture critiche** | Sistemi per gestione/traffico reti elettriche, idriche, gas, trasporti, infrastrutture digitali | ❌ **NO** — CodeCoroner è tool di sviluppo software, non gestisce infrastrutture fisiche |
| **3** | **Educazione e formazione professionale** | Sistemi per determinare accesso/ammissione/valutazione in educazione/formazione | ❌ **NO** — Non usato in contesti educativi per decisioni su persone |
| **4** | **Lavoro e gestione risorse umane** | Reclutamento, screening CV, valutazione performance, promozioni, licenziamenti | ❌ **NO** — Non prende decisioni su assunzioni/carriere |
| **5** | **Servizi privati/pubblici essenziali** | Accesso a servizi bancari, assicurativi, sanitari, benefici pubblici, credito | ❌ **NO** — Non determina accesso a servizi essenziali |
| **6** | **Law enforcement** | Polizia predittiva, analisi prove, valutazione rischio recidiva, profilazione | ❌ **NO** — Non usato da forze dell'ordine |
| **7** | **Migrazione, asilo, frontiere** | Valutazione rischio migrazione, esame domande asilo, controlli frontiera | ❌ **NO** — Non usato in contesti migratori |
| **8** | **Amministrazione della giustizia** | Supporto decisionale giudiziario, interpretazione leggi, sentenze | ❌ **NO** — Non usato in contesti giudiziari |

---

## 3. Analisi aggiuntiva: General-Purpose AI (GPAI)

CodeCoroner **utilizza** modelli GPAI (qwen2.5-coder via Ollama) ma **non è un sistema GPAI** ai sensi dell'Art. 51-56 AI Act:

- Non è un modello fondazionale messo a disposizione come servizio
- È un'applicazione verticale che *usa* modelli GPAI locali
- Non fornisce API per addestramento/fine-tuning/uso generico del modello

---

## 4. Obblighi applicabili

| Regolamento | Articolo | Obbligo | Stato |
|---|---|---|---|
| **AI Act** | Art. 50(1) | Interaction transparency (informare utenti che interagiscono con AI) | ✅ Implementato (AI-1: badge UI) |
| **AI Act** | Art. 50(2) | Machine-readable marking (output marcati machine-readable) | ✅ Implementato (AI-2: metadati API/DB) |
| **AI Act** | Art. 50(3) | Emotion recognition / biometric categorization disclosure | ❌ N/A |
| **AI Act** | Art. 50(4) | Deployer labeling (deepfake + testo pubblicato interesse pubblico) | ❌ N/A (report privati) |
| **AI Act** | Art. 50(5) | Horizontal: disclosure chiara, distinguibile, primo contatto, accessibile | ✅ Implementato (AI-1 badge UI) |
| **GDPR** | Art. 5, 12, 25 | Privacy by design, trasparenza, accountability | ✅ In piano (piano GDPR) |
| **GDPR** | Art. 22 | Diritto a non essere sottoposto a decisioni automatizzate | ✅ Soddisfatto (output = suggerimenti, no decisioni vincolanti) |

---

## 5. Giustificazione dettagliata per categorie borderline

### Categoria 5 — Servizi essenziali (credito, assicurazioni, sanità)
CodeCoroner è uno **strumento per sviluppatori** (developer tool). Non determina:
- Affidabilità creditizia
- Eleggibilità assicurativa
- Accesso a cure sanitarie
- Erogazione benefici pubblici

### Categoria 4 — HR / Recruiting
CodeCoroner non:
- Filtra CV
- Valuta candidati
- Prende decisioni su assunzioni/promozioni/licenziamenti
- Monitora performance dipendenti

### Categoria 8 — Amministrazione giustizia
CodeCoroner non:
- Assiste giudici/giurati
- Interpreta leggi
- Suggerisce sentenze
- Analizza prove legali

---

## 6. Monitoraggio continuo

Se in futuro CodeCoroner dovesse:
- Essere integrato in pipeline CI/CD che **bloccano automaticamente deploy** basandosi su fix AI (decisione automatizzata con effetti legali/operativi)
- Essere usato per **certificare conformità** di codice per scopi regolatori (es. medical device software)
- Essere offerto come **servizio GPAI** (es. API per terze parti)

Allora una **nuova valutazione** sarebbe necessaria. Attualmente: **nessun trigger**.

---

## 6. Conclusione firmata

**CodeCoroner è un sistema AI a rischio limitato (Art. 50)**. Non ricade in nessuna categoria ad alto rischio (Allegato III). Gli unici obblighi AI Act applicabili sono gli obblighi di trasparenza Art. 50, già implementati.

**Firma valutatore**: ________________________  **Data**: _______________

**Firma titolare**: ________________________  **Data**: _______________