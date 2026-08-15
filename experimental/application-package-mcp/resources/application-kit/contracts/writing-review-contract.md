# General Writing Review Contract

Use this contract when the student asks to check or improve selected writing outside the standard CV, cover-letter, or interview-prep flows.

Also read `mcp-review-payload-contract.md`. The selected text sent to the MCP must be final reader-facing text, not notes, prompts, outline scaffolding, placeholders, or internal revision instructions.

Supported writing modes:

- `application`
- `academic`
- `blog`
- `work`
- `social`
- `general`

The student may provide a paragraph, Markdown/TXT draft, HTML export, DOCX, or text-extractable PDF. Extraction and chunking must happen locally. The MCP receives only selected text chunks.

## Loop Count

Ask the student how many review loops they want. The allowed choices are exactly 1, 2, or 3 review loops:

- 1 loop: quick check
- 2 loops: stronger revision pass
- 3 loops: strongest freestyle writing gate

Never run more than 3 review loops for general writing.

## Required Local Outputs

Use:

```bash
python3 application-kit/scripts/writing_review_loop.py --root . prepare --input <relative-path> --mode <mode> --loops <1-3> --output-dir writing-reviews/<target>
```

This creates:

- `source-extracted.txt`
- `writing-review-manifest.json`
- `loop-<n>/chunk-<nnn>-input.json`

For each input packet, call:

```bash
node application-kit/scripts/mcp_check_client.mjs review writing-reviews/<target>/loop-<n>/chunk-<nnn>-input.json writing-reviews/<target>/loop-<n>/chunk-<nnn>-result.json
```

Then summarize:

```bash
python3 application-kit/scripts/writing_review_loop.py --root . report --manifest writing-reviews/<target>/writing-review-manifest.json
```

If the student wants a local SOP readiness receipt, record the final reviewed artifact with:

```bash
python3 application-kit/scripts/application_sop.py --root . review-writing --loop <n> --artifact <relative-draft-path> --result <result-json>
python3 application-kit/scripts/application_sop.py --root . finalize-writing --required-loops <1-3> --artifact <relative-draft-path>
```

## Privacy Rules

- Do not send the full workspace.
- Do not send photos, signatures, full CV files, or unrelated private notes.
- For long documents, send chunks only.
- For academic work, do not invent citations, sources, findings, methods, or data.
- For personal writing, do not copy another person's voice.
- The MCP result is feedback, not an authorship verdict or detector-bypass guarantee.

## Revision Rules

The local agent may revise the document after each loop, but must preserve facts and source boundaries.

For academic writing:

- keep claims scoped
- add method/evidence/limitation where missing
- do not fabricate citations
- do not weaken correctness just to sound casual

For work writing:

- make decisions, blockers, owners, dates, and next steps clearer
- preserve stakeholder commitments

For blog/social/general writing:

- improve human texture, rhythm, and reader value
- avoid fake slang, deliberate grammar errors, and synonym spinning
