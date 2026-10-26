# Franklee language-classification deployment — 2026-10-26

- Source branch: `codex/franklee-language-classification-20261026`
- Final source commit: `097240e39b434c5c2f1f728fc3db02ee7394f706`
- Runtime target: `root@100.124.166.95:/root/clawdFrankLee/dist/job_search_prefilter.py`
- Installed SHA-256: `614534ae7792967e163277543cadca1d7201ce82c256b7d81db7a97f75dc1c62`
- Rollback copy of pre-deploy production file: `/root/.openclaw/backups/franklee-job-search-language-classification/20261026T205954Z/job_search_prefilter.py`
- An additional pre-follow-up-deploy copy is at `/root/.openclaw/backups/franklee-job-search-language-classification/20261026T210058Z/job_search_prefilter.py`.

## Verification

- Local validator/ranker/runner suite: 19 tests passed.
- Local Python compilation and `git diff --check`: passed.
- Production validator Python compilation: passed.
- No-delivery fixtures executed against the installed production module: English-only/English-required, German-plus, German-not-required, B1, B1+, C1 minimum in parentheses, and conflicting requirement statements all passed; evidence sanitization passed.
- `franklee-job-search-slack.timer` remained active. The service was not triggered manually; the 2026-10-26 scheduled run had already completed `0/SUCCESS` before deployment, and no test Slack post was sent.

## Rollback

Restore the pre-deploy production version with:

```bash
cp -a /root/.openclaw/backups/franklee-job-search-language-classification/20261026T205954Z/job_search_prefilter.py /root/clawdFrankLee/dist/job_search_prefilter.py
python3 -m py_compile /root/clawdFrankLee/dist/job_search_prefilter.py
```
