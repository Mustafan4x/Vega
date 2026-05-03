# Future ideas

A scratch list of features that are out of scope for v1 but worth picking up later. The Project Manager reviews this list when planning the next major release.

## Authentication and per user history

**Idea**: each user signs in (Google OAuth, GitHub OAuth, or magic link email) and gets a private history of their calculations. Other users cannot see their inputs, outputs, or P&L.

**Why deferred**: adds backend depth (sessions, JWT, OAuth callbacks), data model changes (`user_id` foreign keys on every persisted row), and threat model expansion (account takeover, IDOR, password reset). Not required to demonstrate the core skills the project is meant to show.

**When to revisit**: after Phase 11 is shipped and stable, or earlier if the project grows beyond a single user demo.

**Notes for the implementer**: prefer a hosted OAuth provider (Auth0, Clerk, Supabase Auth) over rolling your own. The Security Engineer will need to update the threat model. The Data Engineer will need to migrate existing rows or treat them as anonymous.

## Other deferred ideas

(Add more here as they come up. Each entry should follow the same format: idea, why deferred, when to revisit, notes.)
