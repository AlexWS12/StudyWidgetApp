"""Enumerate available video capture devices via OpenCV."""

import cv2 as cv


def list_cameras(max_index: int = 8) -> list[dict]:
    """Probe camera indices 0..max_index-1 and return those that open.

    Each entry is ``{"index": int, "name": str}`` where *name* is a
    human-readable label.  OpenCV's generic backend doesn't expose device
    names, so the label is synthesised from the index.

    Args:
        max_index: Upper bound (exclusive) of indices to probe.

    Returns:
        List of available cameras sorted by index.
    """
    cameras: list[dict] = []
    for idx in range(max_index):
        cap = cv.VideoCapture(idx)
        if cap.isOpened():
            cameras.append({"index": idx, "name": f"Camera {idx}"})
            cap.release()
    return cameras
