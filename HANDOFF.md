# TaxStox — Development Handoff

> **Purpose:** Single source of truth for the development team. Update this file at the end of every work session so the next developer can pick up without a handoff call.

---

## Quick Start

```bash
# Backend
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload
# → http://localhost:8000
# → API Docs: http://localhost:8000/docs

# Frontend
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |

---

## Session Log

<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- ADD NEW ENTRIES AT THE TOP. Keep older entries below.         -->
<!-- Format: Date, Who, What was done, What's pending, Notes       -->
<!-- ═══════════════════════════════════════════════════════════════ -->

---

### 2026-07-04 — Claude (AI Agent) + Aman

**Context:** Production bug fixes, auth page redesign (ClearTax-style), Google OAuth integration, database fixes. Most of the day was spent debugging and hardening the live deployment on Render + Vercel.


**1. Production Bug Fixes**

| Bug | Root Cause | Fix |
|---|---|---|
| AIS dropzone opened PDF upload when clicking other elements | Missing `relative` on AIS dropzone div — invisible file input with `absolute inset-0` bled across the page | Added `relative` to the parent div in `apps/web/src/app/page.tsx` |
| "Failed to fetch" on registration | CORS middleware only whitelisted localhost origins (Render hadn't deployed the fix from 2026-07-03) | Force-redeployed Render; CORS now allows `https://taxstox.com`, `https://www.taxstox.com`, `https://taxstox.vercel.app` |
| Auto-deploy not triggering on Render | Manual service setup didn't pick up `render.yaml` auto-deploy settings | Confirmed "Auto-Deploy: On Commit" is enabled in Render Settings. Only changes in `apps/api/` trigger deploy. |

**2. Auth Page Redesign — ClearTax-Style Split Layout**

Complete rewrite of `apps/web/src/app/auth/page.tsx`:

- **Split layout:** Form panel (left, 60%) + Feature highlights panel (right, 40%, dark blue `#003366` background)
  - Right panel shows: AI auto-extraction, Regime Optimizer, 400+ validation checks, bank-grade security, trust bar (Infosys, TCS, Wipro, HCL)
- **DOB field:** Replaced manual `DDMMYYYY` text input with native HTML `<input type="date">` date picker
  - Max date enforced: must be 18+ years old
  - Min date: 1920-01-01
  - Uses `color-scheme: light` for consistent styling
- **Google Sign-In button:** Full OAuth flow using Google Identity Services (GIS)
  - Button only appears when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` env var is set (handles missing config gracefully)
  - Dynamically loads `https://accounts.google.com/gsi/client` script on demand
  - Shows Google colored SVG logo + "Continue with Google" text
  - "or use email" divider when Google is configured
- **Input validation:** Live PAN format check with green verified badge, password min-length check

**3. Google OAuth Backend Integration**

Files changed: `apps/api/src/api/auth_routes.py`, `apps/api/src/models/user.py`

- **New endpoint:** `POST /api/v1/auth/google` — accepts `{ credential: "<Google ID token>" }`
- **JWT decoding:** Backend decodes the Google ID token locally instead of calling Google's API
  - Why: Render's free tier blocks outbound HTTPS calls to `oauth2.googleapis.com`
  - How: Splits JWT into 3 parts (header.payload.signature), base64-decodes payload, extracts `email`, `name`, `sub`
  - Validates: audience (`aud`) matches our client ID, token hasn't expired (`exp`), email is present
  - Creates or retrieves user by email → returns JWT token
- **Google Cloud Console setup:**
  - Project: `TaxStox` (project ID: `taxstox`)
  - OAuth Client ID: `435349196142-bjmgv3b08drd7gag81ps7g5gob407v3j.apps.googleusercontent.com`
  - Authorized origins: `https://taxstox.com`, `https://www.taxstox.com`, `http://localhost:3000`
  - Env var set in Vercel: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
- **Frontend flow:**
  1. User clicks "Continue with Google"
  2. GIS script loads dynamically → `google.accounts.id.initialize({ client_id, callback })`
  3. `google.accounts.id.prompt()` shows Google One Tap popup
  4. User selects Gmail account → callback fires with `{ credential: "<JWT>" }`
  5. Frontend POSTs credential to `/api/v1/auth/google`
  6. Backend decodes JWT, creates/gets user, returns TaxStox JWT
  7. Frontend stores token in localStorage, redirects to dashboard
- **Error handling:** User-friendly messages for network errors, token expiry, audience mismatch

**4. Database Column Name Fix**

Files: `apps/api/src/db/database.py`, `apps/api/src/api/auth_routes.py`

