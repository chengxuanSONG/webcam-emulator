# ui/main_window.py (伪多摄像头版本)
import os
import cv2
import time
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
from core import camera, metadata, converter, database
import subprocess
import platform
import json
import sqlite3

def launch_app():
    frames = []
    frame_count = 0
    def open_folder(path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def preview_avi_file():
        file_path = filedialog.askopenfilename(filetypes=[("AVI Video", "*.avi")])
        if not file_path:
            return
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Failed to open video file.")
            return
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("AVI Preview", frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def view_json_metadata():
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
        with open(file_path, 'r') as f:
            data = json.load(f)
        top = tk.Toplevel()
        top.title("Metadata Preview")
        text = tk.Text(top, wrap="word")
        text.insert("1.0", json.dumps(data, indent=4))
        text.pack(expand=True, fill="both")

    def show_db_sessions():
        if not os.path.exists("recordings.db"):
            messagebox.showinfo("DB", "No recordings.db file found.")
            return
        conn = sqlite3.connect("recordings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        top = tk.Toplevel()
        top.title("Recent Sessions")
        text = tk.Text(top, wrap="none")
        text.insert("1.0", "id | subject_id | session_id | timestamp | frame_count | file_base\n")
        text.insert("2.0", "-" * 120 + "\n")
        for row in rows:
            text.insert("end", str(row) + "\n")
        text.pack(expand=True, fill="both")

    def start_recording():
        nonlocal frames, frame_count, last_output_dir
        subject_id = subject_entry.get()
        session_id = session_entry.get()
        task_type = task_combo.get()
        fps = int(fps_entry.get())
        total_frames = int(frame_entry.get())
        gain = gain_entry.get()
        exposure = exposure_entry.get()
        output_dir = output_dir_entry.get()
        filename_base = filename_entry.get()

        gain = float(gain) if gain.strip() != '' else 128
        exposure = float(exposure) if exposure.strip() != '' else None

        selected_label = camera_combo.get()
        selected_index = int(selected_label.split(" - ")[0])

        if not subject_id or not session_id or not fps or not total_frames or not output_dir or not filename_base:
            messagebox.showerror("Input Error", "Please enter all fields.")
            return

        last_output_dir = output_dir

        if selected_index >= 2:
            messagebox.showinfo("Simulated Device", f"'{selected_label}' is a placeholder and not a real camera.")
            return

        cap = camera.initialize_camera(selected_index)
        camera.set_camera_settings(cap, gain, exposure)
        frames.clear()
        frame_count = 0

        window_name = "Recording..."
        cv2.namedWindow(window_name)

        while frame_count < total_frames:
            frame = camera.read_frame(cap)
            cv2.imshow(window_name, frame)
            frames.append(frame)
            frame_count += 1
            if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):
                break

        camera.release_camera(cap)

        bids_path = os.path.join(output_dir, f"sub-{subject_id}", f"ses-{session_id}", task_type)
        os.makedirs(bids_path, exist_ok=True)
        file_base = os.path.join(bids_path, filename_base)
        video_file = file_base + ".avi"
        hdf5_file = file_base + ".h5"
        json_file = file_base + "_metadata.json"
        channel_dir = file_base + "_channels"

        height, width, _ = frames[0].shape
        out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))
        for f in frames:
            out.write(f)
        out.release()

        converter.save_frames_to_hdf5(frames, hdf5_file)
        converter.split_and_save_channels(frames, channel_dir)

        meta = metadata.generate_metadata(subject_id, session_id, frame_count, {
            "gain": gain,
            "exposure": exposure,
            "fps": fps
        })
        metadata.save_metadata_to_json(meta, json_file)

        conn = database.initialize_database()
        database.insert_session_metadata(conn, subject_id, session_id, meta['timestamp'], frame_count, file_base)
        conn.close()

        messagebox.showinfo("Done", f"Recording saved to:\n{file_base}.*")
        open_button.config(state=tk.NORMAL)

    def preview_hdf5_file():
        file_path = filedialog.askopenfilename(filetypes=[("HDF5 files", "*.h5")])
        if file_path:
            converter.preview_hdf5(file_path)

    def open_last_output():
        if last_output_dir:
            open_folder(last_output_dir)

    def browse_output_directory():
        path = filedialog.askdirectory()
        if path:
            output_dir_entry.delete(0, tk.END)
            output_dir_entry.insert(0, path)

    last_output_dir = None

    root = tk.Tk()
    root.title("📹 Webcam Scientific Recorder")
    root.geometry("500x740")
    root.configure(bg="#f0f0f5")

    def labeled_entry(label_text, help_text=None):
        frame = tk.Frame(root, bg="#f0f0f5")
        frame.pack(pady=2)
        tk.Label(frame, text=label_text, bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
        entry = tk.Entry(frame, font=("Arial", 11))
        entry.pack()
        if help_text:
            tk.Label(frame, text=help_text, bg="#f0f0f5", font=("Arial", 9), fg="gray").pack(anchor="w")
        return entry

    subject_entry = labeled_entry("Subject ID")
    session_entry = labeled_entry("Session ID")
    fps_entry = labeled_entry("Frame Rate (FPS)")
    frame_entry = labeled_entry("Number of Frames", "e.g. 100 frames = 5s at 20 FPS")
    gain_entry = labeled_entry("Gain(optional)", "Camera gain 0–255; leave blank to use 128")
    exposure_entry = labeled_entry("Exposure(optional)", "Exposure time (leave blank for auto; default = -4.0)")

    output_frame = tk.Frame(root, bg="#f0f0f5")
    output_frame.pack(pady=2)
    tk.Label(output_frame, text="Output Folder", bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
    output_dir_entry = tk.Entry(output_frame, font=("Arial", 11), width=40)
    output_dir_entry.pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(output_frame, text="Browse", command=browse_output_directory).pack(side=tk.LEFT)

    filename_entry = labeled_entry("File Name Base", "e.g. sub-01_ses-01_task-video")

    tk.Label(root, text="Data Type (folder)", bg="#f0f0f5", font=("Arial", 11)).pack()
    task_combo = ttk.Combobox(root, font=("Arial", 10), state="readonly")
    task_combo['values'] = ["func", "anat", "fmap", "custom"]
    task_combo.set("func")
    task_combo.pack(pady=4)

    tk.Label(root, text="Camera Device", bg="#f0f0f5", font=("Arial", 11)).pack()
    camera_combo = ttk.Combobox(root, font=("Arial", 10))
    camera_combo['values'] = [
        "0 - Built-in Webcam",
        "1 - External Cam A",
        "2 - IR Sensor B",
        "3 - SPAD Array (Sim)",
        "4 - VirtualCam"
    ]
    camera_combo.set(camera_combo['values'][0])
    camera_combo.pack(pady=4)

    tk.Button(root, text="🎬 Start Recording", font=("Arial", 11), bg="#4CAF50", fg="white", width=44, command=start_recording).pack(pady=6)

    preview_frame = tk.Frame(root, bg="#f0f0f5")
    preview_frame.pack(pady=4)
    tk.Button(preview_frame, text="Preview HDF5", font=("Arial", 10), bg="#2196F3", fg="white", width=13, command=preview_hdf5_file).grid(row=0, column=0, padx=2, pady=2)
    tk.Button(preview_frame, text="Preiew AVI", font=("Arial", 10), bg="#9C27B0", fg="white", width=13, command=preview_avi_file).grid(row=0, column=1, padx=2, pady=2)
    tk.Button(preview_frame, text="Preview JSON", font=("Arial", 10), bg="#795548", fg="white", width=13, command=view_json_metadata).grid(row=0, column=2, padx=2, pady=2)
    tk.Button(preview_frame, text="Preview DB", font=("Arial", 10), bg="#607D8B", fg="white", width=13, command=show_db_sessions).grid(row=0, column=3, padx=2, pady=2)

    # 📁 Open Folder
    open_button = tk.Button(root, text="📁 Open Last Output Folder", font=("Arial", 11), bg="#FFC107", fg="black", width=44, state=tk.DISABLED, command=open_last_output)
    open_button.pack(pady=6)

    # ❌ Exit
    tk.Button(root, text="❌ Exit", font=("Arial", 11), bg="gray", fg="white", width=44, command=root.destroy).pack(pady=6)

    root.mainloop()
