---
name: TaxStox Design System
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434652'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737783'
  outline-variant: '#c3c6d4'
  surface-tint: '#2b5bb5'
  primary: '#003178'
  on-primary: '#ffffff'
  primary-container: '#0d47a1'
  on-primary-container: '#a1bbff'
  inverse-primary: '#b0c6ff'
  secondary: '#9c4400'
  on-secondary: '#ffffff'
  secondary-container: '#fd7613'
  on-secondary-container: '#5b2500'
  tertiary: '#003f0b'
  on-tertiary: '#ffffff'
  tertiary-container: '#005914'
  on-tertiary-container: '#7ecf79'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d9e2ff'
  primary-fixed-dim: '#b0c6ff'
  on-primary-fixed: '#001945'
  on-primary-fixed-variant: '#00429c'
  secondary-fixed: '#ffdbca'
  secondary-fixed-dim: '#ffb68f'
  on-secondary-fixed: '#331200'
  on-secondary-fixed-variant: '#773200'
  tertiary-fixed: '#a3f69c'
  tertiary-fixed-dim: '#88d982'
  on-tertiary-fixed: '#002204'
  on-tertiary-fixed-variant: '#005312'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
  itd-blue-deep: '#003366'
  itd-orange-vibrant: '#F57C00'
  success-green: '#166534'
  error-red: '#991B1B'
  warning-amber: '#92400E'
  surface-muted: '#F8FAFC'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  subheading:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-base:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  gutter: 24px
  margin-page: 40px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
  container-max: 1120px
---

## Brand & Style

The design system for this platform is anchored in the brand pillars of **Automated Precision, Expert Authority, and Unshakeable Security**. It is designed for Indian taxpayers who are overwhelmed by complexity and seek a "single source of truth" that respects their time and intelligence. 

The aesthetic follows a **Corporate / Modern** style with a focus on **High-Clarity Data Visualization**. It takes the institutional reliability of government portals and filters it through a clean, high-performance SaaS lens.

- **Minimalist Foundations:** Heavy use of white space to reduce cognitive load during complex financial tasks.
- **Expert Utility:** Borrowing from the `shadcn/ui` philosophy, the UI uses crisp borders and systematic spacing to create a sense of structural integrity.
- **Trust-Focused:** Subtle use of depth and refined typography to move away from the "cluttered" feel of legacy tax portals toward a streamlined, automated experience.

## Colors

The color palette is a modernization of the official India Income Tax Department (ITD) identity. 

- **Primary (Deep Blue):** Represents institutional trust, stability, and legal compliance. Used for primary navigation, headers, and the main "File Now" actions.
- **Secondary (Energetic Orange):** Used as a functional accent for "Attention Required" states, wizard progress indicators, and highlight-worthy savings.
- **Tertiary (Tax-Success Green):** Specifically reserved for "Exempt" components, "Optimized" regime indicators, and successful filing confirmations.
- **Neutral (Slate/Gray):** Used for typography and structural borders to maintain a professional, news-like clarity.

**Color Mode:** This system is strictly `light` mode by default to ensure maximum readability for document parsing and data verification, though surfaces are layered with a soft gray (`#F8FAFC`) to reduce eye strain.

## Typography

Typography is used as a tool for hierarchy in information-dense environments.

- **Headlines (Hanken Grotesk):** A sharp, contemporary grotesque that feels "designed" and authoritative. It is used for section headers and the "Tax Summary" totals.
- **Body (Inter):** Chosen for its exceptional legibility in SaaS interfaces. Used for all instructions and wizard questions.
- **Data (JetBrains Mono):** Crucial for "Technical Accuracy." Used for PANs, ISIN codes, Tan numbers, and the "ITR JSON Path" identifiers to distinguish raw data from UI text.

**Scaling:** On mobile, display sizes are reduced significantly to ensure currency values (often 7-8 digits) do not wrap awkwardly.

## Layout & Spacing

The system uses a **Fixed Grid** approach for the desktop dashboard to keep complex data tables and wizard cards centered and readable.

- **The 12-Column Grid:** Standard desktop layout uses a 12-column grid with 24px gutters.
- **Wizard Layout:** Step-by-step questions are housed in a narrow 6-column central container (approx 640px) to keep the user focused and prevent "eye-scanning" fatigue.
- **The One-Pager Summary:** Uses a specialized 2-column "Impact" layout—Income/Deductions on the left, Tax Computation on the right.
- **Mobile Adaptivity:** Transitions to a single-column fluid layout with 16px side margins. Tabular data (like Stock Sales) switches to "Card-based List" views.

## Elevation & Depth

To maintain a "Professional/Expert" feel, the system avoids heavy drop shadows, opting instead for **Tonal Layers** and **Low-Contrast Outlines**.

- **Level 0 (Base):** `#F8FAFC` (Surface-Muted). Used for the global background.
- **Level 1 (Cards):** `#FFFFFF` with a 1px border of `#E2E8F0`. This is the primary container for questions and data blocks.
- **Level 2 (Active State/Modals):** Subtle ambient shadow (Y: 4px, Blur: 12px, 5% Opacity Black) to lift critical alerts or the "Regime Optimizer" recommendation above the grid.
- **Separators:** Use 1px solid dividers for logical breaks within a form; use 1px dashed dividers for "Drag & Drop" zones (PDF Uploads).

## Shapes

The shape language is **Soft (Level 1)**. This creates a professional, "Fintech" precision without feeling overly playful or "bubbly."

- **Standard Elements:** 0.25rem (4px) radius for input fields, checkboxes, and small utility buttons.
- **Container Elements:** 0.5rem (8px) for cards and main "Wizard" containers.
- **Interactive Prompts:** Large action buttons (like "Download ITR JSON") use 0.5rem to feel substantial and clickable.

## Components

### Buttons
- **Primary:** Solid `itd-blue-deep`, white text, 4px radius. High emphasis.
- **Secondary (The Optimizer):** Solid `itd-orange-vibrant`, white text. Reserved for "Switch to New Regime" or "Optimize Tax."
- **Ghost:** Transparent with blue border. Used for "Add more details" or "Back."

### The "Step-by-Step" Wizard
- **Question Cards:** White background, thin border. Headline is `subheading` typography. Answers are large, selectable tiles (Yes/No).
- **Progress Track:** A thin bar at the top using `secondary` color for the active segment.

### Data Visualization & Tables
- **Tax Summary Card:** A high-contrast card with a `success-green` left-accent if a refund is due, or `warning-amber` if balance is payable. Use `data-mono` for all currency values to ensure digit alignment.
- **Comparison Bars:** Side-by-side horizontal bars comparing "Old Regime" vs "New Regime" tax liability.

### Input Fields
- Standard `shadcn/ui` style: thin slate border, turns `primary-blue` on focus.
- **Currency Inputs:** Prefixed with ₹ symbol in a muted slate color.

### Chips/Badges
- **Status Badges:** Used for "Parsed," "Mismatch," or "Exempt." Uses a light tinted background with dark text (e.g., Green tint for Exempt).