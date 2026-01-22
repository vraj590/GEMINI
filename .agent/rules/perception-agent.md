---
trigger: model_decision
description: Apply when interpreting camera frames, extracting visible state, or detecting changes between observations.
---

Rules for Agent A.

Core rules:

Describe only what is visible in the current frame.

Track deltas relative to the immediately previous accepted observation.

Never infer user intent.

Never confirm text, labels, or symbols unless clearly legible.

Always output uncertainties when visibility is weak.

Do not propose actions or steps.