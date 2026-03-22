# Team A - Head Pose Tracking Reliability (Week 5)

## Context
Team A's MediaPipe migration is in place. Week 5 focuses on stabilizing head-pose-based attention-state quality and making outputs easier for the Intelligence pipeline to consume.
We are not using eye-tracking as the primary signal; the core signal is head pose (yaw/pitch/roll).

## Completed in Week 4 (Carryover)
- [x] Confirmed MediaPipe dependency setup in project workflow
- [x] Replaced Haar-based path with MediaPipe-based head pose pipeline
- [x] Initialized FaceMesh/landmarker path for pose-driven attention tracking
- [x] Completed integration pass that simplified attention-state validation with the rest of vision

## Week 5 Status (Implemented So Far)

The team did not execute the original Week 5 plan linearly. The checklist below reflects what is actually implemented in the current codebase.

### 1) Head-Pose State Stability
- [ ] Add temporal smoothing to attention-state transitions derived from head pose (rolling window or consecutive-frame confirmation)
- [x] Prevent the most brittle single-frame flips by adding tolerance around pose thresholds and a short no-face grace window
- [ ] Document chosen smoothing window size and why it balances responsiveness vs stability

### 2) Structured Output Hardening
- [x] Ensure each frame output includes consistent keys even when no face is present
- [ ] Include confidence-like score for gaze-state quality
- [x] Add clear no-face state semantics for downstream consumers
- [x] Keep tracker overlay neutral so camera-level attention messaging stays the single source of truth

### 3) Calibration Quality Checks
- [x] Add calibration support for non-top camera placement (e.g., side monitor webcam, lower laptop camera)
- [x] Add multi-screen-aware calibration by asking the user to look at all active screen corners
- [ ] Build screen boundary model from corner samples to create an allowed attention region/barrier
- [ ] Validate center/corner calibration across at least 3 lighting scenarios
- [ ] Re-run calibration after head posture changes and compare bounds drift
- [ ] Document acceptable variance for yaw/pitch/roll bounds between runs

### 4) Integration Readiness
- [x] Verify output remains stable enough to coexist with phone detector overlays and camera-level attention UI
- [x] Confirm performance remains acceptable by capping tracker rate and separating helper/runtime responsibilities
- [x] Add focused helper tests for threshold tolerance and transient-dropout stabilization

## Deliverables
- [x] Updated tracker logic with tolerance/grace-based stabilization
- [x] Updated calibration flow supporting off-center camera and multi-screen corner mapping
- [ ] Short test notes: false state flips before vs after smoothing
- [x] Updated attention output schema notes for integration
