# Arafat Codex - storefront, wallet & admin panel

A Telegram Mini App storefront with a FastAPI backend, Firestore as the
database, wallet top-ups with auto-verified Binance Pay deposits, and an
admin panel to manage products/packages, payment methods, and orders.

## ⚠️ Before anything else: rotate your Firebase key

The Firebase service account (private key, project id, everything) was
pasted in plaintext earlier in this chat. Treat it as compromised regardless
of where it ends up next:

1. Firebase Console → Project Settings → Service Accounts →
   **Manage service account permissions** → find that key → **delete/disable it**.
2. Generate a brand new private key and save it locally as
   `backend/secrets/firebase-service-account.json` (already gitignored).
3. Never paste a real private key into a chat, ticket, or commit again -
   reference it by file path or env var instead, the way `.env.example` does.

The same goes for the default admin password shown in your notes
(`FREE_FIRE_NO_1`) - it's only used once, to bootstrap the very first admin
account, and is bcrypt-hashed before it ever touches the database. Change it
from the admin panel immediately after your first login.

## What's included

- **backend/** - FastAPI app: products, wallet/deposits, orders, admin auth,
  settings, nickname lookup. Binance Pay verification is your `app.py` logic
  adapted into a web endpoint (same approach, same checks, now backed by
  Firestore instead of local JSON files so it's safe to run more than one
  instance).
- **frontend/** - the storefront pages (home, package picker, checkout,
  wallet, account, orders) styled to match your existing arafatcodex.shop,
  plus **frontend/admin/** for the dashboard.
- **firestore/** - the data model and security rules.

## What's intentionally *not* included

The "auto likes" delivery (`bot.py` in your notes) isn't implemented here.
Free Fire's "likes" are a per-account social feature with no official way to
buy them - services that sell bulk likes deliver them by automating many
accounts (or an undocumented Garena endpoint) against a target profile.
That's account automation / platform manipulation against Garena's terms,
which isn't something I'll build the mechanics of.

Everything around it is still here and works normally: orders get created,
paid for out of the wallet, and land in `orders` with status
`pending_fulfillment`. `backend/app/fulfillment.py` is the single hook where
delivery happens - by default it just flags the order for a human to
fulfill and mark "Mark fulfilled" in the admin panel. If you already run
your own fulfillment process, that's the one file to wire it into.

The "check nickname" lookup **is** included, since it's just a call to a
public endpoint (yours, or whichever one you set in Settings). Worth
knowing: it's a third-party, unofficial API with no published reliability
guarantee (and the `"api_owner": "ETHICAL HACKER BD"` field in its response
is a sign it wasn't built with Garena's involvement) - checkout doesn't
depend on it succeeding, so an outage there won't block a purchase.

## Setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values, see below
uvicorn app.main:app --reload --port 8000
```

Required before it'll run:
- `FIREBASE_CREDENTIALS_PATH` → your **rotated** service account JSON (above)
- `JWT_SECRET` → any long random string (`openssl rand -hex 32`)
- `BINANCE_API_KEY` / `BINANCE_API_SECRET` → same keys your CLI script used
- `ADMIN_BOOTSTRAP_EMAIL` / `ADMIN_BOOTSTRAP_PASSWORD` → for first admin login

Then open `frontend/index.html` behind whatever web server you deploy it
with, and set `window.ARAFAT_API_BASE_URL` (top of `frontend/js/api.js`, or
a `<script>` before it loads) to your backend's URL. For the Telegram Mini
App, register the same URL as your bot's Web App URL via @BotFather.

bKash and Nagad endpoints are stubbed (`501 Not Implemented`) until you add
their real merchant credentials to `.env` and fill in the two `TODO`s in
`backend/app/routers/wallet.py` - those need signing up for their
merchant/PGW programs first, there's no way around that step.

## Admin panel

`frontend/admin/login.html` → log in with your bootstrap email/password →
manage products & packages, toggle payment methods on/off, set the Binance
Pay ID and minimum deposit, swap the nickname API, and process orders.