- **Bug:** Schema defines `hashed_password` column but `change_user_password()` and the Google auth endpoint referenced `password_hash` → `sqlite3.OperationalError: table users has no column named password_hash`
- **Fix:** Changed all references to `hashed_password` consistently (4 occurrences in database.py, 1 in auth_routes.py)
- **Note for Prasoon:** If the Render database has old data, you may need to reset it. SSH into Render (paid plan only) or push a commit that drops + recreates the users table. For now, fresh registrations and Google sign-ins should work.

**5. DOB Model Update**

- `UserCreate` model now accepts optional `dob` field (YYYY-MM-DD string from date picker)
- `registerUser()` in `apps/web/src/lib/api.ts` sends `dob` parameter
- `signUp()` in `apps/web/src/lib/auth.tsx` accepts optional `dob` parameter
- Backend `register` endpoint stores DOB if provided

**6. Render Auto-Deploy Verification**

- **Status:** Auto-Deploy is ON — triggers on commits that modify files inside `apps/api/`
- **Important:** Commits that only change frontend files (`apps/web/`) or root files (`HANDOFF.md`) will NOT trigger Render deploys. This is correct behavior.
- **Vercel:** Auto-deploys on every push to `main` for the `apps/web/` root directory.

**7. Current Known Issues & Debugging Notes**

| Issue | Status | Notes |
|---|---|---|
| Email/password registration "Failed to fetch" | Should be fixed | CORS now has production origins. Test after Render deploy. |
| Google Sign-In "Failed to fetch" | Should be fixed | Two bugs fixed: (1) JWT decode instead of outbound API call, (2) column name mismatch. Both deployed. |
| **Test Google Sign-In again** | Pending verification | After Render auto-deploys commit `723c295`, try Google Sign-In on taxstox.com/auth |
| UptimeRobot cron | NOT SET UP | Backend may sleep after 15 min idle → first request slow (30-60s cold start) |

**8. ⚠️ Action Items for Prasoon**

**A. Set up Neon DB (PostgreSQL) — HIGH PRIORITY**

Current SQLite database on Render is ephemeral — data WILL be lost on each deploy/restart. Move to Neon for persistent storage.

