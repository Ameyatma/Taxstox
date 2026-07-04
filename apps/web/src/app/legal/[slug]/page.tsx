import { notFound } from "next/navigation";
import Link from "next/link";

const legalContent: Record<string, { title: string; lastUpdated: string; sections: { heading: string; body: string | string[] }[] }> = {
  "terms": {
    title: "Terms of Service",
    lastUpdated: "2026-07-04",
    sections: [
      {
        heading: "1. Acceptance of Terms",
        body: "By accessing or using TaxStox (\"the Platform\"), you agree to be bound by these Terms of Service. If you do not agree, please do not use the Platform. TaxStox is owned and operated by TaxStox Technologies Private Limited (\"Company\", \"we\", \"us\", \"our\").",
      },
      {
        heading: "2. Description of Service",
        body: "TaxStox provides an automated income tax return (ITR) preparation service. The Platform extracts data from uploaded documents (Form 16, AIS, broker statements), classifies income sources, optimizes tax across Old and New regimes, validates the return against 400+ checks, and generates an ITR JSON file ready for upload to the Income Tax Department's e-filing portal.",
      },
      {
        heading: "3. User Eligibility",
        body: [
          "You must be at least 18 years of age to use this Platform.",
          "You must be a resident Indian taxpayer with a valid PAN card.",
          "You are responsible for maintaining the confidentiality of your account credentials.",
          "You agree to provide accurate and truthful information, including PAN, date of birth, and income details.",
        ],
      },
      {
        heading: "4. No Legal or Tax Advice",
        body: "TaxStox is a technology platform that automates ITR preparation. It does NOT provide legal advice, tax advice, or Chartered Accountancy services. The tax calculations are algorithmic and based on the Income Tax Act, 1961 as amended. You should consult a qualified Chartered Accountant for personalized tax advice. The Company is not liable for any discrepancies, penalties, or notices arising from the use of generated ITR files.",
      },
      {
        heading: "5. User Obligations",
        body: [
          "Upload only genuine, unaltered PDF documents issued by authorized entities (employers, banks, brokers, Income Tax Department).",
          "Verify all auto-extracted data before filing. The Platform provides data as-is from uploaded documents.",
          "Do not use the Platform for any fraudulent, unlawful, or prohibited purpose.",
          "Do not attempt to reverse-engineer, decompile, or extract the source code of the Platform.",
        ],
      },
      {
        heading: "6. Intellectual Property",
        body: "All content, trademarks, logos, software, algorithms, and design elements on TaxStox are the exclusive property of TaxStox Technologies Private Limited. You may not copy, reproduce, distribute, or create derivative works without express written permission.",
      },
      {
        heading: "7. Limitation of Liability",
        body: [
          "TaxStox is provided on an \"as-is\" and \"as-available\" basis without warranties of any kind, express or implied.",
          "The Company shall not be liable for any direct, indirect, incidental, special, consequential, or exemplary damages, including but not limited to tax penalties, interest, notices, or litigation costs arising from the use of the Platform.",
          "The Company's total liability for any claim shall not exceed the fees paid by you for the specific filing in question.",
          "The Company is not responsible for errors in source documents (Form 16, AIS, broker statements) provided by you or third parties.",
        ],
      },
      {
        heading: "8. Data & Privacy",
        body: "Your use of the Platform is also governed by our Privacy Policy. By using TaxStox, you consent to the collection and processing of your data as described in the Privacy Policy. Uploaded documents are processed in-memory and auto-deleted within 48 hours. No financial data is permanently stored unless explicitly saved to your account.",
      },
      {
        heading: "9. Fees & Refunds",
        body: [
          "Document upload, data extraction, and regime comparison are free. A fee is charged only when you download the finalized ITR JSON.",
          "Fees are displayed before payment and are non-refundable once the ITR JSON has been generated and downloaded.",
          "If the Platform fails to generate a valid ITR JSON due to a technical error on our side, a full refund will be issued within 7 business days.",
          "All payments are processed through RBI-compliant payment gateways with 256-bit SSL encryption.",
        ],
      },
      {
        heading: "10. Termination",
        body: "We reserve the right to suspend or terminate your account at any time, without notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties, or for any other reason in our sole discretion.",
      },
      {
        heading: "11. Governing Law",
        body: "These Terms shall be governed by and construed in accordance with the laws of India. Any disputes arising out of or relating to these Terms shall be subject to the exclusive jurisdiction of the courts in Bangalore, Karnataka.",
      },
      {
        heading: "12. Changes to Terms",
        body: "We reserve the right to modify these Terms at any time. Changes will be effective immediately upon posting. Your continued use of the Platform after changes are posted constitutes acceptance of the modified Terms.",
      },
      {
        heading: "13. Contact",
        body: "For questions about these Terms, contact us at legal@taxstox.com.",
      },
    ],
  },

  "privacy": {
    title: "Privacy Policy",
    lastUpdated: "2026-07-04",
    sections: [
      {
        heading: "1. Introduction",
        body: "TaxStox Technologies Private Limited (\"we\", \"our\", \"us\") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use TaxStox (\"the Platform\"). This policy is compliant with the Information Technology Act, 2000 and the Digital Personal Data Protection Act, 2023.",
      },
      {
        heading: "2. Information We Collect",
        body: [
          "Personal Information: PAN card number, full name, email address, date of birth, and phone number (if provided).",
          "Financial Information: Salary details, TDS amounts, capital gains, dividend income, interest income, HRA, deductions under Chapter VI-A, and other tax-related data extracted from your uploaded documents.",
          "Document Data: Form 16, Annual Information Statement (AIS), broker tradebooks, and investment proofs uploaded by you.",
          "Account Information: Hashed password (bcrypt), Google OAuth identifier (if using Google Sign-In), account creation date.",
          "Usage Data: IP address, browser type, pages visited, time spent on pages, and feature usage patterns.",
        ],
      },
      {
        heading: "3. How We Use Your Information",
        body: [
          "To extract, classify, and process tax-related data from your uploaded documents.",
          "To compute your tax liability under Old and New regimes and generate optimized ITR JSON files.",
          "To validate your return against 400+ algorithmic checks.",
          "To authenticate your identity and maintain your account.",
          "To communicate with you about your filings, platform updates, and support requests.",
          "To improve the Platform's accuracy, performance, and user experience through anonymized analytics.",
        ],
      },
      {
        heading: "4. Data Storage & Deletion",
        body: [
          "Uploaded PDFs and extracted financial data are processed in-memory and auto-deleted within 48 hours of processing.",
          "Your account information (name, email, PAN) is stored in an encrypted PostgreSQL database hosted on Neon (AWS us-east-1).",
          "ITR filing records (status, assessment year, ITR type) are retained for your reference until you delete your account.",
          "You may request deletion of your account and all associated data by emailing privacy@taxstox.com. Data will be purged within 30 days.",
        ],
      },
      {
        heading: "5. Data Security",
        body: [
          "All data in transit is encrypted using TLS 1.3 (256-bit SSL).",
          "Passwords are hashed using bcrypt with unique salts. We never store plain-text passwords.",
          "Database access is restricted to application servers via IP whitelisting and encrypted connections.",
          "We conduct regular security audits and vulnerability assessments.",
          "In the unlikely event of a data breach, affected users will be notified within 72 hours as required by Indian law.",
        ],
      },
      {
        heading: "6. Data Sharing & Third Parties",
        body: [
          "We do NOT sell, rent, or trade your personal information to third parties.",
          "We do NOT share your financial data with any third party except as required by law.",
          "Service Providers: We use Neon (database hosting), Render (backend hosting), and Vercel (frontend hosting). These providers process data on our behalf and are bound by data processing agreements.",
          "Legal Compliance: We may disclose information if required by law, court order, or government regulation.",
        ],
      },
      {
        heading: "7. Cookies & Tracking",
        body: "TaxStox uses essential cookies for authentication (JWT tokens stored in localStorage) and session management. We do not use third-party tracking cookies, advertising cookies, or analytics cookies that identify individual users. We do not engage in behavioral advertising or user profiling for marketing purposes.",
      },
      {
        heading: "8. Google OAuth",
        body: "If you sign in using Google, we receive your name and email address from Google. We do not access your Google Drive, Gmail, contacts, or any other Google service data. The Google ID token is processed server-side and your Google credentials are never stored by TaxStox.",
      },
      {
        heading: "9. Your Rights",
        body: [
          "Right to Access: You may request a copy of all personal data we hold about you.",
          "Right to Correction: You may update your name and PAN through the Settings page.",
          "Right to Erasure: You may request deletion of your account and all associated data.",
          "Right to Data Portability: You may download your filing history as structured data.",
          "Right to Withdraw Consent: You may withdraw consent at any time by deleting your account.",
        ],
      },
      {
        heading: "10. Children's Privacy",
        body: "The Platform is not intended for individuals under 18 years of age. We do not knowingly collect personal information from children. If you believe a child has provided us with personal data, please contact us immediately.",
      },
      {
        heading: "11. Changes to This Policy",
        body: "We may update this Privacy Policy from time to time. Material changes will be communicated via email. Continued use of the Platform after changes constitutes acceptance of the updated policy.",
      },
      {
        heading: "12. Grievance Officer",
        body: "As required by the Information Technology Act, 2000, our Grievance Officer is: Mr. Aman Verma, TaxStox Technologies Pvt Ltd, Bangalore, India. Email: grievance@taxstox.com. Response time: within 15 days.",
      },
      {
        heading: "13. Contact",
        body: "For privacy-related inquiries: privacy@taxstox.com.",
      },
    ],
  },

  "security": {
    title: "Security",
    lastUpdated: "2026-07-04",
    sections: [
      {
        heading: "Our Security Commitment",
        body: "TaxStox handles some of the most sensitive personal and financial data in India — PAN numbers, salary details, capital gains, and tax returns. We have built security into every layer of the platform from day one.",
      },
      {
        heading: "Encryption",
        body: [
          "TLS 1.3 (256-bit SSL) for all data in transit between your browser and our servers.",
          "Passwords hashed using bcrypt with unique per-password salts (never stored in plain text).",
          "JWT tokens signed with HS256 + auto-generated 32-character secrets (rotated on each Render deploy).",
          "Database connections use SSL/TLS with certificate validation (sslmode=require).",
        ],
      },
      {
        heading: "Infrastructure Security",
        body: [
          "Frontend hosted on Vercel with automatic DDoS protection and global CDN.",
          "Backend hosted on Render with isolated Docker containers.",
          "Database hosted on Neon (AWS us-east-1) with IP-whitelisted access.",
          "All services use separate, auto-generated credentials — no shared passwords.",
        ],
      },
      {
        heading: "Data Handling",
        body: [
          "Uploaded PDFs (Form 16, AIS, broker statements) are processed entirely in-memory (RAM).",
          "Extracted financial data is purged within 48 hours of ITR generation.",
          "We do NOT permanently store your Form 16, AIS, or broker statements on disk.",
          "No financial data is logged — application logs contain only request metadata.",
        ],
      },
      {
        heading: "Authentication",
        body: [
          "Email/password login with bcrypt-hashed credentials (72-byte maximum password length enforced).",
          "Google OAuth 2.0 sign-in using Google-verified ID tokens (server-side validation of audience, expiry, and signature).",
          "JWT access tokens with configurable expiry for API authentication.",
          "All authenticated endpoints verify JWT signature and expiry on every request.",
        ],
      },
      {
        heading: "Compliance",
        body: [
          "Compliant with the Information Technology Act, 2000 (India).",
          "Compliant with the Digital Personal Data Protection Act, 2023.",
          "Data processed and stored exclusively within India (AWS us-east-1 is the closest available region; migration to AWS ap-south-1 pending).",
        ],
      },
      {
        heading: "Report a Vulnerability",
        body: "We take security seriously. If you discover a vulnerability, please email security@taxstox.com. We follow responsible disclosure practices and will respond within 48 hours. Please do not publicly disclose the issue until we have addressed it.",
      },
    ],
  },

  "support": {
    title: "Support",
    lastUpdated: "2026-07-04",
    sections: [
      {
        heading: "How Can We Help?",
        body: "TaxStox is built to be self-serve — upload your documents, answer a few questions, and download your ITR. But if you need help, we're here.",
      },
      {
        heading: "Frequently Asked Questions",
        body: [
          "Q: Is TaxStox free? A: Upload, extraction, and regime comparison are free. You pay only when you download the final ITR JSON.",
          "Q: Which ITR forms are supported? A: Currently ITR-1 (Sahaj) and ITR-2. ITR-3 and ITR-4 are coming soon.",
          "Q: Is my data safe? A: Yes. See our Security page for details. Uploaded documents are processed in-memory and purged within 48 hours.",
          "Q: How accurate are the calculations? A: Our tax engine implements the Income Tax Act FY 2025-26 slabs and validates against 400+ checks. However, TaxStox is not a substitute for a Chartered Accountant.",
          "Q: Can I file directly through TaxStox? A: Currently, you download the ITR JSON and upload it to the Income Tax e-filing portal yourself. Direct e-filing integration is on the roadmap.",
          "Q: What if I made a mistake? A: You can revise your return. Upload corrected documents and regenerate. The Income Tax Department also allows filing a revised return under Section 139(5).",
        ],
      },
      {
        heading: "Contact Us",
        body: [
          "Email: support@taxstox.com",
          "Response time: Within 24 hours on business days.",
          "For security issues: security@taxstox.com",
          "For privacy inquiries: privacy@taxstox.com",
          "For legal matters: legal@taxstox.com",
        ],
      },
      {
        heading: "Business Hours",
        body: [
          "Monday — Friday: 9:00 AM to 7:00 PM IST",
          "Saturday: 10:00 AM to 4:00 PM IST",
          "Sunday: Closed",
          "During ITR filing season (June — July): Extended hours — 8:00 AM to 10:00 PM IST, 7 days a week.",
        ],
      },
    ],
  },
};

