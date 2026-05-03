# 0001. React plus FastAPI over Streamlit

**Status**: accepted, 2026-05-02.

## Context

The source video that inspired this build demonstrates a Streamlit prototype: one Python file, no separate frontend, deployed to Streamlit Cloud. Streamlit is the path of least resistance for a quant who already writes Python and wants a chart on the screen quickly.

The project's primary goal, however, is to serve as a quant interview pet project that can be linked from a resume. A reviewer opening the deployed app should see a real frontend (not a Streamlit auto generated layout) and a real backend (not a single script), because that is what production trading tooling actually looks like.

The user (Mustafa) has explicitly chosen to demonstrate frontend skill alongside the quant math. Tailwind plus Vite plus React plus TypeScript is the documented stack, with the Oxblood theme as the visual ground truth.

## Decision

Build the frontend as React 18 plus Vite plus TypeScript plus Tailwind, hosted on Cloudflare Pages. Build the backend as FastAPI on Python 3.12, hosted on Render. Connect them over JSON HTTPS. Do not use Streamlit at any layer.

## Consequences

**Positive**:

* The deployed app looks and feels like a real product, not a notebook.
* Frontend and backend can evolve independently; the React app could later target a different backend, and the FastAPI service could later serve a different client (CLI, mobile).
* FastAPI's Pydantic validation and OpenAPI schema give us contract tests and a generated API reference for free.
* The user gains React, Tailwind, FastAPI, and SQLAlchemy experience as part of the build.

**Negative**:

* Two deploy targets instead of one (Cloudflare Pages plus Render), so Phase 11 is heavier than a Streamlit deploy would be.
* CORS, auth (when added), and CSP have to be configured explicitly. Streamlit hides these.
* The first visible UI screen lands in Phase 3 instead of Phase 1, because the FastAPI wrapper has to exist first.

The tradeoffs are accepted. The build plan reserves entire phases (Phase 3, Phase 4, Phase 11) to absorb the extra surface area.
