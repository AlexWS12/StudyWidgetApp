# Team A - Tracking Robustness and Integration Tolerance (Week 6)

## Context
Team A now owns the reliability pass for head-pose-based attention tracking as the vision helper subsystem is prepared for cleaner integration with the rest of the app.
The focus this week is not adding new heavy features, but making tracking outputs more tolerant, more stable, and easier for downstream consumers to trust.

## Completed in Week 5 (Carryover)
- [x] MediaPipe head-pose tracking is the primary attention signal
- [x] Neutral tracker overlay avoids conflicting with camera-level attention messaging
- [x] Corner-based gaze calibration persists user-specific screen-facing bounds
- [x] Camera-level 3-state attention display (`ATTENTIVE`, `LOOK_AWAY`, `LEFT_DESK`) is wired into runtime flow

## Week 6 Priorities

### 1) Runtime Tolerance and Stability
- [x] Add small pose tolerance around calibrated/default bounds so tracking is less brittle near thresholds
- [x] Prevent single noisy pose samples from immediately flipping attention state
- [x] Add short grace window for transient no-face detector dropouts
- [ ] Tune tolerance values against real webcams with different camera placements

### 2) Failure Handling
- [x] Make tracker degrade gracefully when MediaPipe/OpenCV detection fails temporarily
- [x] Avoid camera-loop crashes from transient tracker errors
- [ ] Add lightweight debug flag to surface when tracker is running in degraded mode

### 3) Integration Contract Quality
- [x] Keep tracker output schema consistent even during degraded/no-face periods
- [x] Keep final attention messaging owned by camera.py instead of duplicating tracker semantics
- [ ] Confirm downstream consumers do not depend on raw `attention_state` naming quirks

### 4) Validation
- [x] Add focused helper tests for permissive threshold behavior and dropout stabilization
- [ ] Compare false no-face / false away rate before vs after the Week 6 hardening pass
- [ ] Record recommended threshold defaults for shared integration notes

## Deliverables
- [x] Tracker helper methods for tolerance and stabilization
- [x] Focused unit/helper tests covering the new permissive behavior
- [ ] Short integration note summarizing remaining edge cases for other teams