export default async function LegalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const content = legalContent[slug];

  if (!content) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <div className="max-w-3xl mx-auto px-6 py-16">
        {/* Breadcrumb */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-sm text-[#003178] hover:text-[#003366] transition-colors"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            ← Back to Home
          </Link>
        </div>

        {/* Header */}
        <div className="mb-10 pb-8 border-b border-[#E2E8F0]">
          <h1
            className="text-3xl md:text-4xl font-bold text-[#003366] mb-3"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            {content.title}
          </h1>
          <p className="text-sm text-[#737783]">
            Last updated: {new Date(content.lastUpdated).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
          </p>
        </div>

        {/* Sections */}
        <div className="space-y-8">
          {content.sections.map((section, i) => (
            <div key={i}>
              <h2
                className="text-lg font-semibold text-[#003366] mb-2"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                {section.heading}
              </h2>
              {Array.isArray(section.body) ? (
                <ul className="list-disc pl-5 space-y-1.5">
                  {section.body.map((item, j) => (
                    <li key={j} className="text-sm text-[#434652] leading-relaxed">{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[#434652] leading-relaxed">{section.body}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export async function generateStaticParams() {
  return Object.keys(legalContent).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const content = legalContent[slug];
  if (!content) return {};
  return {
    title: `${content.title} — TaxStox`,
    description: `${content.title} for TaxStox — the 2-minute ITR filing platform.`,
  };
}
