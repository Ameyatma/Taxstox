# 06 — Frontend Architecture

> **Parent:** [00-README.md](00-README.md) | **Prev:** [05 Backend Architecture](05-backend-architecture.md) | **Next:** [07 Database Design](07-database-design.md)

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | Next.js 14 (App Router) | SSR for SEO on public pages, CSR for dashboard, API routes for BFF layer |
| Language | TypeScript 5.x (strict mode) | Type safety across the entire codebase |
| UI Library | React 18.x | Ecosystem maturity, concurrent features |
| Styling | Tailwind CSS 3.x + shadcn/ui | Matches existing design system (Tailwind tokens), component primitives |
| State (Server) | TanStack Query (React Query) v5 | Server state caching, deduplication, optimistic updates |
| State (Client) | Zustand | Lightweight client state for UI concerns |
| Form Handling | React Hook Form + Zod | Performance (uncontrolled), schema validation |
| Animation | Framer Motion | Wizard transitions, micro-interactions |
| PDF Viewing | react-pdf | In-browser PDF preview |
| Charts | Recharts | Tax comparison charts, regime visualization |
| Icons | Material Symbols (Google Fonts) | Already used in existing UI prototype |
| Testing | Vitest + React Testing Library + Playwright | Unit, integration, E2E |
| Build | Turbopack (Next.js) | Fast builds, HMR |
| Package Manager | pnpm | Disk efficiency, strict resolution |
| Monorepo | Turborepo | If splitting into multiple packages |
| Linting | ESLint + Prettier | Code quality |
| Git Hooks | Husky + lint-staged | Pre-commit quality gates |

---

## 2. Component Architecture

### 2.1 Component Tree (Authenticated Shell)

```
<App>
├── <AuthProvider>                    // Auth context, token management
│   ├── <QueryClientProvider>         // TanStack Query
│   │   ├── <Router>
│   │   │   ├── <PublicLayout>        // Landing, auth pages
│   │   │   │   ├── <TopAppBar variant="public" />
│   │   │   │   └── <main>{children}</main>
│   │   │   │
│   │   │   └── <AuthenticatedLayout> // All post-login pages
│   │   │       ├── <TopAppBar variant="authenticated" />
│   │   │       │   ├── <Logo />
│   │   │       │   ├── <PrimaryNav />
│   │   │       │   ├── <NotificationBell />
│   │   │       │   └── <UserMenu />
│   │   │       ├── <Sidebar />       // Desktop only
│   │   │       │   ├── <UserProfileCard />
│   │   │       │   ├── <SidebarNav />
│   │   │       │   └── <QuickActions />
│   │   │       ├── <main>{children}</main>
│   │   │       └── <Footer />
│   │   │
│   │   │       // Key page components:
│   │   │       ├── <DashboardPage>
│   │   │       │   ├── <StatsRow />
│   │   │       │   ├── <QuickActionsGrid />
│   │   │       │   ├── <FilingHistoryTable />
│   │   │       │   └── <TaxCalendar />
│   │   │       │
│   │   │       └── <FilingWizard>    // State machine driven
│   │   │           ├── <WizardProgress />
│   │   │           ├── <StepUpload />
│   │   │           │   ├── <DragDropZone />
│   │   │           │   ├── <ProcessingState />
│   │   │           │   └── <SuccessCard />
│   │   │           ├── <StepVerify />
│   │   │           │   ├── <ExtractedDataTable />
│   │   │           │   └── <ConfidenceBadge />
│   │   │           ├── <StepQuestions />
│   │   │           │   ├── <QuestionCard />
│   │   │           │   └── <ExpertTip />
│   │   │           ├── <StepReview />
│   │   │           │   ├── <RegimeComparison />
│   │   │           │   ├── <IncomeSummary />
│   │   │           │   ├── <DeductionDetails />
│   │   │           │   ├── <TaxComputationCard />
│   │   │           │   └── <ExplainMyTax />
│   │   │           └── <StepExport />
│   │   │               ├── <JsonDownload />
│   │   │               └── <PortalInstructions />
```

### 2.2 Shared/Reusable Components

```
components/
├── ui/                          // shadcn/ui primitives
│   ├── button.tsx
│   ├── input.tsx
│   ├── card.tsx
│   ├── badge.tsx
│   ├── progress.tsx
│   ├── dialog.tsx
│   ├── dropdown-menu.tsx
│   ├── table.tsx
│   ├── tabs.tsx
│   ├── tooltip.tsx
│   └── toast.tsx (via Sonner)
│
├── shared/                      // Domain-specific shared
│   ├── AmountDisplay.tsx        // ₹ formatted with data-mono font
│   ├── ConfidenceBadge.tsx      // High/Med/Low with color coding
│   ├── DocumentIcon.tsx         // Type-specific document icon
│   ├── PANInput.tsx             // Masked PAN input with validation
│   ├── RegimeBadge.tsx          // "Old Regime" / "New Regime" chip
│   ├── StatusBadge.tsx          // Filed/Processing/Draft/Rejected
│   ├── SectionBadge.tsx         // "80C" / "80D" etc.
│   ├── TaxSavingBadge.tsx       // Green badge showing savings
│   ├── TrustSeal.tsx            // ITD/security badges
│   └── EmptyState.tsx           // Reusable empty state
│
└── layout/
    ├── TopAppBar.tsx
    ├── Sidebar.tsx
    ├── Footer.tsx
    ├── PublicLayout.tsx
    ├── AuthenticatedLayout.tsx
    └── WizardLayout.tsx
```

