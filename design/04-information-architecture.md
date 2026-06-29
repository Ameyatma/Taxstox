# 04 — Information Architecture

> **Parent:** [00-README.md](00-README.md) | **Prev:** [03 User Personas](03-user-personas-journeys.md) | **Next:** [05 Backend Architecture](05-backend-architecture.md)

---

## 1. Site Map

```
TaxStox Platform
├── PUBLIC (unauthenticated)
│   ├── /                         → Landing Page
│   ├── /how-it-works             → Product walkthrough
│   ├── /pricing                  → Pricing plans
│   ├── /about                    → Company, trust, ERI license
│   ├── /security                 → Security & privacy center
│   ├── /blog                     → Tax guides, updates
│   ├── /auth/signup              → Create account
│   ├── /auth/login               → Sign in
│   ├── /auth/forgot-password     → Password reset
│   └── /auth/verify-email        → Email verification
│
├── AUTHENTICATED
│   ├── /dashboard                → User dashboard (home)
│   │   ├── /dashboard/overview   → Stats, filing status, deadlines
│   │   ├── /dashboard/filings    → Filing history
│   │   └── /dashboard/profile    → Taxpayer profile & settings
│   │
│   ├── /file                     → Filing wizard (step-by-step)
│   │   ├── /file/new             → Start new filing
│   │   │   ├── /file/new/upload  → Document upload step
│   │   │   ├── /file/new/process → Processing (progress view)
│   │   │   ├── /file/new/qa      → Adaptive questionnaire
│   │   │   ├── /file/new/review  → Tax summary & regime comparison
│   │   │   ├── /file/new/export  → Download JSON + instructions
│   │   │   └── /file/new/done    → Completion confirmation
│   │   ├── /file/resume/:id      → Resume incomplete filing
│   │   └── /file/revise/:id      → File revised return
│   │
│   ├── /tools                    → Standalone tools
│   │   ├── /tools/regime-compare → Old vs New regime calculator
│   │   ├── /tools/hra-calculator → HRA exemption calculator
│   │   ├── /tools/capital-gains  → Capital gains calculator
│   │   └── /tools/tax-estimator  → Quick tax estimation
│   │
│   ├── /records                  → Tax records
│   │   ├── /records/documents    → Previously uploaded docs (while retained)
│   │   ├── /records/itr-jsons    → Generated ITR JSONs
│   │   ├── /records/acknowledge  → Filed acknowledgements
│   │   └── /records/26as         → Imported 26AS/AIS data
│   │
│   ├── /support                  → Help & support
│   │   ├── /support/help-center  → Knowledge base
│   │   ├── /support/notice-help  → Tax notice assistance
│   │   ├── /support/chat         → Live chat / AI chat
│   │   └── /support/contact      → Contact form
│   │
│   └── /settings                 → Account settings
│       ├── /settings/account     → Account details
│       ├── /settings/security    → Password, 2FA
│       ├── /settings/privacy     → Data & privacy controls
│       └── /settings/delete      → Account deletion
│
└── ADMIN (staff only)
    ├── /admin/er-dashboard       → ERI operations dashboard
    ├── /admin/users              → User management
    ├── /admin/filings            → Filing queue management
    ├── /admin/analytics          → Platform analytics
    └── /admin/schema-updates     → ITR schema version management
```

---

## 2. Navigation Model

### 2.1 Primary Navigation (TopAppBar)

Persistent across all authenticated pages:

```
[TaxStox Logo]  [Dashboard] [File New] [Tools ▾] [Records ▾] [Support]
                                                              [🔔] [👤]
```

- Logo: Always links to `/dashboard`
- Dashboard: Active when on any `/dashboard/*` route
- File New: Primary CTA, always visible
- Tools: Dropdown with regime compare, HRA calc, capital gains calc, tax estimator
- Records: Dropdown with documents, ITR JSONs, acknowledgements
- Support: Dropdown with help center, notice help, chat, contact
- Notifications bell: Badge for unread notifications
- User avatar: Dropdown with profile, settings, logout

### 2.2 Filing Wizard Navigation

During active filing, the wizard takes over:

```
[← Back to Dashboard]  [Step 2 of 5: Review Your Income]  [Save & Exit]
─────────────────────────────────────────────────────────────
[████████░░░░░░░░░░░░░░░░░░░░] 40%
```

