# 0003. Cloudflare Pages over Vercel for the frontend

**Status**: accepted, 2026-05-02.

## Context

The frontend is a static React build produced by Vite. The two obvious managed hosts for a static React build are Cloudflare Pages and Vercel; both have generous free tiers, both wire up to GitHub for auto deploy on push, and both can attach a custom domain with HTTPS at no cost.

The setup guide at [`../setup-guide.md`](../setup-guide.md) lists the practical differences observed at the time of this decision: Cloudflare Pages pairs cleanly with Cloudflare's WAF and DDoS protection, ships a generous free tier, and allows future migration of edge logic to Cloudflare Workers without leaving the platform. Vercel is a fine alternative whose deploy steps are nearly identical; the setup guide explicitly notes that recent reports of Vercel related incidents have not been independently verified by this project, and that for a public pet project that does not store user secrets the practical risk of using either platform is low.

The user (Mustafa) prefers Cloudflare Pages as the v1 default. The decision was made on platform fit (WAF in front of the static frontend, free tier, possible future Workers use), not on incident response.

## Decision

Deploy the frontend to Cloudflare Pages. Treat Vercel as a documented alternative in the setup guide for any future operator who wants to swap. Do not deploy the frontend to both simultaneously.

## Consequences

**Positive**:

* Cloudflare's WAF sits in front of the frontend by default. The Security Engineer's hardening checklist for Phase 11 leans on this.
* Free tier covers the project's traffic profile with margin to spare.
* If the project later adopts edge logic (e.g., a small auth proxy, a request rewriter), Cloudflare Workers is one click away.

**Negative**:

* The DevOps Engineer's Phase 11 runbook is Cloudflare specific. Switching to Vercel later is straightforward but not free of work.
* Cloudflare Pages preview deploys behave slightly differently from Vercel previews; the agents should not assume Vercel ergonomics carry over.

The backend hosting choice (Render over Vercel) is a separate, harder decision: Vercel is unsuitable for long lived Python servers and is excluded for the backend regardless. That part is not a tradeoff, just a constraint, and is documented in [`../setup-guide.md`](../setup-guide.md) rather than as its own ADR.