---

## 3. Routing Architecture

### 3.1 Route Definitions

```typescript
// app/(public)/layout.tsx      → PublicLayout
// app/(public)/page.tsx         → LandingPage
// app/(public)/auth/signup/page.tsx → SignupPage
// app/(public)/auth/login/page.tsx  → LoginPage

// app/(auth)/layout.tsx         → AuthenticatedLayout (with auth guard)
// app/(auth)/dashboard/page.tsx → DashboardPage
// app/(auth)/file/new/page.tsx  → FilingWizard (entry)
// app/(auth)/tools/regime-compare/page.tsx → RegimeComparePage
// etc.
```

### 3.2 Route Guards

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token');
  const isAuthRoute = request.nextUrl.pathname.startsWith('/(auth)');

  if (isAuthRoute && !token) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  if (!isAuthRoute && token && request.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
}
```

### 3.3 Filing Wizard Routing

The wizard uses a state-machine-driven approach within a single route:

```typescript
// /file/new/page.tsx
type WizardStep = 'upload' | 'verify' | 'questions' | 'review' | 'export' | 'done';

// Step transitions managed by WizardStateMachine (see 08-state-management.md)
// URL query param reflects current step for deep-linking:
// /file/new?step=review

// Resuming an existing session:
// /file/resume/[sessionId]
```

---

## 4. State Architecture (Client-Side)

See [08-state-management.md](08-state-management.md) for complete state design. Frontend-specific summary:

### 4.1 State Categories

| Category | Tool | Example |
|----------|------|---------|
| Server State | TanStack Query | Filing history, extracted entities, tax computation |
| Wizard State | Zustand | Current step, uploaded files, answers, regime choice |
| UI State | Zustand | Sidebar open, active dropdown, theme |
| Form State | React Hook Form | Login form, profile edit, manual data entry |
| Auth State | AuthProvider (Context) | User, token, permissions |

### 4.2 Wizard State Store (Zustand)

```typescript
interface WizardStore {
  // Session
  sessionId: string | null;
  step: WizardStep;
  assessmentYear: string;
  itrType: ITRType | null;

  // Documents
  uploadedFiles: UploadedFile[];
  extractedEntities: ExtractedEntityMap;

  // User Answers
  answers: Record<string, AnswerValue>;
  skippedQuestions: string[];

  // Computation
  selectedRegime: 'old' | 'new' | null;
  taxComputation: TaxComputation | null;
  recommendations: Recommendation[];

  // Actions
  setStep: (step: WizardStep) => void;
  addFile: (file: UploadedFile) => void;
  setAnswer: (questionId: string, value: AnswerValue) => void;
  setRegime: (regime: 'old' | 'new') => void;
  // ...
}
```

---

## 5. API Client Architecture

### 5.1 Backend-for-Frontend (BFF)

Next.js API routes serve as BFF layer. They:
- Aggregate multiple backend service calls
- Handle auth token forwarding
- Strip sensitive data before sending to client
- Transform backend responses to frontend-friendly shapes

### 5.2 API Client Setup

```typescript
// lib/api/client.ts
const apiClient = {
  filing: {
    createSession: (ay: string) => POST('/api/filing/sessions', { ay }),
    getSession: (id: string) => GET(`/api/filing/sessions/${id}`),
    uploadDocument: (sessionId: string, file: File) => {
      // Presigned URL flow:
      // 1. GET /api/filing/sessions/:id/upload-url → { url, fields }
      // 2. POST form data directly to S3
      // 3. POST /api/filing/sessions/:id/documents → { s3Key, type }
    },
    processDocuments: (sessionId: string) =>
      POST(`/api/filing/sessions/${sessionId}/process`),
    getEntities: (sessionId: string) =>
      GET(`/api/filing/sessions/${sessionId}/entities`),
    getQuestions: (sessionId: string) =>
      GET(`/api/filing/sessions/${sessionId}/questions`),
    submitAnswer: (sessionId: string, questionId: string, value: any) =>
      POST(`/api/filing/sessions/${sessionId}/answers`, { questionId, value }),
    getTaxComputation: (sessionId: string) =>
      GET(`/api/filing/sessions/${sessionId}/tax-computation`),
    optimizeRegime: (sessionId: string) =>
      POST(`/api/filing/sessions/${sessionId}/optimize`),
    generateJSON: (sessionId: string) =>
      POST(`/api/filing/sessions/${sessionId}/generate-json`),
    downloadJSON: (sessionId: string) =>
      GET(`/api/filing/sessions/${sessionId}/json/download`, { responseType: 'blob' }),
  },
  dashboard: {
    getStats: () => GET('/api/dashboard/stats'),
    getFilingHistory: (filters: FilingFilters) =>
      GET('/api/dashboard/filings', filters),
  },
  tools: {
    compareRegimes: (params: RegimeCompareParams) =>
      POST('/api/tools/regime-compare', params),
    calculateHRA: (params: HRAParams) =>
      POST('/api/tools/hra-calculate', params),
    calculateCapitalGains: (params: CGParams) =>
      POST('/api/tools/capital-gains', params),
  },
};
```

### 5.3 Optimistic Updates

For the wizard flow:
- File upload progress: useMutation with onProgress callback
- Answer submission: optimistic update to wizard state, rollback on error
- Regime switch: optimistic recompute, show spinner while backend confirms

---

## 6. Performance Architecture

### 6.1 Code Splitting

```typescript
// Heavy components loaded dynamically
const RegimeComparison = dynamic(() => import('@/components/wizard/RegimeComparison'), {
  loading: () => <RegimeComparisonSkeleton />,
  ssr: false, // Contains charts, no SEO benefit from SSR
});

