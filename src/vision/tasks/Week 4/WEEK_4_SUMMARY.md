# Vision Team — Week 4 Summary

## Overview
Full week sprint. Team A migrates from Haar cascades to MediaPipe (no training required). Team B tunes YOLO parameters and documents detection limits. Team Lead handles integration, management, and codebase cleanup.

---

## Team A — MediaPipe Migration (Shah & Alex)
**Goal:** Replace Haar cascade eye tracker with MediaPipe Face Mesh + Iris for accurate gaze tracking.

**Key Deliverables:**
1. Rewrite `iris_tracker.py` with MediaPipe (`refine_landmarks=True` for iris)
2. Tune detection/tracking confidence parameters
3. Return structured data (gaze state, attention confidence, iris positions)
4. Define attention states: ATTENTIVE, LOOKING_AWAY, EYES_CLOSED, FACE_NOT_VISIBLE
5. Add temporal smoothing to reduce state flickering

**Important:** No model training needed — MediaPipe ships pre-trained.

---

## Team B — YOLO Optimization (Paul & Josue)
**Goal:** Find optimal detection parameters and document where phone detection breaks down.

**Key Deliverables:**
1. Test `conf` (0.25, 0.5, 0.75), `iou` (0.3, 0.5, 0.7), `imgsz` (320, 640, 1280)
2. Document detection limits (distance, angle, lighting, similar objects)
3. Return structured detection data (phone_detected, confidence, bbox)
4. Implement detection events (PHONE_APPEARED, PHONE_GONE) with cooldown

---

## Team Lead — Integration & Management (Jorge)
**Goal:** Keep teams unblocked, clean up codebase, build the integration layer.

**Key Deliverables:**
1. Code reviews for both teams' PRs
2. Codebase cleanup (folder structure, `__init__.py` files, dependencies)
3. Design unified vision output format (attention + distraction data)
4. Prototype vision → app event system
5. Database schema for study session data
6. Mid-week and end-of-week check-ins

---

## Week 4 Priorities (ranked)
1. **Team A:** Get MediaPipe running and returning iris landmarks
2. **Team B:** Document optimal YOLO parameters
3. **Lead:** Codebase cleanup and dependency management
4. **Team A:** Structured attention data output
5. **Team B:** Structured detection data output
6. **Lead:** Integration layer connecting vision to app
7. **All:** Event system design for vision → UI communication
