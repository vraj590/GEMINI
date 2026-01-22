---
trigger: always_on
---

Core rules:

Treat the system as a closed-loop state machine, not a chat flow.

Never skip verification for steps marked as critical.

Persist state changes explicitly, no implicit assumptions.

Resume sessions only from last verified step.

Prefer asking for evidence over guessing.

Every agent output must be machine-consumable JSON.