const PdfPreview = dynamic(() => import('@/components/shared/PdfPreview'), {
  ssr: false,
});
```

### 6.2 Image Optimization

- All images use Next.js `<Image>` component
- Third-party trust badges: preload critical, lazy-load below fold
- Generated images (charts): render client-side, no server burden

### 6.3 Font Loading

```html
<!-- Preconnect to Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<!-- Critical font: Hanken Grotesk (headlines) -->
<!-- Fallback: system-ui → instantly visible text -->
```

### 6.4 Bundle Budget

| Metric | Budget |
|--------|--------|
| Initial JS (public pages) | < 100 KB (gzipped) |
| Initial JS (dashboard) | < 200 KB (gzipped) |
| Total JS (all routes) | < 500 KB (gzipped) |
| CSS | < 50 KB (gzipped, Tailwind purged) |
| LCP | < 2.5s on 3G |
| TBT | < 200ms |

---

## 7. Error Handling (Frontend)

### 7.1 Error Boundary Hierarchy

```typescript
<ErrorBoundary fallback={<PageErrorFallback />}>        // Top-level
  <ErrorBoundary fallback={<SectionErrorFallback />}>    // Per-section
    <WizardStep />
  </ErrorBoundary>
</ErrorBoundary>
```

### 7.2 API Error Handling

```typescript
// TanStack Query global error handler
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error.status === 401) return false;    // Don't retry auth errors
        if (error.status === 404) return false;    // Don't retry not found
        return failureCount < 3;                    // Retry others up to 3 times
      },
    },
    mutations: {
      onError: (error) => {
        toast.error(getUserFacingMessage(error));
      },
    },
  },
});
```

### 7.3 Error → User Message Mapping

| Error Code | User-Facing Message |
|------------|---------------------|
| UPLOAD_TOO_LARGE | "This file is {{size}}MB. Max size is 10MB. Try compressing it." |
| UPLOAD_WRONG_FORMAT | "We only support PDF files. You uploaded a {{format}}." |
| PDF_CORRUPTED | "We couldn't read this file. It may be damaged. Try a fresh copy." |
| PDF_PASSWORD | "This PDF is password-protected. Enter the password to continue." |
| EXTRACTION_FAILED | "We had trouble reading some parts. Let's continue and I'll ask you about those." |
| VALIDATION_MISMATCH | "The {{field}} in your {{doc1}} doesn't match {{doc2}}. Which is correct?" |
| TAX_ENGINE_ERROR | "Tax computation hit a snag. Our team has been notified. Please try again." |
| JSON_GENERATION_FAILED | "Couldn't generate your ITR JSON. Please try again or contact support." |
| NETWORK_ERROR | "Connection lost. Your progress is saved. Check your internet and try again." |
| SESSION_EXPIRED | "Your session expired for security. Please sign in again." |
| RATE_LIMITED | "You're going too fast! Please wait a moment before trying again." |

---

## 8. Progressive Web App (PWA)

- Service Worker: Cache static assets, offline fallback page
- Manifest: Install prompt with TaxStox branding
- Offline: Wizard state persisted to IndexedDB, sync when online
- Push Notifications: Filing deadline reminders, refund status updates

---

## 9. Internationalization (i18n)

- Framework: next-intl
- V1 Languages: English, Hindi (हिन्दी)
- V2 Languages: Gujarati, Marathi, Tamil, Telugu, Kannada, Bengali
- All user-facing strings in translation files
- Number formatting uses Intl.NumberFormat with `en-IN` locale
- Currency always displayed as ₹ (Indian Rupee)

---

## 10. Build & Deploy Pipeline (Frontend)

```
Git Push → GitHub Actions
  ├── Lint (ESLint + Prettier)
  ├── Type Check (tsc --noEmit)
  ├── Unit Tests (Vitest)
  ├── Integration Tests (React Testing Library)
  ├── Build (next build)
  ├── Bundle Analysis (@next/bundle-analyzer)
  ├── E2E Tests (Playwright against preview deploy)
  └── Deploy (Vercel / AWS Amplify)
```

---

*Next: [07 Database Design](07-database-design.md)*
