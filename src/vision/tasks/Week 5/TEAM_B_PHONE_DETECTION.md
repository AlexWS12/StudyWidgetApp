# Team B - Phone Labeling Correctness and Robustness (Week 5)

## Context
Phone detection now uses calibration and persisted few-shot bundle data. Week 5 goal: make sure labels are truly correct in real use, not just detected once.

## Completed in Week 4 (Carryover)
- [x] Built interactive calibration flow with guide box and rotation phases
- [x] Added calibration test GUI for isolated validation
- [x] Hooked calibration flow into Camera startup workflow
- [x] Added calibration analysis for confidence/lighting recommendations
- [x] Added validation step (accept/retry/cancel)
- [x] Added clearer animated prompts for rotation guidance
- [x] Introduced few-shot appearance learning during calibration
- [x] Added weak-phase logging/debug visibility for calibration failures
- [x] Updated camera/test menu workflow for faster team testing

## Why Box-Only Is Not Enough
Guide-box center checks reduce noise but can still pass false positives when:
- a non-phone object appears inside the box
- a partial phone crop has center in-box but poor overlap
- one noisy frame spikes confidence

## Week 5 Status (Implemented So Far)

The phone-detection work evolved during implementation. This status reflects the current runtime code rather than the original step-by-step plan.

### Week 5 Progress (Completed)
- [x] Fixed a false-positive issue where YOLO was tracking the phone 3D model instead of the real phone target.

### 1) Spatial Validity (Guide Box)
- [ ] Replace center-in-box acceptance with overlap ratio gate
- [ ] Compute overlap as intersection_area / detection_box_area
- [ ] Require overlap >= 0.65 (tune after tests)
- [x] Keep guide-box overlay for user feedback

### 2) Appearance Validity (Few-Shot)
- [x] Keep few-shot similarity gate active when bundle exists
- [x] Log similarity score for accepted/rejected detections
- [ ] Tune threshold per environment using calibration outputs
- [x] Persist calibrated few-shot bundle and auto-load it in camera runtime

### 3) Temporal Validity (Anti-Flicker)
- [ ] Add temporal smoothing: detection accepted only if valid in N of last M frames
- [ ] Suggested start: N=4, M=5
- [x] Add absence cooldown before switching to PHONE_GONE / finalized distraction logging
- [x] Add high-confidence fallback path to preserve visual continuity when few-shot validation briefly rejects all candidates

### 4) Geometry Sanity Checks
- [ ] Reject implausible boxes (too small, too large, invalid aspect ratio)
- [ ] Reuse calibration-derived baseline geometry where possible

### 5) Score Fusion
- [ ] Build combined acceptance score using:
  - YOLO confidence
  - few-shot similarity
  - overlap ratio
- [ ] Compare fusion vs hard-threshold-only behavior

### 6) Validation Protocol
- [ ] Build a local validation set (~100 frames):
  - positives: phone in box under realistic poses
  - negatives: remote, wallet, hand-only, empty box, phone out of box
- [ ] Report precision/recall and false-positive count
- [ ] Track rejection reason distribution (overlap fail, similarity fail, geometry fail)

### Additional Work Implemented
- [x] Separated calibration from camera direct startup so calibration runs only from menu/calibration paths
- [x] Kept heavy calibration imports lazy so helper/runtime paths stay lightweight for integration
- [x] Added test runners and pytest coverage for vision-side distraction behavior

## Deliverables
- [x] Updated runtime gating logic (guide-box gate + few-shot gate + fallback handling)
- [ ] Validation metrics report (precision/recall + confusion summary)
- [ ] Recommended default thresholds for overlap, similarity, and temporal smoothing
