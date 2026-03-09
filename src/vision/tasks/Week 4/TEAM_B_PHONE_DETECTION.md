# Team B — YOLO Optimization & Detection Events (Paul & Josue)

## Context
Phone detection is working with `yolo26n.pt` and `classes=[67]`. This week we focus on **tuning for accuracy**, **documenting limits**, and **outputting structured detection data** so the rest of the app can react to phone presence.

---

## Phase 1: Parameter Experimentation

### Confidence Threshold (`conf`)
- [ ] Run detection with `conf=0.25` — count false positives over 1 minute of video
- [ ] Run detection with `conf=0.50` — same test, compare
- [ ] Run detection with `conf=0.75` — same test, compare
- [ ] Document: which value gives the best balance of catching phones vs avoiding false positives?
- [ ] Test with phone face-down, face-up, and at an angle — does `conf` affect which orientations are caught?

### IOU Threshold (`iou`)
- [ ] Test `iou=0.3` — note how it handles overlapping detections
- [ ] Test `iou=0.5` — compare
- [ ] Test `iou=0.7` — compare
- [ ] Document: when do overlapping boxes become a problem? (probably only with multiple phones)

### Image Size (`imgsz`)
- [ ] Test `imgsz=320` — note FPS and detection accuracy
- [ ] Test `imgsz=640` — compare (this is the default)
- [ ] Test `imgsz=1280` — compare
- [ ] Document the speed vs accuracy tradeoff — which is best for real-time webcam?

### Recommended Values
- [ ] Write up the recommended combination of `conf`, `iou`, and `imgsz` for our use case
- [ ] Update `camera.py` with the optimal parameter values

---

## Phase 2: Detection Limits

### Distance Testing
- [ ] Test phone detection at ~30cm from camera — document result
- [ ] Test at ~60cm — document
- [ ] Test at ~100cm — document
- [ ] Test at ~150cm+ — document where detection breaks
- [ ] Note: what's the minimum/maximum reliable distance?

### Angle Testing
- [ ] Test phone held straight-on (facing camera)
- [ ] Test phone at 45° angle
- [ ] Test phone at 90° (edge-on) — can YOLO still detect it?
- [ ] Test phone held behind/beside the user (partially visible)

### Lighting & Environment
- [ ] Test in well-lit room
- [ ] Test in dim lighting
- [ ] Test with backlight (window behind user)
- [ ] Does phone screen being on/off affect detection?

### Object Confusion
- [ ] Test with similar objects: tablet, TV remote, calculator, book
- [ ] Document any false positives with non-phone objects
- [ ] If false positives are common, note which objects trigger them

---

## Phase 3: Structured Detection Output

### Return Detection Data
- [ ] Add a method or update `read_frame()` to return structured data alongside the annotated frame
- [ ] Target format:
  ```python
  {
      "phone_detected": True,
      "phone_count": 1,
      "detections": [
          {
              "confidence": 0.87,
              "bbox": (x1, y1, x2, y2),  # bounding box coordinates
              "area_ratio": 0.05          # how much of frame the phone occupies
          }
      ]
  }
  ```
- [ ] Calculate `area_ratio` = (bbox area) / (frame area) — useful for knowing if phone is close vs far

### Detection Events
- [ ] Define events: `PHONE_APPEARED`, `PHONE_STILL_PRESENT`, `PHONE_GONE`
- [ ] Track phone presence across frames — don't fire `PHONE_APPEARED` every single frame
- [ ] Add a cooldown: only fire `PHONE_GONE` if phone has been absent for N frames (avoid flicker)
- [ ] Add timestamp to events for logging

---

## Phase 4: Per-User Phone Fine-Tuning

**Why:** Everyone's phone case is different. The generic COCO model detects "cell phone" but may struggle with unusual cases, colors, or orientations. Fine-tuning on each user's actual phone will improve accuracy significantly.

### Data Collection Pipeline
- [ ] Design a calibration flow: when a new user sets up the app, prompt them to show their phone to the camera
- [ ] Record a short video (~5 seconds) while the user slowly rotates their phone in front of the webcam
- [ ] Auto-extract ~20–30 frames from the video at regular intervals (skip near-duplicates)
- [ ] Save extracted frames to a per-user directory (e.g., `data/users/{user_id}/phone_images/`)
- [ ] The user only needs to do one quick video — the app handles the rest

### Auto-Labeling with Base Model
- [ ] Use the existing `yolo26n.pt` model to auto-label captured frames (it already knows "phone")
- [ ] Export auto-labels in YOLO format (class + bounding box coordinates)
- [ ] Review: manually spot-check labels — fix any that the base model got wrong
- [ ] Save labels alongside images in YOLO dataset structure:
  ```
  data/users/{user_id}/
  ├── images/
  │   ├── train/
  │   └── val/
  └── labels/
      ├── train/
      └── val/
  ```

### Fine-Tuning
- [ ] Create a YOLO dataset YAML config for the user's phone data
- [ ] Fine-tune from `yolo26n.pt` (transfer learning — NOT training from scratch)
- [ ] Use small epoch count (10–20) since we're just adapting, not retraining
- [ ] Save the fine-tuned model as `data/users/{user_id}/phone_model.pt`
- [ ] Test: compare detection accuracy between base model and fine-tuned model on user's phone
- [ ] Document the fine-tuning command and parameters

### Integration
- [ ] Update `Camera` class to load per-user model if available, fall back to base model
- [ ] Design the flow: first launch → calibration → fine-tune → switch to custom model
- [ ] Consider: re-calibrate option if user changes phone case

### Labeling Tool Options (if manual labeling needed)
- [ ] Try [Roboflow](https://roboflow.com/) — free tier, browser-based, exports YOLO format
- [ ] Try [CVAT](https://www.cvat.ai/) — open source, self-hosted option
- [ ] Try [Label Studio](https://labelstud.io/) — open source, Python-based
- [ ] Pick one and document the workflow for the team

---

## Phase 5: Stretch Goals
- [ ] Try `yolo26s.pt` (small) instead of `yolo26n.pt` (nano) — is accuracy noticeably better? Is it still fast enough?
- [ ] Explore: can we detect if the user is *holding* the phone vs phone just sitting on the desk?
- [ ] Consider: should we track other distracting objects? (e.g., game controllers, food)
- [ ] Explore: can we distinguish between "checking phone briefly" vs "scrolling for minutes"?

---

## Notes

### Files to Modify
- `src/vision/camera.py` — update YOLO parameters, add structured output, per-user model loading
- May create a new `phone_events.py` if event logic gets complex
- May create `calibration.py` for the phone capture/fine-tune pipeline

### Resources
- [Ultralytics YOLO Predict Docs](https://docs.ultralytics.com/modes/predict/) — conf, iou, imgsz params
- [Ultralytics Fine-Tuning Guide](https://docs.ultralytics.com/modes/train/) — transfer learning setup
- COCO class 67 = cell phone
