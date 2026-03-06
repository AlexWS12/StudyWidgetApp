# Team B — Phone Detection & Open Images (Paul & Josue)

## Getting Started
- [ ] Pull the `vision-team` branch
- [ ] Run `uv sync` to install dependencies
- [ ] Run `phone_detector.py` and confirm YOLO loads and detects objects
- [ ] Run `camera.py` and confirm the webcam feed works

---

## Paul — Camera + Live Phone Detection

### Combine Camera with YOLO
- [ ] Merge `camera.py` and `phone_detector.py` into a working live phone detector
- [ ] Add `classes=[67]` to filter detections for cell phones only
- [ ] Use `results[0].plot()` to draw bounding boxes on the frame
- [ ] Display the annotated frame in the OpenCV window

### Experiment with Parameters
- [ ] Change `conf` threshold — try 0.25, 0.5, 0.75. Note how it affects detection accuracy
- [ ] Change `iou` threshold — try 0.3, 0.5, 0.7. Note how it handles overlapping detections
- [ ] Change `imgsz` — try 320, 640, 1280. Note the speed vs accuracy tradeoff
- [ ] Test detecting phones at different distances and angles

### Document Findings
- [ ] Note which `conf` value gives the best balance of accuracy vs false positives
- [ ] Note at what distance/angle phone detection breaks
- [ ] Share findings in the team thread

---

## Josue — Open Images Dataset Research

### Understand the Baseline
- [ ] Test the pretrained COCO model on phone detection and document accuracy
- [ ] Count how many phone images are in the COCO dataset
- [ ] Identify limitations of COCO for phone detection (angles, phone types, distances)

### Research Open Images
- [ ] Look up the Open Images dataset — how many "Mobile Phone" images does it have?
- [ ] Understand the annotation format Open Images uses vs what YOLO expects
- [ ] Research how to convert Open Images annotations to YOLO format
- [ ] Find or draft a custom data YAML file for training YOLO on Open Images phone data

### Plan the Dataset Switch
- [ ] Document the steps needed to download just the phone subset of Open Images
- [ ] Estimate the dataset size and training time with the nano model
- [ ] Outline a plan for how we would fine-tune YOLO with the new dataset
- [ ] Share findings in the team thread

---

## Notes
_Use this space to jot down observations:_

