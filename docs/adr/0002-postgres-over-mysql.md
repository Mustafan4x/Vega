# 0002. Postgres over MySQL

**Status**: accepted, 2026-05-02.

## Context

Phase 6 introduces a persistence layer: every Calculate click writes one row to an inputs table and N rows to an outputs table (one per heat map cell). The SPEC names two tech stack constraints for the database layer: SQLAlchemy 2.x as the ORM, Alembic for migrations, and a free tier managed cloud Postgres plus a zero setup local dev path. SQLite covers local dev cleanly, so the only real choice is which production database engine to target.

The realistic free tier candidates for managed cloud SQL in 2026 are Postgres (Neon, Supabase, Railway) and MySQL (PlanetScale, until it deprecated its free tier; Aiven's limited free tier; some shared hosts). Postgres has more free tier inventory, broader Python ecosystem support (psycopg, asyncpg), and richer column types (JSONB, arrays, range types) which the project may use for storing heat map matrices.

## Decision

Use Postgres as the production database, hosted on Neon's free tier. Use SQLite for local development. Both are spoken to through SQLAlchemy 2.x with Alembic for migrations. Do not adopt MySQL or any MySQL flavored fork.

## Consequences

**Positive**:

* Neon's free tier is generous and includes branching, which makes preview environments cheap when we need them.
* Postgres JSONB lets us store heat map matrices as a single column if the row layout (one cell per row) ever becomes a performance problem.
* Switching between SQLite and Postgres through SQLAlchemy is well understood; the agents can develop locally on SQLite without touching Neon until Phase 11.
* No vendor lock to a Postgres compatible managed offering; Neon, Supabase, Railway, Render's own Postgres, and Fly Postgres all speak standard wire protocol.

**Negative**:

* Some SQLite specific shortcuts (e.g., dynamic typing) will not work on Postgres, so the agents must develop with Postgres as the canonical target and use SQLite only for fast feedback.
* Neon's free tier auto suspends idle databases, so the first request after an idle period takes a few seconds while the compute spins back up. The Backend Developer should handle this with reasonable timeouts.

The tradeoffs are accepted; the cost ceiling for v1 is zero dollars per month, and Neon stays inside that envelope.
