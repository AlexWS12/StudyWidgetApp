import cv2 as cv
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

cap = cv.VideoCapture(0)

with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,  # Enables iris landmarks (468-477)
    min_detection_confidence=0.5,  # Play with this (0.0 - 1.0)
    min_tracking_confidence=0.5,   # Play with this (0.0 - 1.0)
) as face_mesh:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # MediaPipe expects RGB
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Draw all face mesh landmarks
                mp_drawing.draw_landmarks(
                    frame, face_landmarks,
                    mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style(),
                )

                # Print iris landmark coordinates to understand them
                left_iris = face_landmarks.landmark[468]   # Left iris center
                right_iris = face_landmarks.landmark[473]  # Right iris center
                print(f"Left iris: ({left_iris.x:.3f}, {left_iris.y:.3f})")
                print(f"Right iris: ({right_iris.x:.3f}, {right_iris.y:.3f})")

        cv.imshow("Iris Tracking", frame)
        if cv.waitKey(1) == ord("q"):
            break

cap.release()
cv.destroyAllWindows()