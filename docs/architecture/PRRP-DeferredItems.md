# PRRP Deferred Production Items

> **Program:** Production Readiness Remediation Program
> **Created:** 2026-08-01 (PR1)
> **Purpose:** Register production readiness gaps that cannot be resolved in the current remediation wave due to infrastructure or dependency constraints.

---

## PRRP-DEFER-001: JWT in localStorage — Migration to httpOnly Cookies

| Dimension | Detail |
|-----------|--------|
| **Wave recorded** | PR1 (Security Hardening) |
| **Target resolution wave** | Post-PR6 (pre-Public-Beta) |
| **Severity** | High |
| **PRR finding** | Security audit cross-cutting: JWT access tokens stored in browser `localStorage` (`apps/web/src/lib/auth.tsx:20`). XSS-exfiltratable. No refresh token rotation. No token revocation. |
| **Risk** | Any successful XSS attack exfiltrates the JWT → full account access for 24-hour token lifetime. |
| **Mitigation in place (PR1)** | CSP `script-src 'self'` prevents inline script injection. `X-Content-Type-Options: nosniff` blocks MIME confusion. `X-Frame-Options: DENY` blocks clickjacking. `Cross-Origin-Opener-Policy: same-origin` isolates browsing context. |
| **Resolution plan** | 1. Implement httpOnly, `SameSite=Strict` cookie for JWT delivery from `/auth/login` and `/auth/google`. 2. Add CSRF token middleware (double-submit cookie pattern). 3. Backend: extract JWT from cookie instead of `Authorization` header. 4. Frontend: remove all `localStorage.setItem("taxstox_token", ...)` calls. Switch `fetch` to `credentials: 'include'`. 5. Google OAuth popup flow incompatible with httpOnly cookies — requires server-side redirect OAuth flow. 6. Implement refresh token rotation with `/auth/refresh` endpoint. |
| **Why deferred** | Requires coordinated changes across auth, frontend, and deployment. Google OAuth flow must be redesigned from popup to server-side redirect. Cookie-based auth requires shared parent domain (frontend + API on same domain or subdomain). Multi-wave change. |
| **Acceptance criteria** | JWT no longer stored in `localStorage` or accessible to JavaScript. Refresh tokens rotated on use. `/auth/refresh` endpoint functional. Google OAuth uses server-side redirect flow. |

---

## PRRP-DEFER-002: Per-Worker Rate Limiter — Global Redis Rate Limiting

| Dimension | Detail |
|-----------|--------|
| **Wave recorded** | PR1 (Security Hardening) |
| **Target resolution wave** | PR5 (Operational Readiness) |
| **Severity** | Medium |
| **PRR finding** | Architecture review: `InMemoryRateLimitStore` is per-worker. With 4 Gunicorn workers, the effective rate limit is 4× the configured threshold. |
| **Risk** | During beta with 2 workers, effective rate limits are 2× configured. Not a security risk at beta scale (≤50 users) but must be corrected before public beta. |
| **Mitigation in place (PR1)** | `RateLimitStore` Protocol defined in domain layer. `InMemoryRateLimitStore` implements it. Redis swap requires only implementing the Protocol — zero upstream code changes. |
| **Resolution plan** | Implement `RedisRateLimitStore` in PR5 when Redis infrastructure is available. Use `INCR` + `EXPIRE` for atomic check-and-increment. Swap singleton in `rate_limit_dependency.py`. |
| **Acceptance criteria** | Rate limits enforced globally across all workers. Redis `INCR` operation is atomic. TTL-based expiry via `EXPIRE`. |
