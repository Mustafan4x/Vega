# Future ideas

A scratch list of features that are out of scope for v1 but worth picking up later. The Project Manager reviews this list when planning the next major release.

## Authentication and per user history

**Idea**: each user signs in (Google OAuth, GitHub OAuth, or magic link email) and gets a private history of their calculations. Other users cannot see their inputs, outputs, or P&L.

**Why deferred**: adds backend depth (sessions, JWT, OAuth callbacks), data model changes (`user_id` foreign keys on every persisted row), and threat model expansion (account takeover, IDOR, password reset). Not required to demonstrate the core skills the project is meant to show.

**When to revisit**: after Phase 11 is shipped and stable, or earlier if the project grows beyond a single user demo.

**Notes for the implementer**: prefer a hosted OAuth provider (Auth0, Clerk, Supabase Auth) over rolling your own. The Security Engineer will need to update the threat model. The Data Engineer will need to migrate existing rows or treat them as anonymous.

## Dividends in the pricing model

**Idea**: extend the Black Scholes module to support a continuous dividend yield `q` (and, for completeness, the binomial and Monte Carlo pricers added in Phase 9). The standard generalization replaces `S` with `S * exp(-q * T)` in the d1 and d2 formulas, so the change is local to one module.

**Why deferred**: v1 is scoped to European options on a non dividend paying stock to keep the math doc, the test reference values (Hull, Wilmott, Natenberg), and the Pydantic input model small and exact. Adding `q` doubles the test surface (every reference case needs a `q != 0` variant) and complicates the UI form (a new percent input next to the rate field).

**When to revisit**: after Phase 11 ships and the project is being used. Or sooner if the user adds a real ticker and notices the price disagrees with the market because the underlying actually pays dividends.

**Notes for the implementer**: the convention is documented in `docs/risk/conventions.md` (dividends assumed zero in v1). The Quant Domain Validator owns the formula change and the new reference values. Risk Reviewer must update sanity cases. Backend Developer adds an optional `q: float = 0.0` parameter to the function signature so existing callers keep working. Frontend Developer adds the input field and the percent to decimal conversion. Default to `q = 0` everywhere so the v1 behavior is preserved.

## Required signed commits on `main`

**Idea**: enable `required_signatures` on the GitHub branch protection rule for `main`. Each commit must carry a verified GPG or SSH signature; GitHub displays a "Verified" badge.

**Why deferred**: the user does not currently have a GPG or SSH commit signing key configured locally. Enabling the toggle without first setting up a key would block all future commits. Defense in depth value is moderate for a solo dev pet project (the main attacker scenario, account takeover, would also let the attacker disable the toggle). Still worth doing before Phase 11 deploys publicly.

**When to revisit**: before Phase 11 (production deployment). Or any time the user wants to set up signing.

**Notes for the implementer**: generate an SSH or GPG key, upload the public key to GitHub at https://github.com/settings/keys (Authentication and Signing keys), set `git config user.signingkey`, set `git config commit.gpgsign true` (or `gpg.format ssh` plus `commit.gpgsign true` for SSH signing), then re run the branch protection PUT to set `required_signatures: true`. The setting to flip is `required_signatures` in the existing branch protection JSON; everything else stays unchanged.

## Other deferred ideas

(Add more here as they come up. Each entry should follow the same format: idea, why deferred, when to revisit, notes.)
