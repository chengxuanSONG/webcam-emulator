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
            key = cv2.waitKey(30)
            if key == ord('q') or cv2.getWindowProperty("AVI Preview", cv2.WND_PROP_VISIBLE) < 1:
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
        subject_id = subject_entry.get().strip().replace('\n', '').replace('\r', '')
        session_id = session_entry.get().strip().replace('\n', '').replace('\r', '')
        task_type = task_combo.get()
        #fps = int(fps_entry.get())
        fps_text = fps_entry.get()
        if not fps_text.isdigit():
            messagebox.showerror("Input Error", "FPS input must be an integer")
            return
        fps = int(fps_text)
        if frame_mode.get() == "frame":
            total_frames = int(total_entry.get())
        else:
            duration_seconds = float(total_entry.get())
            total_frames = int(duration_seconds * fps)
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

        window_name = "Recording... Press 'q' to stop early. "
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
        if save_channels_var.get():
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
    
    

    # Combine Subject ID and Session ID on the same line
    id_frame = tk.Frame(root, bg="#f0f0f5")
    id_frame.pack(fill="x", padx=10, pady=(6, 2))
    # Subject ID
    sub_label = tk.Label(id_frame, text="Subject ID", bg="#f0f0f5", font=("Arial", 12))
    sub_label.pack(side=tk.LEFT)
    subject_entry = tk.Entry(id_frame, font=("Arial", 12), width=12)
    subject_entry.pack(side=tk.LEFT, padx=(4, 10))

    # Session ID
    ses_label = tk.Label(id_frame, text="Session ID", bg="#f0f0f5", font=("Arial", 12))
    ses_label.pack(side=tk.LEFT)
    session_entry = tk.Entry(id_frame, font=("Arial", 12), width=12)
    session_entry.pack(side=tk.LEFT, padx=4)
    tk.Label(root, text="Supports letters, numbers, and symbols", bg="#f0f0f5", fg="gray", font=("Arial", 9)).pack(anchor="w", padx=12)
        
    #FPS settings
    fps_frame = tk.Frame(root, bg="#f0f0f5")
    fps_frame.pack(pady=2, fill="x")

    fps_left = tk.Frame(fps_frame, bg="#f0f0f5")
    fps_left.pack(side=tk.LEFT, padx=8, expand=True, fill="x")
    tk.Label(fps_left, text="Frame Rate (FPS)", bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
    fps_entry = tk.Entry(fps_left, font=("Arial", 11))
    fps_entry.pack(fill="x")
    #tk.Label(fps_left, text="Must be an integer (e.g., 20, 30)", bg="#f0f0f5", fg="gray", font=("Arial", 9)).pack(anchor="w")

    try:
        probe_cam = cv2.VideoCapture(0)
        fps_range = probe_cam.get(cv2.CAP_PROP_FPS)
        fps_label = tk.Label(root, text=f"⚙️Must be an integer; Your built-in camera reports max FPS: {fps_range:.1f}", fg="gray", bg="#f0f0f5")
        fps_label.pack()
        probe_cam.release()
    except Exception as e:
        print("FPS check failed:", e)

    frame_mode = tk.StringVar(value="frame") 

    mode_frame = tk.Frame(root, bg="#f0f0f5")
    mode_frame.pack(anchor="w", padx=10, pady=(4, 0))
    tk.Label(mode_frame, text="Choose capture mode:", bg="#f0f0f5", font=("Arial", 10)).pack(side=tk.LEFT)
    tk.Radiobutton(mode_frame, text="Number of Frames", variable=frame_mode, value="frame", bg="#f0f0f5").pack(side=tk.LEFT, padx=8)
    tk.Radiobutton(mode_frame, text="Duration (Seconds)", variable=frame_mode, value="time", bg="#f0f0f5").pack(side=tk.LEFT, padx=8)


    frame_input_frame = tk.Frame(root, bg="#f0f0f5")
    frame_input_frame.pack(pady=2, fill="x")

    frame_right = tk.Frame(frame_input_frame, bg="#f0f0f5")
    frame_right.pack(side=tk.LEFT, padx=8, expand=True, fill="x")
    total_label = tk.Label(frame_right, text="Number of Frames", bg="#f0f0f5", font=("Arial", 11))
    total_label.pack(anchor="w")
    total_entry = tk.Entry(frame_right, font=("Arial", 11))
    total_entry.pack(fill="x")
    total_hint = tk.Label(frame_right, text="e.g., 100 = 5 seconds @ 20 FPS", bg="#f0f0f5", fg="gray", font=("Arial", 9))
    total_hint.pack(anchor="w")


    def update_frame_mode():
        if frame_mode.get() == "frame":
            total_label.config(text="Number of Frames")
            total_hint.config(text="e.g., 100 = 5 seconds @ 20 FPS")
        else:
            total_label.config(text="Duration (Seconds")
            total_hint.config(text="e.g., 5 = 5 seconds")

    frame_mode.trace_add("write", lambda *args: update_frame_mode())

    #gain settings
    ex_frame = tk.Frame(root, bg="#f0f0f5")
    ex_frame.pack(pady=2, fill="x")

    # Gain
    gain_block = tk.Frame(ex_frame, bg="#f0f0f5")
    gain_block.pack(side=tk.LEFT, padx=8, expand=True, fill="x")
    tk.Label(gain_block, text="Gain (optional)", bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
    gain_entry = tk.Entry(gain_block, font=("Arial", 11), fg="gray")
    gain_entry.insert(0, "128")
    gain_entry.pack(fill="x")

    def on_gain_focus_in(event):
        if gain_entry.get() == "128":
            gain_entry.delete(0, tk.END)
            gain_entry.config(fg="black")

    def on_gain_focus_out(event):
        if gain_entry.get().strip() == "":
            gain_entry.insert(0, "128")
            gain_entry.config(fg="gray")

    gain_entry.bind("<FocusIn>", on_gain_focus_in)
    gain_entry.bind("<FocusOut>", on_gain_focus_out)

    # Exposure
    exposure_block = tk.Frame(ex_frame, bg="#f0f0f5")
    exposure_block.pack(side=tk.LEFT, padx=8, expand=True, fill="x")
    tk.Label(exposure_block, text="Exposure (optional)", bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
    exposure_entry = tk.Entry(exposure_block, font=("Arial", 11), fg="gray")
    exposure_entry.insert(0, " -4.0")
    exposure_entry.pack(fill="x")

    def on_exposure_focus_in(event):
        if exposure_entry.get() == "-4.0":
            exposure_entry.delete(0, tk.END)
            exposure_entry.config(fg="black")

    def on_exposure_focus_out(event):
        if exposure_entry.get().strip() == "":
            exposure_entry.insert(0, "-4.0")
            exposure_entry.config(fg="gray")

    


    # Data Type (folder)
    type_frame = tk.Frame(root, bg="#f0f0f5")
    type_frame.pack(fill="x", padx=10, pady=(4, 2))
    tk.Label(type_frame, text="Data Type (folder)", bg="#f0f0f5", font=("Arial", 11)).pack(side=tk.LEFT)

    # Help button for data type info
    info_text = """
    func: functional recording (e.g., task-video)
    anat: anatomical or static imaging (e.g., T1w, infrared)
    fmap: field mapping or calibration (e.g., darkmap)
    custom: define your own
    """

    def show_data_type_help():
        tk.messagebox.showinfo("Data Type Explanation", info_text)

    help_button = tk.Button(type_frame, text="?", font=("Arial", 8, "bold"), width=2, bg="#ddd", command=show_data_type_help)
    help_button.pack(side=tk.LEFT, padx=6)

    # Combine task type and filename base on same line
    filename_frame = tk.Frame(root, bg="#f0f0f5")
    filename_frame.pack(fill="x", padx=10, pady=(4, 4))

    # Task type dropdown
    tk.Label(filename_frame, text="Data Type", bg="#f0f0f5", font=("Arial", 10)).pack(side=tk.LEFT)
    task_combo = ttk.Combobox(filename_frame, font=("Arial", 10), state="readonly", width=10)
    task_combo['values'] = ["func", "anat", "fmap", "custom"]
    task_combo.set("func")
    task_combo.pack(side=tk.LEFT, padx=4)

    # File name base
    tk.Label(filename_frame, text="Custom FIle Label", bg="#f0f0f5", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10, 0))
    filename_entry = tk.Entry(filename_frame, font=("Arial", 10), width=22)
    filename_entry.pack(side=tk.LEFT, padx=(4, 0))
    # Recording label hint
    tk.Label(root, text="                                                                     e.g. sub-01/ses-01/func/task-video", bg="#f0f0f5", fg="gray", font=("Arial", 9)).pack(anchor="w", padx=12, pady=(0, 2))

    # Preview current BIDS path live
    preview_path_label = tk.Label(root, text="📂 BIDS Path Preview: None", font=("Arial", 12), fg="black", bg="#f0f0f5")
    preview_path_label.pack(pady=(2, 0))

    def update_path_preview(*args):
        sid = subject_entry.get().strip().replace('\n', '').replace('\r', '')
        ses = session_entry.get().strip().replace('\n', '').replace('\r', '')
        task = task_combo.get()
        
        if sid and ses and task:
            preview_path_label.config(text=f"📂 BIDS Path Preview: Output Folder/sub-{sid}/ses-{ses}/{task}/")
        else:
            preview_path_label.config(text="📂 BIDS Path Preview: Incomplete")

    subject_entry.bind("<KeyRelease>", update_path_preview)
    session_entry.bind("<KeyRelease>", update_path_preview)
    task_combo.bind("<<ComboboxSelected>>", update_path_preview)

    def on_task_selected(event):
        if task_combo.get() == "custom":
            import tkinter.simpledialog as sd
            custom_type = sd.askstring("Custom Data Type", "Enter your custom data type (e.g., calibration):")
            if custom_type:
                task_combo.set(custom_type)
            else:
                task_combo.set("func")

    task_combo.bind("<<ComboboxSelected>>", on_task_selected)

    

    #filename_entry = labeled_entry("Custom File Label", "e.g. sub-01_ses-01_func_task-video")

    tk.Label(root, text="Camera Device", bg="#f0f0f5", font=("Arial", 11)).pack()
    camera_options = []
    for i in range(4):
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.read()[0]:
            name = f"{i} - Built-in Camera" if i == 0 else f"{i} - Camera {i}"
            if "obs" in cap.getBackendName().lower():
                name += " (OBS VirtualCam)"
            camera_options.append(name)
            cap.release()
        else:
            camera_options.append(f"{i} - (Unavailable)")

    camera_combo = ttk.Combobox(root, font=("Arial", 10), values=camera_options, state="readonly")
    camera_combo.set("0 - Built-in Webcam")
    camera_combo.pack(pady=4)


    # Optional checkbox: whether to save RGB channels separately
    save_channels_var = tk.BooleanVar(value=True)
    save_channels_check = tk.Checkbutton(root, text="Save RGB Channels Separately", variable=save_channels_var, bg="#f0f0f5", font=("Arial", 10))
    save_channels_check.pack(anchor="w", padx=12)

    
    exposure_entry.bind("<FocusIn>", on_exposure_focus_in)
    exposure_entry.bind("<FocusOut>", on_exposure_focus_out)
    output_frame = tk.Frame(root, bg="#f0f0f5")
    output_frame.pack(pady=2)
    tk.Label(output_frame, text="Output Folder", bg="#f0f0f5", font=("Arial", 11)).pack(anchor="w")
    output_dir_entry = tk.Entry(output_frame, font=("Arial", 11), width=40)
    output_dir_entry.pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(output_frame, text="Browse", command=browse_output_directory).pack(side=tk.LEFT)



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
