---
trigger: glob
---

This protects your orchestration logic.

Core rules:

Enforce schema validation on every agent response.

Retry once on invalid JSON, otherwise fail loudly.

Never let frontend directly call model APIs.

Persist observations, deltas, and artifacts separately.

Prefer idempotent endpoints for resume safety.