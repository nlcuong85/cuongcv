# Security review: Franklee AI job ranking

Date: 2026-10-26
Risk tier: Tier 4 (privileged automation with external text and Slack delivery)

## Scope and verdict

The added model step is confined to relevance ordering of an already Python-validated shortlist. It does not decide whether jobs pass eligibility, and shadow mode does not change Slack content. The security gate is **approved for shadow-only operation**; the first scheduled sidecar still requires review before any consideration of ranking-mode promotion.

## Boundaries

- Input consists of public job-posting fields only; no CV, application history, or candidate profile.
- Stable IDs are hashes of canonical URLs; actual URLs are not sent to the model or written to the sidecar.
- Job descriptions are explicitly untrusted. Model tools, skills, workspace-context injection, subagents, and channel routing are disabled for the ranker.
- The ranker is pinned to `openai/gpt-6-luna` with `medium` thinking and checks the effective model and live agent policy before processing.
- Output schema validation requires the exact ID set, unchanged section labels, bounded text, and a unique consecutive priority sequence. It cannot add/remove jobs.
- A timeout, provider error, policy mismatch, or invalid schema fails open to deterministic Python ordering; it never blocks the existing report or causes a model-generated Slack message.
- Temporary prompt files are mode `0600` in an owner-only directory and removed after the CLI call. Sidecars are mode `0600` and contain only ranks, short rationales, and hashed IDs.

## Residual risks and release gates

- OpenClaw session storage retains the public prompt/response for operational debugging. Do not add private applicant data to the ranking prompt.
- External job text can still bias a text-only model. The tool-free boundary, strict output schema, and shadow-only rollout limit the consequences; inspect the first week of sidecars before considering rank mode.
- Model relevance judgments may be inconsistent. Evaluate them against deterministic ordering and human review; do not use them to claim ATS compatibility, candidate fit, or job eligibility.
- The Franklee checkout has unrelated dirty/untracked files. Do not commit, clean, or reset it as part of this change.

## Evidence

- Unit tests cover bounded input, URL omission, prompt-injection framing, schema rejection, deterministic fallback, and shortlist preservation.
- A synthetic live canary used GPT-6 Luna at medium thinking and returned a valid two-candidate JSON result; no tools were exposed or invoked.
- No test Slack message was sent.