- No top nav — focused wizard experience
- Progress bar shows completion
- Back button returns to dashboard (with save prompt)
- Save & Exit persists session state

### 2.3 Mobile Navigation

Bottom tab bar replaces top nav:

```
[🏠 Home] [📄 File] [🧮 Tools] [📋 Records] [👤 Profile]
```

---

## 3. Content Hierarchy

### 3.1 Dashboard Page Structure

```
Dashboard
├── HERO STATS ROW (4 cards)
│   ├── Total Refunds (₹ amount, across all filings)
│   ├── Tax Saved (₹ amount, via optimization)
│   ├── Filings Done (count, all verified)
│   └── Deadline Countdown (days remaining)
│
├── QUICK ACTIONS GRID (2×2)
│   ├── File New ITR (primary action)
│   ├── Download Last JSON
│   ├── Regime Calculator
│   └── File Revised Return
│
├── FILING HISTORY TABLE
│   ├── Assessment Year
│   ├── ITR Type
│   ├── Regime
│   ├── Gross Income
│   ├── Tax Paid
│   ├── Status (Filed / Processing / Draft / Rejected)
│   └── Actions (Download JSON, Download Ack, View Details)
│
├── TAX CALENDAR (sidebar or bottom card)
│   ├── July 31 — ITR Deadline
│   ├── December 31 — Belated Return Deadline
│   ├── March 15 — Advance Tax 4th Installment
│   └── June 15 — Advance Tax 1st Installment
│
└── RECENT ACTIVITY FEED
    ├── "ITR-2 for AY 2025-26 was filed on June 25, 2026"
    ├── "Refund of ₹14,500 credited to bank account"
    └── "TDS mismatch detected — resolved"
```

### 3.2 Filing Wizard Content Flow

```
STEP 1: UPLOAD
├── Instruction: "Upload your Form 16 and AIS PDF"
├── Drag & drop zone
├── Recent documents quick-select (if any)
├── Skip option: "I don't have documents — let's do this manually"
├── Processing state (after upload):
│   ├── Parsing document... [progress bar]
│   ├── Classifying income sources...
│   └── Applying tax optimizations...
└── Success: "We found 14 income entries and ₹2,45,000 in eligible deductions"

STEP 2: VERIFY EXTRACTED DATA
├── "Here's what we found. Please verify."
├── PAN, Name, DOB (auto-verified)
├── Salary Components (expandable table)
│   ├── Basic: ₹X — Source: Form 16, Page 2 ✓
│   ├── HRA: ₹Y — Source: Form 16, Page 2 ✓
│   └── ...etc
├── Other Income (if any)
├── TDS Details
├── Edit/Correct buttons for each value
└── "Looks correct → Continue"

STEP 3: ADAPTIVE QUESTIONS (2-5 questions)
├── Question generated based on profile gaps
├── Examples:
│   ├── "Do you live in rented accommodation?" (if HRA in Form 16)
│   ├── "Did you make any PPF/NPS/ELSS investments?" (80C gap)
│   ├── "Do you have a home loan?" (80EEA potential)
│   ├── "Any medical insurance premiums paid?" (80D)
│   └── "Did you sell any stocks or mutual funds this year?"
├── Each question: Yes/No → if Yes → detail follow-up
├── Skip allowed for non-critical questions
└── Progress: "Question 3 of 5"

STEP 4: REVIEW & OPTIMIZE
├── REGIME COMPARISON (side-by-side)
│   ├── Old Regime column
│   ├── New Regime column
│   ├── Highlighted winner with savings amount
│   └── "Switch to New Regime" / "Keep Old Regime" buttons
├── INCOME SUMMARY
│   ├── Salary Income: ₹X
│   ├── House Property: ₹Y
│   └── Other Sources: ₹Z
├── DEDUCTION DETAILS
│   ├── 80C: ₹X (PPF, LIC, ELSS...)
│   ├── 80D: ₹Y (Health Insurance)
│   ├── HRA Exemption: ₹Z
│   └── Standard Deduction: ₹50,000
├── TAX COMPUTATION
│   ├── Gross Tax: ₹X
│   ├── Rebate 87A: -₹Y
│   ├── TDS/TCS: -₹Z
│   ├── Net Tax Payable / Refund: ₹W
│   └── Interest (if applicable): 234A/B/C
├── EXPLAIN MY TAX (expandable)
│   ├── "Why is New Regime better for me?"
│   ├── "What deductions did we apply?"
│   └── "What if I invest more in 80C?"
└── OPTIMIZATION SUGGESTIONS
    ├── "Invest ₹50K more in NPS → Save ₹15,600"
    └── "Claim your medical bills → Save ₹5,000"

STEP 5: EXPORT
├── "Your ITR JSON is ready!"
├── Download button (primary)
├── Filing instructions (8 steps specific to ITR type)
├── Cross-check values for portal verification
├── "What if the portal rejects my JSON?" — troubleshooting
└── Support contact
```

