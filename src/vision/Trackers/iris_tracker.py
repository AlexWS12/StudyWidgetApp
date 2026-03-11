# iris_tracker.py
# Eye tracking using MediaPipe Face Landmarker + Iris

import cv2 as cv
import mediapipe as mp
import os
import numpy as np

from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions


class eyeTracker:

    def __init__(self):

        model_path = os.path.join(
            os.path.dirname(__file__),
            "face_landmarker.task"
        )

        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1
        )

        self.detector = vision.FaceLandmarker.create_from_options(options)

        self.landmarks = None
        self.neutral_pitch = None  # used for vertical calibration

    # -----------------------------------------

    def track_eyes(self, frame):

        gaze_text = "Gaze: N/A"

        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(mp_image)

        self.landmarks = None

        if result.face_landmarks:

            self.landmarks = result.face_landmarks[0]

            data = self.extract_eye_data(self.landmarks, frame)

            self.draw_head_pose(frame, self.landmarks)

            h, w, _ = frame.shape

            left_iris = [474, 475, 476, 477]
            right_iris = [469, 470, 471, 472]

            for idx in left_iris + right_iris:
                lm = self.landmarks[idx]
                x = int(lm.x * w)
                y = int(lm.y * h)
                cv.circle(frame, (x, y), 2, (0, 255, 0), -1)

            gaze_text = f"Gaze: {data['gaze_state_horizontal']} {data['gaze_state_vertical']}"

        cv.putText(
            frame,
            gaze_text,
            (30, 40),
            cv.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        return frame

    # -----------------------------------------

    def extract_eye_data(self, landmarks, frame):

        data = {
            "face_present": landmarks is not None,
            "eyes_detected": False,
            "left_iris": None,
            "right_iris": None,
            "gaze_state_horizontal": None,
            "gaze_state_vertical": None
        }

        if landmarks is None:
            return data

        w, h = frame.shape[1], frame.shape[0]

        pitch, yaw, roll, _, _, _, _ = self.estimate_head_pose(landmarks, frame)

        # calibrate neutral pitch once
        if self.neutral_pitch is None:
            self.neutral_pitch = pitch

        pitch_offset = pitch - self.neutral_pitch

        # --- Iris centers ---
        right_iris = landmarks[468]
        left_iris = landmarks[473]

        rx, ry = int(right_iris.x * w), int(right_iris.y * h)
        lx, ly = int(left_iris.x * w), int(left_iris.y * h)

        data["eyes_detected"] = True
        data["right_iris"] = (rx, ry)
        data["left_iris"] = (lx, ly)

        # ---------------------------------
        # Horizontal iris gaze
        # ---------------------------------

        right_eye_left = int(landmarks[33].x * w)
        right_eye_right = int(landmarks[133].x * w)

        left_eye_left = int(landmarks[362].x * w)
        left_eye_right = int(landmarks[263].x * w)

        right_ratio = (rx - right_eye_left) / (right_eye_right - right_eye_left)
        left_ratio = (lx - left_eye_left) / (left_eye_right - left_eye_left)

        avg_ratio = (right_ratio + left_ratio) / 2

        if avg_ratio < 0.40:
            iris_horizontal = "left"
        elif avg_ratio > 0.60:
            iris_horizontal = "right"
        else:
            iris_horizontal = "center"

        # ---------------------------------
        # Head horizontal
        # ---------------------------------

        if yaw < -10:
            head_horizontal = "left"
        elif yaw > 10:
            head_horizontal = "right"
        else:
            head_horizontal = "center"

        # ---------------------------------
        # Vertical from pitch offset
        # ---------------------------------

        if pitch_offset < -1.5:
            head_vertical = "down"
        elif pitch_offset > 1.5:
            head_vertical = "up"
        else:
            head_vertical = "center"

        # ---------------------------------
        # Combine iris + head
        # ---------------------------------

        final_horizontal = iris_horizontal
        final_vertical = head_vertical

        if head_horizontal != "center":
            final_horizontal = head_horizontal

        data["gaze_state_horizontal"] = final_horizontal
        data["gaze_state_vertical"] = final_vertical

        return data

    # -----------------------------------------

    def estimate_head_pose(self, landmarks, frame):

        h, w = frame.shape[:2]

        image_points = np.array([
            (landmarks[1].x * w, landmarks[1].y * h),
            (landmarks[152].x * w, landmarks[152].y * h),
            (landmarks[33].x * w, landmarks[33].y * h),
            (landmarks[263].x * w, landmarks[263].y * h),
            (landmarks[61].x * w, landmarks[61].y * h),
            (landmarks[291].x * w, landmarks[291].y * h)
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -63.6, -12.5),
            (-43.3, 32.7, -26),
            (43.3, 32.7, -26),
            (-28.9, -28.9, -24),
            (28.9, -28.9, -24)
        ], dtype="double")

        focal_length = w
        center = (w / 2, h / 2)

        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")

        dist_coeffs = np.zeros((4, 1))

        success, rotation_vector, translation_vector = cv.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            dist_coeffs
        )

        rotation_matrix, _ = cv.Rodrigues(rotation_vector)

        pose_matrix = cv.hconcat((rotation_matrix, translation_vector))

        _, _, _, _, _, _, euler_angles = cv.decomposeProjectionMatrix(pose_matrix)

        pitch = float(euler_angles[0][0])
        yaw = float(euler_angles[1][0])
        roll = float(euler_angles[2][0])

        pitch = (pitch + 180) % 360 - 180
        yaw = (yaw + 180) % 360 - 180
        roll = (roll + 180) % 360 - 180

        return pitch, yaw, roll, rotation_vector, translation_vector, camera_matrix, dist_coeffs

    # -----------------------------------------

    def draw_head_pose(self, frame, landmarks):

        pitch, yaw, roll, rotation_vector, translation_vector, camera_matrix, dist_coeffs = \
            self.estimate_head_pose(landmarks, frame)

        h, w = frame.shape[:2]

        nose = (int(landmarks[1].x * w), int(landmarks[1].y * h))

        axis = np.float32([
            [100, 0, 0],
            [0, 100, 0],
            [0, 0, 100]
        ])

        imgpts, _ = cv.projectPoints(
            axis,
            rotation_vector,
            translation_vector,
            camera_matrix,
            dist_coeffs
        )

        x_axis = tuple(imgpts[0].ravel().astype(int))
        y_axis = tuple(imgpts[1].ravel().astype(int))
        z_axis = tuple(imgpts[2].ravel().astype(int))

        cv.line(frame, nose, x_axis, (0, 0, 255), 3)
        cv.line(frame, nose, y_axis, (0, 255, 0), 3)
        cv.line(frame, nose, z_axis, (255, 0, 0), 3)