# Week 5 Summary - Detection Correctness and Integration Cleanup

## Objective
Improve phone labeling correctness beyond box-only gating by combining spatial, appearance, and temporal validation.

This workstream did not land strictly in the original planned order. The summary below reflects what is actually implemented in the current codebase.

## Completed in Week 4 (Carryover)
- [x] Interactive phone calibration flow shipped (guide box + rotation phases)
- [x] Calibration validation UX shipped (accept/retry/cancel)
- [x] Rotation guidance improvements shipped (animation + clearer prompts)
- [x] Few-shot appearance learning introduced in calibration flow
- [x] Team test menu flow added for quicker validation loops
- [x] Gaze-tracking integration path simplified for cross-team testing

## Key Technical Direction
- Spatial gate: overlap ratio with guide box (not center-only)
- Appearance gate: persisted few-shot similarity
- Temporal gate: N-of-M frame consistency
- Sanity gate: geometric plausibility checks
- Evaluation: precision/recall + rejection-reason analytics

## What Actually Landed
- Persisted few-shot bundle loading and runtime similarity gating in `camera.py`
- Guide-box filtering for uncalibrated phone placement
- High-confidence fallback path for visual continuity when few-shot validation rejects all candidates
- Menu-driven separation of camera launch vs calibration flows
- Camera no longer auto-runs calibration on direct startup
- Look-away / left-desk distraction-state integration with a 3-state camera-owned overlay
- Vision/intelligence pytest isolation with temp DB cleanup and direct-run-friendly team scripts
- Tracking robustness hardening via tolerance and short no-face grace handling

## Team Focus
- Team A: gaze-state smoothing and calibration consistency
- Team B: phone-label correctness implementation + metrics
- Team Lead: integration contract, telemetry, release gating

## Scope Correction
- Grounding DINO and ByteTrack experimentation exists in the repository, but that path is not the current main camera runtime and should not be treated as the completed Week 5 runtime outcome.

## Exit Criteria
- False positives reduced in guide-box scenarios
- Minimal detection flicker
- Thresholds documented and reproducible
- Runtime behavior understandable through reason-coded rejects
