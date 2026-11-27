# LLM-Generated Software Security

Research prototype for CENG 573 and proposed extension for CENG 585. The study investigates vulnerability detection, remediation and privilege separation in LLM-generated Flask applications.

**Local laboratory only.** The initial and baseline variants intentionally retain the generated insecure configuration. Never deploy them or use real user data. Keep the repository private pending advisor and publication-policy review.

## Versions
- `applications/initial`: first prototype, recovered from PDF pages 1–12.
- `applications/baseline`: feature-complete pre-remediation version, recovered from pages 34–55; primary comparison baseline.
- `applications/remediated`: user-supplied current source, not a claim of complete security.

PDF recovery normalizes indentation and line wrapping, including a clipped import. It is not byte-identical provenance. See `docs/generation_history.md`.

## Local setup
Use Python 3.11 (original project environment), create a virtual environment, and install `requirements.txt`. Run one variant at a time from its own directory using `python app.py`. Open http://127.0.0.1:5000. Use synthetic accounts only. Stop the server before switching variants. Each variant creates its own database when launched from its directory.

## Research status
Prior findings reported by the student: hardcoded secret and debug mode; remediation of these two findings. Raw reports are pending import. SQL injection, application fuzzing, DAST and privilege separation experiments are pending. No new security results are claimed by this archive.
