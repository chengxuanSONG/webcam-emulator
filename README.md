# 🎥 Webcam Scientific Workflow Emulator

This project provides a Python-based GUI application to emulate scientific data collection workflows using a webcam. It mimics the structure and logic of neuroscience-style imaging pipelines with support for video capture, metadata storage, color channel splitting, HDF5 output, and SQLite-based session tracking.

---

## 🚀 Features

- ✅ **Live webcam capture** with FPS, gain, exposure control  
- ✅ Save recordings as `.avi` + `.h5` + `.json` metadata  
- ✅ BIDS-like folder structure: `sub-01/ses-01/func/...`  
- ✅ Channel splitting: RGB frames saved independently  
- ✅ Embedded **SQLite database** for session tracking  
- ✅ GUI built with Tkinter (no browser needed)  
- ✅ One-click preview of:  
  - 🎞️ Recorded `.avi` video  
  - 🖼️ `.h5` data preview  
  - 📖 JSON metadata  
  - 📋 Database session logs  
- ✅ Simulated camera options for testing/demo  
- ✅ `.gitignore`, `requirements.txt`, `environment.yml` included  

---

## 📦 Installation

> This application is designed and tested on **Windows 10/11** systems with a built-in or USB webcam.

To get started, follow these steps:

### 1. 📁 Download the Latest Release

- Go to the [Releases](https://github.com/chengxuanSONG/webcam-emulator/releases) page.
- Download the latest `.zip` archive (e.g., `webcam-emulator-v1.2.1.zip`).
- Extract the files to any folder on your computer.
- Then, open a terminal (e.g.PowerShell, CMD or Anaconda Prompt) and use `cd` to change into the extracted folder:

```bash
cd yourPath_to\webcam-emulator-v1.2.1
```


### 2. 🛠️ Set Up Your Python Environment

> First-time users need to install required packages. You can use either conda or pip:

### Option 1 (Recommended) – conda users:

```bash
conda env create -f environment.yml
conda activate webcam_emulator
python bidsrec.py
```

### Option 2 – pip users:

```bash
pip install -r requirements.txt
python bidsrec.py
```
### 3. 🧩 Known Startup Warning (Windows)

If you see messages like the following in the terminal when launching the app bidsrec.py:

```bash    
[ERROR:0@8.563] global obsensor_uvc_stream_channel.cpp:158 cv::obsensor::getStreamChannelGroup Camera index out of range
[WARN:0@7.617] global cap_msmf.cpp:476 `anonymous-namespace'::SourceReaderCB::OnReadSample videoio(MSMF): OnReadSample() is called with error status: -1072875772 
```

📌 **Don't worry!**  
These warnings are normal when OpenCV tries to probe camera devices using the Microsoft Media Foundation (MSMF) backend and doesn't find any additional sources.

✅ The application will continue to work normally. Just wait a few seconds for it to finish scanning available devices.






## 🛠 GUI Controls

| Field            | Description                                 |
|------------------|---------------------------------------------|
| Subject ID       | Participant code (e.g. `sub-01`)            |
| Session ID       | Session block (e.g. `ses-01`)               |
| FPS              | Frame rate (e.g. 20)                        |
| Number of Frames | Total frames to capture (e.g. 100)          |
| Gain / Exposure  | Camera light sensitivity (optional)         |
| Data Type        | `func`, `anat`, `fmap`, or `custom`         |
| Custom File Label| Naming base for all output files            |
| Output Folder    | Root path to save data                      |

---

## 🗂 Output Folder Structure (BIDS-like)

<output_folder>/  
├── sub-01/  
│└── ses-01/  
│  └── func/  
│     ├── sub-01_ses-01_task-video.avi  
│     ├── sub-01_ses-01_task-video.h5  
│     ├── sub-01_ses-01_task-video_metadata.json  
│     └── sub-01_ses-01_task-video_channels/


---

## 💾 Output Files Formats

- `.avi` – raw video file  
- `.h5` – RGB image stack in HDF5 format  
- `.json` – camera & recording metadata  
- `SQLite` – persistent session logging  
- `Channels/` – separate R/G/B image streams (Optional)

---

## 📊 Database Schema

Recording sessions are saved to an embedded SQLite database `recordings.db` in the root directory.

See [`docs/database.md`](./docs/database.md) for full table definitions and schema documentation.

---


## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ Author

Developed by **Sam Song**, inspired by scientific reproducibility in data workflows.  
Feel free to fork, contribute, or reach out!

