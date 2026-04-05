# Architecture Notes

This folder contains two lightweight C4-style architecture diagrams for the current writing and application stack.

Files:
- `blog-writer-c4-level3.puml`
- `blog-writer-c4-level3.png`
- `cuongcv-application-c4-level2.puml`
- `cuongcv-application-c4-level2.png`

Purpose:
- help future agents understand the main moving parts quickly
- show where tone, routing, and validation decisions happen
- make optimization discussions easier without rereading the whole repo and skill library

Quick reading guide:
- `blog-writer-c4-level3` explains how the Blog Writer skill now chooses between 5 modes, including the newer `social mode`, and how authenticity, planning references, bilingual social output, search routing, and output workflows fit together
- `cuongcv-application-c4-level2` explains how `job-search-cuong`, the CuongCV repo, the application system, and validation/shipping tools work together, including the newer shared `web-search-skill` layer for provider-backed external search

Suggested next optimization areas:
- compress duplicated guidance across `AGENTS.md` and `SKILL.md` while keeping fast-path safety
- keep the writing-mode framework stable so multiple skills do not drift
- keep `social mode` lightweight; do not let it turn into a second long-form blog engine
- preserve the shared `web-search-skill` layer so research-heavy skills do not reimplement provider logic
- preserve strong escalation triggers; do not optimize token cost by removing the safety rails
