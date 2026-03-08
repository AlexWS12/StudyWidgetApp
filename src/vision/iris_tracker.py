class IrisTracker:
    def __init__(self):
        self.state = "TRACKING_UNCERTAIN"

    def process_frame(self, frame):
        return {
            "frame": frame,
            "face_present": False,
            "eyes_detected": False,
            "iris_detected": False,
            "gaze_state": "unknown",
            "attention_confidence": 0.0,
            "state": self.state,
        }