---

## 4. Navigation State Machine

```
                    ┌──────────┐
                    │  LANDING  │
                    └────┬─────┘
                         │ (Sign Up / Login)
                    ┌────▼─────┐
               ┌────│ DASHBOARD │◄──────────────┐
               │    └────┬─────┘                │
               │         │ (File New)           │ (Save & Exit)
               │    ┌────▼─────┐                │
               │    │  UPLOAD   │               │
               │    └────┬─────┘                │
               │         │ (Documents processed) │
               │    ┌────▼─────┐                │
               │    │  VERIFY   │               │
               │    └────┬─────┘                │
               │         │ (Data confirmed)      │
               │    ┌────▼─────┐                │
               │    │ QUESTION  │───────────────┘
               │    └────┬─────┘
               │         │ (All questions answered)
               │    ┌────▼─────┐
               │    │  REVIEW   │
               │    └────┬─────┘
               │         │ (User confirms)
               │    ┌────▼─────┐
               │    │  EXPORT   │
               │    └────┬─────┘
               │         │ (JSON downloaded)
               │    ┌────▼─────┐
               │    │   DONE    │
               │    └──────────┘
               │
               └──── (Revised Return flow re-enters at UPLOAD)
```

---

## 5. Search & Filter Architecture

### 5.1 Global Search
- Search across: filing history, tax records, help articles
- Scope: current user's data only
- Implementation: PostgreSQL full-text search + trigram indexes for PAN/name

### 5.2 Filing History Filters
- By Assessment Year (dropdown: 2025-26, 2024-25, ...)
- By ITR Type (ITR-1, ITR-2, ITR-3, ITR-4)
- By Status (Filed, Draft, Processing, Rejected)
- By Date Range (custom date picker)

### 5.3 Tax Records Filters
- By document type (Form 16, AIS, Bank Statement, etc.)
- By assessment year
- By upload date

---

## 6. URL Structure Conventions

- RESTful patterns: `/resource/:id/action`
- Filing sessions use UUIDs: `/file/resume/a1b2c3d4-...`
- No query parameters for navigation state — use path segments
- Query parameters for filters: `/dashboard/filings?ay=2025-26&status=filed`
- Hash fragments for in-page anchors: `/file/new/review#regime-comparison`

---

## 7. Metadata & SEO

### 7.1 Page Titles
- Pattern: `{Page Title} — TaxStox`
- Example: `Review Your Tax Summary — TaxStox`
- Dashboard: `TaxStox — Your Tax Command Center`

### 7.2 Meta Descriptions (Public Pages)
- Landing: "File your ITR in 2 minutes. Upload 2 PDFs, answer 5 questions. AI-powered tax optimization for Indian taxpayers. Licensed ERI."
- Blog posts: Dynamic from content

### 7.3 Structured Data
- Organization schema on landing page
- BreadcrumbList on nested pages
- FAQ schema on how-it-works page

---

## 8. Accessibility Architecture

- ARIA landmarks on all pages (banner, navigation, main, complementary, contentinfo)
- Skip-to-content link as first focusable element
- All interactive elements keyboard-accessible
- Form fields have associated labels (explicit, not implicit)
- Error messages linked to fields via aria-describedby
- Color is never the sole indicator of state (icons + text accompany color)
- Focus indicators visible on all interactive elements
- Minimum contrast ratio 4.5:1 (AA) on all text; 3:1 on large text
- Screen reader announcements for dynamic content updates (aria-live regions)
- Reduced motion support via prefers-reduced-motion media query

---

*Next: [05 Backend Architecture](05-backend-architecture.md)*
