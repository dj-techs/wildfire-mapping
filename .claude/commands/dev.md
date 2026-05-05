---
description: Boot the Dash app locally on :8050 with auth disabled.
---

Activate the venv, ensure data exists, and run the dev server.

```bash
source .venv/bin/activate 2>/dev/null || (python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)
test -f data/wildfires.csv || python scripts/generate_dummy_data.py
AUTH_DISABLED=true python -m app.server
```
