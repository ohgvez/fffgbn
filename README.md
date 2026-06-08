# ✈️ Flight Price Alert

Controlla automaticamente i prezzi su Google Flights ogni 2 ore e ti avvisa su Telegram.

## Setup in 10 minuti

### 1. Crea il bot Telegram
1. Apri Telegram e cerca **@BotFather**
2. Scrivi `/newbot` e segui le istruzioni
3. Copia il **token** che ti dà (es. `7123456789:AAF...`)
4. Cerca **@userinfobot** e scrivici `/start` → copia il tuo **Chat ID**

### 2. Crea il repo GitHub
1. Vai su [github.com](https://github.com) → **New repository**
2. Nome: `flight-alert`, privato ✓
3. Carica tutti questi file nel repo

### 3. Aggiungi i secrets
Nel repo GitHub → **Settings → Secrets and variables → Actions → New repository secret**:
- `TELEGRAM_TOKEN` → il token del bot
- `TELEGRAM_CHAT_ID` → il tuo chat ID

### 4. Attiva GitHub Actions
- Vai su **Actions** nel repo → clicca **"I understand my workflows, enable them"**
- Per testare subito: **Actions → Flight Price Alert → Run workflow**

## Modifica le ricerche
Edita `searches.json` direttamente su GitHub. I campi:
- `origins`: aeroporti di partenza (MXP, LIN, BGY o combinazioni)
- `destination`: città/aeroporto oppure `"ANYWHERE"` per ovunque
- `months`: mesi da cercare (6=giugno, 7=luglio, 8=agosto)
- `min_nights` / `max_nights`: durata del viaggio
- `max_price_eur`: budget massimo per persona
- `passengers`: numero passeggeri

## Costo
€0 — GitHub Actions gratuito fino a 2000 minuti/mese.
