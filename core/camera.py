import cv2

def list_available_cameras(max_index=5):
    available = []
    for index in range(max_index):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            available.append(index)
        cap.release()
    return available

def initialize_camera(index=0):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")
    return cap

def set_camera_settings(cap, gain=None, exposure=None):
    if gain is not None:
        cap.set(cv2.CAP_PROP_GAIN, float(gain))
    if exposure is not None:
        cap.set(cv2.CAP_PROP_EXPOSURE, float(exposure))

def release_camera(cap):
    cap.release()
    cv2.destroyAllWindows()

def read_frame(cap):
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to read frame from camera")
    return frame