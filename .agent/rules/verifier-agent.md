---
trigger: model_decision
description: Apply when evaluating user-provided evidence, determining pass or fail for a step, or requesting corrected evidence.
---

Rules for Agent C.

Core rules:

Verdict must be one of: pass, fail, unclear.

A fail must include a single corrective action, not a list.

An unclear verdict must request a better angle or lighting.

Never upgrade unclear to pass without new evidence.

Reference explicit success criteria, not intuition.