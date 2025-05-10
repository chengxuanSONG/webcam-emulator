import h5py
import numpy as np
import cv2
import os
import threading

def save_frames_to_hdf5(frames, filename):
    with h5py.File(filename, 'w') as f:
        f.create_dataset('video', data=np.array(frames), compression="gzip")

def split_and_save_channels(frames, base_path):
    os.makedirs(base_path, exist_ok=True)
    for i, frame in enumerate(frames):
        b, g, r = cv2.split(frame)
        cv2.imwrite(os.path.join(base_path, f"frame_{i:04d}_red.jpg"), r)
        cv2.imwrite(os.path.join(base_path, f"frame_{i:04d}_green.jpg"), g)
        cv2.imwrite(os.path.join(base_path, f"frame_{i:04d}_blue.jpg"), b)

def preview_hdf5(hdf5_file, frame_index=0):
    def show_frame():
        with h5py.File(hdf5_file, 'r') as f:
            frames = f['video'][:]
            if frame_index < len(frames):
                frame = frames[frame_index]
                cv2.imshow("HDF5 Preview", frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
    threading.Thread(target=show_frame).start()

def get_bids_path(output_root, subject_id, session_id):
    bids_root = os.path.join(output_root, f"sub-{subject_id}", f"ses-{session_id}", "func")
    os.makedirs(bids_root, exist_ok=True)
    return bids_root