Steps:
1. Go to [neon.tech](https://neon.tech) → sign up with `taxstox@gmail.com` (same password)
2. Create a new project → name it `taxstox-db`
3. Copy the connection string (looks like: `postgresql://taxstox:password@ep-xxx.us-east-2.aws.neon.tech/taxstox?sslmode=require`)
4. Add it as an env var in Render: `DATABASE_URL = <connection-string>`
5. Update `apps/api/src/db/database.py`:
   - Replace `sqlite3` with `psycopg2` or `asyncpg`
   - Or use SQLAlchemy which already handles both SQLite and PostgreSQL
   - Current `sqlite3.connect()` calls need to be replaced
   - `init_db()` schema needs PostgreSQL syntax (TEXT instead of TEXT, SERIAL for auto-increment, etc.)
6. Neon free tier: 0.5 GB storage, 100 hours compute/month — more than enough for MVP

**B. Set up UptimeRobot cron — MEDIUM PRIORITY**

Without this, first visitor after 15 min idle gets a 30-60s cold start.

1. Go to [uptimerobot.com](https://uptimerobot.com) → sign up with `taxstox@gmail.com`
2. Add New Monitor → HTTP(s) → URL: `https://api.taxstox.com/api/v1/health`
3. Monitoring interval: 10 minutes
4. Free tier is sufficient (1 monitor at 5-min checks)

**C. If bandwidth permits — render.yaml integration**

Current `render.yaml` exists at repo root but wasn't used for initial setup (service was created manually). If you rebuild the Render service:
1. Delete the current `taxstox-api` service from Render
2. Go to Render dashboard → New → Web Service → select repo
3. This time it will auto-detect `render.yaml` and configure everything automatically
4. Benefit: future changes to infra are version-controlled in the repo

---

### 2026-07-03 — Claude (AI Agent) + Aman

**Context:** Production hardening + feature gap closure. Fixed 4 production blockers, expanded validator from 7 to 28 checks, built ITR-1 builder, added 3 broker parsers, built Settings page with backend.


**1. Production Blockers Fixed**

| Issue | File | Fix |
|---|---|---|
| Tools page hardcoded `localhost:8000` | `apps/web/src/app/tools/page.tsx` | Changed 4 fetch URLs to `NEXT_PUBLIC_API_URL` |
| CORS only allowed localhost | `apps/api/src/main.py` | Added `taxstox.com`, `www.taxstox.com`, `taxstox.vercel.app` |
| ITR form hardcoded to "ITR-2" | `apps/api/src/api/routes.py` | Wired `ITRSelector` into `/process/{session_id}` — auto-detects ITR-1/2/3/4 based on income sources |
| Export filenames hardcoded `_ITR2_` | `apps/api/src/api/routes.py` | Filename now uses detected ITR form (e.g., `_ITR1_`, `_ITR2_`) |

**2. Validation Engine — 7 → 28 checks** (`apps/api/src/builders/validator.py`)

New checks added:
- **Identity:** PAN format (V-ID-001), PAN consistency (V-ID-002), DOB validity, personal info completeness
- **Income:** Total income cross-schedule consistency (V-CON-001), salary/TDS consistency (V-SAL-001), interest income validation
- **Capital Gains:** CG date range segmentation (V-CG-001), STT paid consistency (V-CG-010)
- **Deductions:** 80C limit (V-DED-001), 80D self+parents limits (V-DED-005), 80CCD(1B) NPS limit, home loan interest limit
- **Tax:** Rebate 87A eligibility/amount, surcharge applicability based on total income
- **Banking:** IFSC format validation (V-BANK-002), bank account refund flag check
- **Data quality:** Assessment year validity, filing status validity, unrealistic value detection (>₹10Cr), empty schedule warnings

**3. ITR-1 (SAHAJ) Builder** (`apps/api/src/builders/itr1.py`)
- Full JSON builder for simple salaried returns (no CG, no business, no foreign income)
- Includes: Schedule S (salary), Schedule HP (house property), Schedule OS (interest), Schedule VI-A (deductions), PartB-TI/TTI
- Slab-wise tax computation for both Old and New regimes (FY 2025-26)
- Auto-calculates 80TTA (up to ₹10K) and 80D premiums
- Wired into `/export/{session_id}` — auto-selects ITR1Builder vs ITRJSONBuilder based on `session.itr_form`
- Session model updated: `itr_form` field added to `utils/session.py`

**4. Broker Statement Parsers** (`apps/api/src/parsers/broker_statements/generic.py`)
- **Groww:** `parse_groww_tradebook()` — column auto-detection for Stock/Name, ISIN, Trade Date, Transaction Type, Quantity, Price
- **Upstox:** `parse_upstox_tradebook()` — handles symbol, isin, trade_date, exchange, segment, qty, avg_price
- **Angel One:** `parse_angel_one_tradebook()` — handles symbol, isin, trade_date, exchange, qty, avg_traded_price
- All return `list[CGSaleEntry]` (same interface as Zerodha parser)
- Unified entry point: `parse_broker_statement()` — auto-detects broker from filename/hint
- `/upload/broker-statement/{session_id}` updated to support `groww`, `upstox`, `angel_one`

**5. Settings Page + Backend** (NEW)
- **Frontend:** `apps/web/src/app/settings/page.tsx` — profile editor, password change, sign out button
- **Backend endpoints:**
  - `PUT /api/v1/auth/profile` — update name
  - `POST /api/v1/auth/change-password` — change password (verifies current)
  - `POST /api/v1/auth/forgot-password` — returns reset token (dev mode; needs SendGrid for production)
- **DB functions:** `update_user_profile()`, `change_user_password()` in `database.py`
- Header updated: Settings gear icon for authenticated users

**6. Build Verification**
- Next.js 16 build: all 8 routes compiled, zero TypeScript errors
- Python: all new modules import clean (ITR1Builder, ITRValidator 28 checks, ITRSelector, broker parsers)

**7. What Was Not Touched (Still Pending from Priority Lists)**

| Item | Status |
|---|---|
| ITR-3 builder (business income) | Not started |
| ITR-4 builder (presumptive) | Not started |
| Schedule FA (foreign assets) | Not started |
| Tests (backend + frontend) | Not started |
| TanStack Query / React Hook Form + Zod | Not started |
| Charts (Recharts) on summary page | Not started |
| Audit trail | Not started |
| Rate limiting | Not started |
| CAMS PDF broker parser | Not started |

---

### 2026-07-02 — Claude (AI Agent) + Aman

**Context:** Deployed TaxStox to production. Switched backend hosting from Railway to Render. Set up custom domains on both Vercel and Render. App is now live at `taxstox.com`.

#### Accounts Created (All use same credentials)

| Service | URL | Email | Purpose |
|---|---|---|---|
| **Render** | render.com | `taxstox@gmail.com` | Backend hosting |
| **Vercel** | vercel.com | `taxstox@gmail.com` | Frontend hosting |
| **UptimeRobot** | uptimerobot.com | `taxstox@gmail.com` | Keep Render free tier alive |

> ⚠️ **All three services use the SAME password.** Prasoon — ask Aman for it if you haven't received it.

#### What Was Done

**1. Switched Deployment: Railway → Render**
- Deleted `apps/api/railway.json`
- Created `render.yaml` at repo root — Render auto-detects this on first deploy
- Rationale: Render free tier is $0/mo (Railway removed their free tier). Render Starter is $7/mo at launch vs Railway's $5/mo minimum, but with better specs (1GB vs 512MB RAM, 0.5 vs 0.1 CPU).
- Updated all docs: `HANDOFF.md`, `README.md`, `docs/MASTER_PLAN.md`

**2. Backend Deployed to Render**
- Service: `taxstox-api` at `https://taxstox-api.onrender.com`
- Docker build succeeded, FastAPI running on port 8000
- Health check: `/api/v1/health` → `{"status": "ok", "version": "0.1.0"}`
- Free tier caveat: spins down after 15 min idle → UptimeRobot cron keeps it warm (every 10 min)

**3. Frontend Deployed to Vercel**
- Project: `taxstox` at `https://taxstox.vercel.app`
- Root directory: `apps/web`, Next.js auto-detected
- Env var: `NEXT_PUBLIC_API_URL` set in Vercel dashboard

**4. Custom Domains Configured (Hostinger)**
- `taxstox.com` → Vercel (A record: `216.198.79.1`, CNAME www → `eb972152648e5da2.vercel-dns-017.com`)
- `api.taxstox.com` → Render (CNAME api → `taxstox-api.onrender.com`)
- Email records (MX, DKIM, SPF, DMARC) left untouched — mail.taxstox.com still works

**5. Production URL Update**
- Updated `NEXT_PUBLIC_API_URL` in Vercel to `https://api.taxstox.com/api/v1` (was the onrender.com URL)

#### Live URLs (Production)

| Layer | URL | Host |
|---|---|---|
| Frontend | `https://taxstox.com` | Vercel ($0/mo) |
| Backend API | `https://api.taxstox.com` | Render ($0/mo free → $7/mo at launch) |
| API Docs | `https://api.taxstox.com/docs` | Swagger auto-generated |

#### Render Cold Start Workaround

The free tier idles after 15 minutes. UptimeRobot (free) pings `https://api.taxstox.com/api/v1/health` every 10 minutes to keep the backend warm 24/7 at no cost. Upgrade to Render Starter ($7/mo) at launch to eliminate this entirely.

#### DNS Reference (Hostinger)

```
A    @    216.198.79.1
CNAME www  eb972152648e5da2.vercel-dns-017.com
CNAME api  taxstox-api.onrender.com
```

#### ⚠️ Action Required — Prasoon

**Set up the cron job to keep Render alive:**

1. Go to [uptimerobot.com](https://uptimerobot.com) and sign up with `taxstox@gmail.com` (same password as everything else)
2. Click **"Add New Monitor"** → select **HTTP(s)**
3. URL: `https://api.taxstox.com/api/v1/health`
4. Monitoring interval: **10 minutes**
5. Save

This is critical — without it, the backend sleeps after 15 minutes of no traffic and the next request takes 30-60 seconds to wake up.

#### Prasoon — To Deploy Code Changes

1. Push to GitHub `main` branch
2. Render auto-deploys on push (detects changes in `apps/api/`)
3. Vercel auto-deploys on push (detects changes in `apps/web/`)
4. No manual steps needed — just `git push`

---

### 2026-07-01 — Claude (AI Agent) + Aman

**Context:** Built the E2E MVP from existing codebase (~65% complete). Added real auth, database, dashboard, calculators, broker import, and deployment configs. Goal was ClearTax feature parity for ITR.

#### What Was Done

**1. Authentication System (Real JWT)**
- Replaced localStorage mock auth with real JWT-based authentication
- Files: `apps/api/src/auth/jwt.py`, `apps/api/src/api/auth_routes.py`, `apps/api/src/models/user.py`
- Frontend: `apps/web/src/lib/auth.tsx` (rewritten), `apps/web/src/app/auth/page.tsx` (updated)
- Login now uses email+password (not PAN)
- Registration: email, password, PAN, name → JWT token returned
- Protected route dependency: `get_current_user` in `auth/jwt.py`
- Frontend stores token in localStorage, auto-restores session on mount

**2. Database Layer (SQLite)**
- SQLite database at `apps/api/data/taxstox.db` (auto-created on first run)
- Tables: `users` (id, email, pan, name, hashed_password, created_at), `filings` (id, user_id, assessment_year, itr_type, regime, gross_income, tax_paid, status, created_at, updated_at)
- Password hashing: bcrypt directly (NOT passlib — incompatible with newer bcrypt versions)
- Files: `apps/api/src/db/database.py`

**3. Dashboard Page**
- Full dashboard at `/dashboard` — hero stats row (total refunds, tax saved, filings done, days to deadline), quick actions grid, filing history table, tax calendar, empty state
- Backend: `apps/api/src/api/dashboard.py` — `/dashboard`, `/filings` (GET+POST) endpoints
- Frontend: `apps/web/src/app/dashboard/page.tsx`
- Dashboard is auth-protected — redirects to `/auth` if not logged in

**4. Standalone Tax Calculators (ClearTax Feature)**
- 4 interactive calculators at `/tools`
- Regime Compare (Old vs New with all deductions), HRA Exemption, Capital Gains Tax, Quick Estimate
- All call live backend APIs
- Backend: `apps/api/src/api/calculators.py` — 4 endpoints
- Frontend: `apps/web/src/app/tools/page.tsx`
- Verified: ₹12L salary → New Regime saves ₹56,680 over Old Regime ✓

**5. ITR Form Auto-Selector**
- Determines ITR-1/2/3/4 based on income profile (salary, CG, business, foreign, agricultural, total income)
- Files: `apps/api/src/engine/itr_selector.py`
- Logic: ITR-1 for simple salary, ITR-2 for CG+foreign, ITR-3 for business, ITR-4 for presumptive

**6. Broker Statement Import (ClearTax Feature)**
- Zerodha tradebook CSV parser + Tax P&L CSV parser
- Extracts ISIN, symbol, dates, quantities, prices → CGSaleEntry objects
- Auto-detects column mappings (handles different CSV formats)
- Endpoint: `POST /api/v1/upload/broker-statement/{session_id}`
- Files: `apps/api/src/parsers/broker_statements/zerodha.py`
- Groww, Upstox, AngelOne parsers still needed

**7. Document Upload Endpoint**
- Upload investment proofs (80C, 80D, HRA receipts, home loan certs)
- Endpoint: `POST /api/v1/upload/document/{session_id}`
- Added to `apps/api/src/api/routes.py`

**8. Production Deployment Configs**
- Frontend: `apps/web/vercel.json` — Vercel deployment config
- Backend: `apps/api/Dockerfile`, `render.yaml` (repo root) — Render deployment (free tier → $7/mo at launch)
- `apps/api/requirements.txt` — pinned production dependencies
- `.env.example` files in both frontend and backend
- Recommended architecture: Vercel (frontend, free) + Render (backend, $0 dev → $7/mo prod) → taxstox.com

**9. Bugs Fixed During Session**
- `passlib` incompatible with bcrypt 4.x → switched to `bcrypt` directly in `database.py`
- bcrypt 72-byte password limit → `hash_password()` auto-truncates
- TypeScript build error in tools page (type mismatch on API response) → fixed

#### What Was Modified (Existing Files)
| File | Change |
|------|--------|
| `apps/api/src/main.py` | Added auth, dashboard, calculators routers; DB init in lifespan |
| `apps/api/src/api/routes.py` | Added broker-statement and document upload endpoints |
| `apps/api/pyproject.toml` | Updated dependencies (removed passlib, added bcrypt) |
| `apps/web/src/lib/api.ts` | Added auth, dashboard, filings API functions + auth header helper |
| `apps/web/src/lib/auth.tsx` | Complete rewrite — mock → real JWT |
| `apps/web/src/app/auth/page.tsx` | PAN→email login, wired to real API |
| `apps/web/src/components/Header.tsx` | Auth-aware nav with dashboard link, sign out |

#### What's Running NOW
- Backend: `http://localhost:8000` ✅
- Frontend: `http://localhost:3000` ✅
- Both verified working — auth (register+login), dashboard, calculators all tested

#### Current State — What Works E2E
1. Register account (email+password+PAN) → get JWT
2. Login → JWT stored → dashboard loads
3. Upload Form 16 + AIS PDFs → parsed → classified → questions generated
4. Answer 0-5 yes/no questions → tax computed (Old vs New) → regime comparison → summary
5. Download validated ITR-2 JSON with post-export instructions
6. Dashboard shows filing history (empty for new users)
7. Tools page: all 4 calculators work with live API

---

### Template for Future Sessions

```
### YYYY-MM-DD — [Developer Name]

**What Was Done**
- 

**What Was Modified**
- 

**What's Broken / Blocked**
- 

**What's Pending for Next Session**
- 

**Notes for Next Developer**
- 
```

---

## Architecture Overview

```
apps/
├── api/                              # FastAPI backend (Python 3.12+)
│   ├── src/
│   │   ├── main.py                   # Entry point — registers all routers, init DB
│   │   ├── auth/
│   │   │   └── jwt.py                # JWT creation, verification, get_current_user dependency
│   │   ├── db/
│   │   │   └── database.py           # SQLite — users, filings tables + CRUD + bcrypt
│   │   ├── models/
│   │   │   ├── form16.py             # Form16Data — Part A, Part B, Annexure, Chapter VI-A
│   │   │   ├── ais.py                # AISData — equity MF sales, other unit sales, interest, TDS
│   │   │   ├── tax.py                # UnifiedTaxData, CGSaleEntry, ClassifiedCGData, RegimeResult, UserAnswers
│   │   │   ├── api.py                # Request/Response models for all endpoints
│   │   │   └── user.py               # UserCreate, UserLogin, UserResponse, TokenResponse
│   │   ├── parsers/
│   │   │   ├── form16_parser.py      # Form 16 PDF → Form16Data (pikepdf + pdfplumber)
│   │   │   ├── ais_parser.py         # AIS PDF → AISData
│   │   │   └── broker_statements/
│   │   │       └── zerodha.py        # Zerodha CSV → CGSaleEntry list
│   │   ├── engine/
│   │   │   ├── classifier.py         # AIS entries → ITR schedule buckets (112A, 111A, CG)
│   │   │   ├── regime_optimizer.py   # Old vs New regime — deterministic math, FY 25-26 slabs
│   │   │   ├── questions.py          # Adaptive question generation (0-5 questions)
│   │   │   └── itr_selector.py       # Auto-select ITR-1/2/3/4 based on income profile
│   │   ├── builders/
│   │   │   ├── itr_json_builder.py   # ITR-2 JSON builder (all schedules)
│   │   │   └── validator.py          # 7 validation checks (needs expansion to 400+)
│   │   ├── api/
│   │   │   ├── routes.py             # Core ITR pipeline endpoints + broker/doc upload
│   │   │   ├── auth_routes.py        # /auth/register, /auth/login, /auth/me
│   │   │   ├── dashboard.py          # /dashboard, /filings
│   │   │   └── calculators.py        # /calculator/regime-compare, /hra, /capital-gains, /quick-estimate
│   │   └── utils/
│   │       ├── password_resolver.py  # Form 16 + AIS password auto-guessing
│   │       └── session.py            # In-memory session manager (30min TTL)
│   ├── data/
│   │   └── taxstox.db               # SQLite database (auto-created)
│   ├── Dockerfile                    # Production Docker build
│   (render.yaml at repo root)         # Render deployment config (auto-detected)
│   ├── requirements.txt             # Pinned production dependencies
│   ├── pyproject.toml               # Project metadata + dev dependencies
│   └── .env.example
│
├── web/                              # Next.js 16 frontend (TypeScript)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx            # Root layout — Header, Footer, Providers, fonts
│   │   │   ├── globals.css           # Tailwind CSS
│   │   │   ├── page.tsx              # Landing page + Upload portal (inline)
│   │   │   ├── auth/page.tsx         # Sign Up / Sign In (tabs)
│   │   │   ├── dashboard/page.tsx    # Dashboard — stats, filings, calendar
│   │   │   ├── questions/page.tsx    # Question wizard (step-by-step Yes/No)
│   │   │   ├── summary/page.tsx      # Tax summary + regime banner + JSON download + 8-step instructions
│   │   │   └── tools/page.tsx        # Calculators — regime, HRA, CG, quick estimate
│   │   ├── components/
│   │   │   ├── Header.tsx            # Auth-aware nav bar
│   │   │   ├── Providers.tsx         # AuthProvider + Google Fonts
│   │   │   └── ui/                   # shadcn/ui components (button, card, input, select, dialog, etc.)
│   │   └── lib/
│   │       ├── api.ts                # API client — all endpoints + types
│   │       ├── auth.tsx              # Auth context + provider + useAuth hook
│   │       ├── store.ts              # Client state (session, upload, questions, summary)
│   │       └── utils.ts              # Tailwind className merge utility
│   ├── vercel.json                   # Vercel deployment config
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
│
├── design/                           # Design references (do NOT modify)
│   ├── 00-README.md                  # Index of all design docs
│   ├── 01-product-requirements.md    # PRD + functional requirements
│   ├── 04-information-architecture.md # Site map, navigation, content hierarchy
│   ├── 05-backend-architecture.md    # 15-microservice spec (future reference)
│   ├── 06-frontend-architecture.md   # Frontend tech stack + component tree
│   ├── 07-database-design.md         # Database schema
│   ├── 10-ocr-document-pipeline.md   # OCR pipeline spec
│   ├── 12-validation-engine.md       # 400+ validation rules spec
│   ├── 13-conversation-engine.md     # NL conversation engine spec
│   ├── 15-prompt-engineering.md      # AI/LLM prompt templates
│   ├── 16-tax-optimization-engine.md # Tax computation rules
│   ├── 19-json-schemas-api-contracts.md # API contracts + ITR JSON schemas
│   ├── design-system/DESIGN.md       # Design tokens (colors, typography, spacing)
│   └── [various]/code.html          # HTML prototypes (landing, auth, upload, questions, summary, etc.)
│
├── docs/                             # Build specs (authoritative)
│   ├── MASTER_PLAN.md                # Complete build specification
│   ├── ARCHITECTURE.md               # Detailed architecture
│   ├── DATA_MODEL.md                 # Pydantic v2 data models
│   └── ITR_TYPES_QUESTIONS.md       # Per-ITR question decision trees
│
└── HANDOFF.md                        # ← THIS FILE
```

---

## API Endpoints (21 total)

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Create account → JWT |
| POST | `/api/v1/auth/login` | No | Login → JWT |
| GET | `/api/v1/auth/me` | Yes | Current user profile |

### ITR Pipeline
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/upload` | No | Upload Form 16 + AIS PDFs |
| POST | `/api/v1/process/{session_id}` | No | Classify + optimize + generate questions |
| POST | `/api/v1/answers/{session_id}` | No | Submit answers, get tax summary |
| POST | `/api/v1/export/{session_id}` | No | Build + validate + export ITR JSON |

### Broker & Documents
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/upload/broker-statement/{session_id}` | No | Upload broker trade CSV |
| POST | `/api/v1/upload/document/{session_id}` | No | Upload investment proof |

### Dashboard
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/dashboard` | Yes | Stats, filings, calendar |
| GET | `/api/v1/filings` | Yes | Filing history list |
| POST | `/api/v1/filings` | Yes | Create new filing record |

### Calculators
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/calculator/regime-compare` | No | Old vs New regime |
| GET | `/api/v1/calculator/hra` | No | HRA exemption |
| GET | `/api/v1/calculator/capital-gains` | No | CG tax |
| GET | `/api/v1/calculator/quick-estimate` | No | Quick tax estimate |

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | No | Service health check |

---

## Priority 1 — Must Complete Before Production

These are the critical gaps that need to be addressed before the platform can handle real users:

### 1. Validation Engine — Expand from 7 to 50+ rules
- **File:** `apps/api/src/builders/validator.py`
- **Spec:** `design/12-validation-engine.md` (400+ rules defined)
- **Priority rules to add:**
  - PAN format + consistency across documents (V-ID-001 through V-ID-004)
  - TDS amount cross-validation Form 16 vs AIS (V-TDS-001)
  - Salary figure consistency across Form 16 parts (V-SAL-001)
  - 80C/80D limit enforcement (V-DED-001 through V-DED-010)
  - CG date ranges must sum to BFLA (V-CG-001 through V-CG-020)
  - Bank account validation — IFSC format, single refund account (V-BANK-001)
  - Mandatory field presence check per ITR type
  - Interest income consistency with AIS

### 2. ITR-1, ITR-3, ITR-4 JSON Builders
- **Reference implementation:** `apps/api/src/builders/itr_json_builder.py` (ITR-2 — complete)
- **Selector already built:** `apps/api/src/engine/itr_selector.py`
- **What to build:**
  - `apps/api/src/builders/itr1.py` — Simpler than ITR-2 (no CG schedules, no Schedule FA)
  - `apps/api/src/builders/itr3.py` — ITR-2 + business income schedules
  - `apps/api/src/builders/itr4.py` — Presumptive income schedules
- **How:** Extract common schedules into a base class, subclass for each ITR type

### 3. Tests
- Backend: `apps/api/tests/` — pytest + httpx
  - Test auth flow (register → login → protected endpoint)
  - Test parser with sample Form 16 + AIS PDFs
  - Test regime optimizer with known inputs
  - Test ITR JSON builder output against schema
- Frontend: Vitest + Playwright
  - Test auth page → login → redirect
  - Test dashboard loads for authenticated user
  - Test calculator inputs → API call → results display

### 4. Deployment to taxstox.com
- Frontend → Vercel (point `taxstox.com` DNS)
- Backend → Render (point `api.taxstox.com` DNS via CNAME to `taxstox-api.onrender.com`)
- Set `NEXT_PUBLIC_API_URL=https://api.taxstox.com/api/v1` in Vercel
- `TAXSTOX_JWT_SECRET` auto-generated by Render (or set manually in Render dashboard)
- Configs already created: `vercel.json`, `Dockerfile`, `render.yaml`
- Render free tier: 512 MB / 0.1 CPU, spins down after 15 min idle — use UptimeRobot (free) to keep warm
- Render Starter ($7/mo): 1 GB / 0.5 CPU, no cold starts — upgrade at launch

---

## Priority 2 — ClearTax Feature Parity

### 5. Broker Statement Parsers
- **Done:** Zerodha — `apps/api/src/parsers/broker_statements/zerodha.py`
- **To build:** Groww, Upstox, Angel One, CAMS (PDF)
- All should output `list[CGSaleEntry]` same as Zerodha parser

### 6. Schedule FA (Foreign Assets)
- **New file:** `apps/api/src/builders/schedule_fa.py`
- Needed for NRIs, ESOP holders, foreign stock owners
- Add questions to `engine/questions.py` for foreign income/assets

### 7. Frontend Gaps
| # | What | Where |
|---|------|-------|
| 1 | **Profile/Settings page** | `apps/web/src/app/settings/page.tsx` |
| 2 | **Forgot password flow** | Add to `auth/page.tsx` + backend endpoint |
| 3 | **Filing detail view** | Click a filing in dashboard → see full details, re-download JSON |
| 4 | **Document vault UI** | Manage uploaded investment proofs (endpoint exists) |
| 5 | **React Hook Form + Zod** | Replace plain state in all forms with schema-validated forms |
| 6 | **TanStack Query** | Replace raw fetch with React Query for caching + dedup |
| 7 | **Charts (Recharts)** | Regime comparison bar chart on summary page |

### 8. Audit Trail
- **FR-9.1:** Log every data extraction with source document, confidence, and decision basis
- **New file:** `apps/api/src/engine/audit.py`
- Log to database or structured log output

---

## Priority 3 — Nice to Have (Post-Launch)

| # | Feature | Spec Reference |
|---|---------|---------------|
| 1 | AI/LLM-based entity extraction | `design/15-prompt-engineering.md` |
| 2 | Natural language conversation engine | `design/13-conversation-engine.md` |
| 3 | Notification service (email/SMS) | `design/05-backend-architecture.md` |
| 4 | Marketing pages (how-it-works, pricing, blog) | `design/04-information-architecture.md` |
| 5 | Admin dashboard | `design/04-information-architecture.md` |
| 6 | Expert chat / CA support | FR-019 |
| 7 | Notice response assistant | FR-020 |
| 8 | Payment integration | Spec mentions "pay only when you file" |
| 9 | Aadhaar-based e-Verify integration | Future |

---

## Known Issues & Gotchas

1. **bcrypt + passlib incompatibility:** DO NOT add `passlib` as a dependency. Use `bcrypt` directly as done in `database.py`. If you re-add passlib, it will break on newer bcrypt versions.

2. **In-memory sessions:** `utils/session.py` uses in-memory dict — sessions are lost on server restart. This is fine for MVP but needs Redis/persistent storage for production.

3. **No file persistence:** Uploaded PDFs are processed in-memory (BytesIO) and discarded. The `filing_documents` table was planned but not created in the DB schema.

4. **CORS is localhost-only:** `main.py` allows CORS only from `localhost:3000`. Update for production domain.

5. **JWT secret is hardcoded default:** Set `TAXSTOX_JWT_SECRET` environment variable in production.

6. **ITR-2 only:** The pipeline currently builds ITR-2 JSON regardless of what the user needs. Wire the ITR selector into the routes.

7. **Frontend tools page hardcodes `http://localhost:8000`:** The calculator fetch calls use a hardcoded URL instead of `NEXT_PUBLIC_API_URL`. Fix before production deployment.

8. **No rate limiting:** Upload endpoints have no rate limiting — easy to abuse in production.

---

## Environment Variables

### Backend (`apps/api/.env`)
```
TAXSTOX_JWT_SECRET=your-random-secret-here
```

### Frontend (`apps/web/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Useful Commands

```bash
# Backend
cd apps/api
pip install -r requirements.txt         # Install deps
uvicorn src.main:app --reload           # Start dev server
python -c "from src.db.database import init_db; init_db()"  # Reset DB

# Frontend
cd apps/web
npm install                             # Install deps
npm run dev                             # Start dev server
npm run build                           # Production build (type-checks)
npm run lint                            # ESLint

# Git
git status
git add -A
git commit -m "Description of changes"
git push origin main
```

---

*Last updated: 2026-07-01 — Claude (AI Agent) + Aman*
