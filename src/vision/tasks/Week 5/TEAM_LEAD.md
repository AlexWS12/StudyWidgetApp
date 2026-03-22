# Team Lead - Week 5 Integration and Quality Gate

## Context
Week 5 focus is quality assurance across the full attention + phone pipeline, with emphasis on phone-label correctness in real-world conditions.

## Completed in Week 4 (Carryover)
- [x] Reviewed Team B calibration flow, heuristics, and parameter experiments
- [x] Supported Team B on threshold tuning and weak-detection filtering
- [x] Ran both teams' code together and surfaced early integration issues
- [x] Ensured MediaPipe dependency inclusion in project dependencies
- [x] Ran calibration flow from camera path and test GUI path
- [x] Improved calibration guidance animation and preview behavior
- [x] Simplified gaze-detection validation path after Team A migration
- [x] Built menu flow for faster calibration and feature testing
- [x] Partnered with Team B on phone-calibration optimization (UX + thresholds)

## Management Priorities
- [ ] Confirm Team B's labeling validation protocol is executed and documented
- [ ] Ensure Team A and Team B smoothing choices do not conflict in responsiveness
- [ ] Review threshold defaults before merge (confidence, overlap, few-shot, temporal)

## Team Lead Work Completed in Week 5
- [x] Built menu flow for cleaner launch-camera vs calibration separation
- [x] Removed duplicate runtime DB/bootstrap responsibility from vision menu path
- [x] Set up pytest-based vision/intelligence isolation with shared fixtures and temp DB cleanup
- [x] Added direct-run-friendly test helpers and folder-local test scripts for team workflows
- [x] Refactored runtime imports to keep vision helper paths lightweight for integration
- [x] Added camera-level 3-state attention UI (`ATTENTIVE`, `LOOK_AWAY`, `LEFT_DESK`)
- [x] Unified no-face behavior so look-away can transition into left-desk after sustained absence
- [x] Hardened tracking behavior with tolerance/grace handling for integration stability

## Notes on Scope Corrections
- Grounding DINO/ByteTrack experimentation exists in the repo, but those items are not the current main `camera.py` runtime path and should not be counted as completed runtime integration work for Week 5.

## Integration Tasks

### 1) Unified Detection Contract
- [ ] Define final accepted-phone criteria in one place:
  - in guide region by overlap ratio
  - passes few-shot similarity
  - passes temporal consistency window
- [ ] Require reason-coded rejection path for debugging

### 2) Observability
- [ ] Add lightweight runtime telemetry counters:
  - total phone candidates
  - accepted detections
  - rejected by overlap
  - rejected by few-shot
  - rejected by temporal gate
- [ ] Surface counters in logs or debug panel for quick diagnosis

### 3) Performance and UX Balance
- [ ] Verify gates do not reduce FPS below target
- [ ] Confirm user-facing prompts remain clear when detection is rejected
- [ ] Keep guide-box messaging actionable (not generic failures)

### 4) Release Readiness Criteria
- [ ] Precision target agreed and met on validation set
- [ ] False positives in empty-box scenario below agreed threshold
- [x] No severe flicker in distraction-state transitions caused by transient no-face drops is reduced via tolerance/grace handling
- [x] Calibration overwrite behavior verified across repeated runs well enough for persisted bundle/profile usage

## Deliverables
- [x] Integration checklist substantially advanced through runtime/test cleanup
- [ ] Short release note summarizing reliability gains and remaining risks
