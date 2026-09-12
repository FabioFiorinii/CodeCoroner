# Playbook Notifica Violazione Dati — CodeCoroner (Art. 33, 34 GDPR)

**Versione**: 1.0 | **Data**: 2026-09-10 | **Stato**: Bozza operativa
**Titolare**: [Organizzazione] | **DPO**: [Nome/email]

---

## 1. Scopo e campo di applicazione

Questa procedura definisce come **rilevare, contenere, valutare, notificare e documentare** una violazione di dati personali (data breach) ai sensi degli Art. 33 (notifica all'autorità) e 34 (comunicazione agli interessati) del GDPR.

Si applica a **qualsiasi incidente** che comporti distruzione, perdita, alterazione, divulgazione non autorizzata o accesso non autorizzato a dati personali trattati da CodeCoroner.

---

## 2. Definizioni

| Termine | Definizione |
|---|---|
| **Violazione (breach)** | Violazione della sicurezza che comporta distruzione, perdita, alterazione, divulgazione non autorizzata o accesso a dati personali (Art. 4(12) GDPR) |
| **Dato personale** | Qualsiasi informazione riguardante persona fisica identificata/identificabile (Art. 4(1)) |
| **Titolare** | [Organizzazione] — determina finalità e mezzi del trattamento |
| **Responsabile** | Fornitori infrastruttura (hosting) — trattano dati per conto del titolare |
| **DPO** | [Nome] — referente privacy, punto di contatto autorità/Interessati |
| **Autorità di controllo** | Garante Privacy (Italia) / Autorità capofila (se cross-border) |

---

## 3. Team di gestione incidente

| Ruolo | Persona | Contatto | Responsabilità |
|---|---|---|---|
| **Incident Commander** | [Nome CTO/Tech Lead] | [Tel/Email/Slack] | Coordina risposta, decide escalation |
| **DPO / Privacy Lead** | [Nome DPO] | [Tel/Email] | Valuta rischio diritti, redige notifiche autorità/interessati |
| **Security Engineer** | [Nome SecEng] | [Tel/Email] | Analisi tecnica, containment, forensics |
| **Legal Counsel** | [Nome Avvocato] | [Tel/Email] | Consulenza legale, review notifiche |
| **Comms Lead** | [Nome PM/Marketing] | [Tel/Email] | Comunicazione utenti/stakeholder/media |

---

## 4. Processo — Timeline 72 ore (Art. 33)

```
T+0      Rilevazione
   │
   ▼
T+1h     Contenimento immediato (SecEng)
   │
   ▼
T+2h     Valutazione rischio (DPO + SecEng + Legal)
   │          ├─ Rischio basso  → Documenta, chiudi
   │          ├─ Rischio medio  → Notifica autorità (Art. 33)
   │          └─ Rischio alto   → Notifica autorità + Comunicazione interessati (Art. 34)
   ▼
T+24h    Notifica autorità (se richiesta) — entro 72h da rilevazione
   ▼
T+48h    Comunicazione interessati (se rischio alto) — senza indebito ritardo
   ▼
T+72h    Report finale autorità + Piano rimediation
   ▼
T+30g    Review post-incidente + Aggiornamento misure
```

---

## 5. Rilevazione (T+0 → T+1h)

### Fonti di rilevazione
| Fonte | Esempi |
|---|---|
| **Monitoring interno** | Alert Prometheus/Grafana (anomalie accessi, spike errori, exfiltration) |
| **Log audit** | Tentativi login anomali (axes), accessi admin insoliti, query DB massive |
| **Segnalazione interna** | Dipendente nota anomalia, riceve phishing, trova dati esposti |
| **Segnalazione esterna** | Utente/reporter sicurezza, autorità, media, ricercatore (responsible disclosure) |
| **Fornitori** | Hosting provider notifica compromissione infrastruttura |

### Azioni immediate (T+0 → T+1h)
1. **SecEng**: Isola sistema compromesso (revoca token, blocca IP, disabilita account, snapshot DB)
2. **Incident Commander**: Convoca team (Slack/Phone bridge), assegna ticket incidente (es. `INC-2026-09-10-001`)
3. **DPO**: Avviata scheda valutazione rischio (vedi §6)

---

## 6. Valutazione rischio (T+1h → T+4h)

### Matrice rischio (Art. 33(1) — "rischio per i diritti e le libertà")

| Fattore | Peso | Note |
|---|---|---|
| **Natura dati** | Alto=3 / Medio=2 / Basso=1 | PII sensibili (salute, biometrici) = 3; Email/nome = 2; Solo ID anonimi = 1 |
| **Volume** | >10k=3 / 1k-10k=2 / <1k=1 | Numero record coinvolti |
| **Categoria interessati** | Vulnerabili=3 / Generici=2 / Solo staff=1 | Minori, pazienti, dipendenti = 3 |
| **Probabilità abuso** | Alta=3 / Media=2 / Bassa=1 | Dati criptati? Accesso solo lettura? Exfiltration confermata? |
| **Impatto potenziale** | Furto identità=3 / Frode=2 / Disagio=1 | Conseguenze concrete per interessati |

**Punteggio ≥ 8 → Rischio ALTO** (notifica autorità + comunicazione interessati)
**Punteggio 5-7 → Rischio MEDIO** (notifica autorità)
**Punteggio ≤ 4 → Rischio BASSO** (solo documentazione interna)

### Eccezioni notifica autorità (Art. 33(1))
Non notificare se violazione **improbabile che comporti rischio** per diritti (es. dati cifrati con chiave non compromessa, accesso solo lettura su dati anonimi). **Documentare sempre la decisione**.

---

## 7. Notifica all'autorità (Art. 33) — entro 72h

### Contenuto minimo notifica (Art. 33(3))
1. **Natura violazione** — categorie dati, n. record, n. interessati
2. **Probabili conseguenze** — furto identità, frode, perdita riservatezza, ecc.
4. **Misure adottate** — contenimento, rimediation, mitigazione rischi
5. **DPO contact** — nome, email, telefono
6. **Allegati** — log tecnici, forensics summary (se disponibili)

### Canali notifica (Italia)
- **Portale Garante**: https://www.garanteprivacy.it/home/diritto-alla-protezione-dei-dati-personali/notifiche-violazioni-dati-personali
- **PEC**: protocollo@pec.gpdp.it
- **Telefono urgenze**: +39 06 696771 (orario ufficio)

---

## 8. Comunicazione agli interessati (Art. 34) — se rischio ALTO

### Quando comunicare
- Rischio **alto** per diritti e libertà (punteggio ≥ 8)
- Obbligatorio **senza indebito ritardo** dopo notifica autorità

### Contenuto comunicazione
1. **Cosa è successo** — linguaggio chiaro, non tecnico
2. **Quali dati** — categorie (es. "email e nome", "nessuna password")
3. **Conseguenze probabili** — cosa potrebbe accadere
4. **Misure adottate** — cosa stiamo facendo per proteggere
5. **Cosa fare l'interessato** — cambiare password, monitorare account, contattare DPO
6. **Contatti** — email DPO, numero verde, link FAQ

### Canali
- **Email** (primario) — da indirizzo ufficiale verificato
- **Notifica in-app** — banner dashboard CodeCoroner
- **Sito web** — banner homepage se vasta scala

### Eccezioni (Art. 34(3))
Non comunicare se:
- Dati cifrati con chiave non compromessa (AES-256, chiave HSM)
- Misure successive rendono rischio non più probabile (es. reset password forzato)
- Comunicazione richiede sforzo sproporzionato → comunicazione pubblica equivalente

---

## 9. Documentazione interna (Art. 33(5))

Registro violazioni (`docs/gdpr/breach-register.md` o DB):

| Campo | Esempio |
|---|---|
| ID incidente | `INC-2026-09-10-001` |
| Data/ora rilevazione | 2026-09-10 14:32 UTC |
| Data/ora notifica autorità | 2026-09-10 16:15 UTC |
| Tipo violazione | Accesso non autorizzato DB / Esfiltrazione / Perdita dispositivo |
| Dati coinvolti | Email, nome, hash password (bcrypt) |
| N. record / interessati | 247 utenti |
| Valutazione rischio | Medio (punteggio 6) |
| Misure contenimento | Revoca token, reset password forzato, blocco IP |
| Misure rimediation | Rotazione chiavi, audit log, patch vulnerabilità |
| Notifica autorità | Sì / No (con motivazione) |
| Comunicazione interessati | Sì / No |
| Chiusura incidente | 2026-09-12 10:00 UTC |
| Lezioni apprese | Patch X, miglioramento monitoraggio Y |

---

## 10. Template email notifica autorità

```
OGGETTO: Notifica violazione dati personali Art. 33 GDPR — [Organizzazione] — INC-YYYY-MM-DD-NNN

Spett.le Garante per la Protezione dei Dati Personali,

Si notifica, ai sensi dell'Art. 33 GDPR, una violazione di dati personali rilevata in data [GG/MM/AAAA] ore [HH:MM] UTC.

1. Natura della violazione: [es. Accesso non autorizzato a database tramite vulnerabilità CVE-XXXX-YYYY]
2. Categorie di dati: [es. Email, nome utente, hash password bcrypt]
3. Numero record interessati: [N]
4. Numero interessati stimati: [N]
5. Probabili conseguenze: [es. Possibile furto identità se password deboli; hash bcrypt mitigano rischio]
5. Misure adottate: [Revoca token, reset password forzato, blocco IP, patch vulnerabilità, rotazione chiavi]
6. DPO: [Nome], [email], [telefono]

Restiamo a disposizione per ogni chiarimento.

Cordiali saluti,
[Nome DPO / Legal Counsel]
[Organizzazione]
```

---

## 11. Template email interessati (Art. 34)

```
OGGETTO: Importante — Informazione su un incidente di sicurezza che coinvolge i tuoi dati

Gentile [Nome],

Ti informiamo che in data [GG/MM/AAAA] abbiamo rilevato un incidente di sicurezza che ha coinvolto alcuni tuoi dati personali conservati su CodeCoroner.

**Cosa è successo**: [Descrizione semplice, es. "Un accesso non autorizzato al nostro database ha esposto email e nomi utente. Le password sono protette da hash bcrypt e non sono state compromesse."]

**Quali dati**: [Elenco categorie, es. "Email, nome utente. Nessuna password in chiaro, nessun dato di pagamento."]

**Cosa stiamo facendo**: [Elenco misure, es. "Abbiamo revocato tutte le sessioni attive, forzato il reset password, patchato la vulnerabilità, rafforzato il monitoraggio."]

**Cosa puoi fare tu**: [Azioni concrete, es. "Cambia la tua password su CodeCoroner e su ogni altro sito dove usi la stessa password. Attiva l'autenticazione a due fattori se disponibile."]

Per domande: dpo@codecoroner.example | +39 XXX XXXXXXX

Ci scusiamo per l'inconveniente. La sicurezza dei tuoi dati è la nostra priorità.

Cordiali saluti,
Il team CodeCoroner
```

---

## 12. Review post-incidente (T+30g)

Entro 30 giorni dalla chiusura:
1. **Root Cause Analysis** tecnica completa
2. **Aggiornamento misure** (patch, config, monitoraggio, formazione)
5. **Aggiornamento DPIA** se necessario
6. **Report lezioni apprese** condiviso con team + board
6. **Test** di verifica efficacia nuove misure

---

## 13. Contatti emergenza

| Ruolo | Nome | Telefono (24/7) | Email | PEC |
|---|---|---|---|---|
| Incident Commander | | | | |
| DPO | | | | |
| Security Engineer | | | | |
| Legal Counsel | | | | |
| Hosting Provider (support) | | | | |

---

**Approvato da**: ________________________  **Data**: _______________
**DPO**: ________________________  **Data**: _______________