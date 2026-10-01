# <img src="assets/logo.gif" height="40" alt="Protego Logo"> Protego - I Protect. The Shield for Workers.

A real-time Personal Protective Equipment (PPE) detection system using Ultralytics YOLO26 and computer vision. This application monitors workplace safety through a webcam or video stream and reports missing hardhats, masks, and safety vests.

## ✨ Features

- 🎥 **Real-time Detection**: Live webcam feed with instant PPE detection & bounding boxes
- 🚀 **High Performance**: `requestAnimationFrame` frame dispatch & optimized detection intervals
- 🎯 **Accurate Recognition**: YOLO26s trained on the Construction Site Safety v27 dataset
- 📊 **Real-time Stat Cards**: Visual violation status badges (Safe / Violation) & category counters
- 🔊 **Voice Audio Alerts**: Web Speech API audio warnings with cooldown controls (`M` key toggle)
- 📜 **Live Incident Log**: Monospaced event stream with smooth fade-in animations
- 💻 **Single-Page Desktop Dashboard**: Minimalist, dark VC startup aesthetic fitted to a single non-scrollable screen
- ⚡ **WebSocket Communication**: Real-time bidirectional data streaming with auto-reconnect logic
- 🔧 **Customizable**: Adjustable detection parameters, thresholds, and model ensemble settings

## 🤖 Detection Models

The application runs two compatible 10-class models and merges their detections:

- `backend/models/ppe_yolo26s_v27.pt`: YOLO26s trained on the larger Construction Site Safety v27 dataset
- `backend/models/ppe_yolo.pt`: Original YOLOv8n PPE model used as a second detector

The ensemble improves coverage when one model misses a violation. Duplicate detections from both models are removed using class-aware IoU matching. The three classes treated as safety violations are `NO-Hardhat`, `NO-Mask`, and `NO-Safety Vest`.

## 🎬 Demo

> **Add your demo video or GIF here**
>
> ![Demo Screenshot](path/to/screenshot.png)

### Sample Detections

> **Add sample detection images here**
>
> | Input                            | Output                                 |
> | -------------------------------- | -------------------------------------- |
> | ![Sample 1](path/to/sample1.png) | ![Detection 1](path/to/detection1.png) |
> | ![Sample 2](path/to/sample2.png) | ![Detection 2](path/to/detection2.png) |

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11.x** (recommended for optimal compatibility)
- **Node.js & npm** (optional, for running via `npm start`)
- **Git** (for cloning the repository)
- **pip** (Python package installer)
- **Webcam/Camera** (for live detection)

### System Requirements

- **OS**: Linux, macOS, or Windows
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: ~2GB for dependencies and models

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/PrasanthPradeep/protego.git
cd protego
```

### 2. Set Up Python Environment

#### Create a Virtual Environment

```bash
# On Linux/macOS
python3.11 -m venv myvenv
source myvenv/bin/activate

# On Windows
python -m venv myvenv
myvenv\Scripts\activate
```

### 3. Install Dependencies

Navigate to the backend directory and install required packages:

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..
```

**Note**: This will install FastAPI, Uvicorn, PyTorch, Ultralytics YOLO, OpenCV, NumPy, and WebSockets.

### 4. Verify Model Files

Ensure both runtime models are present:

```bash
ls backend/models/ppe_yolo.pt backend/models/ppe_yolo26s_v27.pt
```

## 🧠 Training Dataset

The active training dataset is the downloaded Roboflow Construction Site Safety v27 dataset:

https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety

Local path:

```text
Construction Site Safety.v27-yolov8s.yolo26/
```

It uses YOLO labels with these ten classes:

```text
Hardhat, Mask, NO-Hardhat, NO-Mask, NO-Safety Vest,
Person, Safety Cone, Safety Vest, machinery, vehicle
```

Dataset size:

- 2,603 training images
- 114 validation images
- 82 test images
- 10 classes

The earlier 25-class dataset is preserved at `Construction Site Safety.v30-raw-images_latestversion.yolo26/`. Its converted 10-class copy is preserved at `Construction Site Safety.v30-10class.yolo26/`.

### Training on Windows with an NVIDIA GPU

The YOLO26 model was trained on Windows using an RTX 4060 Laptop GPU and CUDA-enabled PyTorch. From PowerShell in the project root:

```powershell
yolo detect train `
	model="yolo26s.pt" `
	data="Construction Site Safety.v27-yolov8s.yolo26\data.yaml" `
	epochs=200 `
	imgsz=640 `
	batch=8 `
	device=0 `
	workers=4 `
	patience=40 `
	project="runs" `
	name="ppe_yolo26s_v27"
```

The best checkpoint is saved at:

```text
runs\ppe_yolo26s_v27\weights\best.pt
```

Copy it to `backend/models/ppe_yolo26s_v27.pt` before starting the application. The conversion utility at [`scripts/convert_ppe_dataset.py`](scripts/convert_ppe_dataset.py) is only needed for the original 25-class dataset; v27 is already in the required 10-class format.

### Test-set Results

The trained YOLO26s v27 model was evaluated on the untouched test split:

- Precision: **92.0%**
- Recall: **74.6%**
- mAP@0.50: **80.6%**
- mAP@0.50:0.95: **55.1%**

PPE violation mAP@0.50:

- `NO-Hardhat`: **65.7%**
- `NO-Mask`: **87.2%**
- `NO-Safety Vest`: **83.6%**

Validate a new checkpoint with:

```powershell
yolo detect val `
	model="runs\ppe_yolo26s_v27\weights\best.pt" `
	data="Construction Site Safety.v27-yolov8s.yolo26\data.yaml" `
	split=test `
	device=0
```

## 🚀 Usage

### Starting the Application

You can start the server using either **npm** or **Python**:

#### Option A: Using NPM (Recommended)

```bash
npm start
```

Or for auto-reload during development:

```bash
npm run dev
```

#### Option B: Using Uvicorn directly

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

You should see output similar to:

```
📦 Loaded PPE classes: {0: 'Hardhat', 1: 'Mask', 2: 'NO-Hardhat', 3: 'NO-Mask', 4: 'NO-Safety Vest', 5: 'Person', 6: 'Safety Cone', 7: 'Safety Vest', 8: 'machinery', 9: 'vehicle'}
INFO:     Started server process [ ]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Accessing the Application

1. Open your web browser
2. Navigate to: `http://127.0.0.1:8080`
3. Allow camera access when prompted
4. The live detection feed will start automatically

### 🌐 Accessing from Mobile or Remote Devices over Internet

Browsers require **HTTPS** for camera permissions on remote devices:

```bash
# Using ngrok to generate a secure HTTPS tunnel
npx ngrok http 8080
```

Open the generated `https://xxxx.ngrok-free.app` URL on any phone or remote browser.

### Using the Interface

- **Live Video Feed**: Camera stream with real-time detection boxes
- **Stat Cards**: Real-time Safe/Violation badges for Hard Hat, Mask, and Safety Vest
- **Incident Log**: Auto-updating list of timestamped safety violations
- **Audio Alerts**: Voice warnings when violations occur (press **`M`** or click 🔊 to toggle)

## ⚙️ Configuration

You can customize the detection parameters in [`backend/main.py`](backend/main.py):

```python
# Performance Controls
DETECT_INTERVAL = 0.25      # Detection frequency (seconds)
RESULT_TTL = 0.6            # Result time-to-live (seconds)
JPEG_QUALITY = 65           # Image quality (1-100)
VIOLATION_COOLDOWN = 2.0    # Cooldown between violation alerts (seconds)
ENSEMBLE_IOU_THRESHOLD = 0.5 # Duplicate-box suppression threshold
```

## 📁 Project Structure

```
protego/
├── backend/
│   ├── main.py              # FastAPI application & WebSocket server
│   ├── detector.py          # Detection logic (legacy/unused)
│   ├── requirements.txt     # Python dependencies
│   ├── Procfile             # Deployment configuration
│   ├── models/
│   │   ├── ppe_yolo26s_v27.pt # YOLO26s model trained on v27
│   │   └── ppe_yolo.pt         # Original YOLOv8 PPE model
│   └── static/
│       └── index.html       # Web interface (Single-page dashboard)
├── package.json             # NPM scripts (start, dev)
├── package-lock.json        # NPM lockfile
├── myvenv/                  # Virtual environment (ignored by git)
├── LICENSE                  # Project license
└── README.md                # Documentation
```

## 🐛 Troubleshooting

### Common Issues

**1. Camera not accessible**

- Ensure your browser has permission to access the webcam
- HTTPS is required when accessing from external/remote devices

**2. Port already in use**

```bash
# Clear process using port 8080
fuser -k 8080/tcp
```

**3. Module not found errors**

```bash
# Ensure virtual environment is activated and requirements installed
source myvenv/bin/activate
pip install -r backend/requirements.txt
```

**4. New model file missing**

Copy the trained checkpoint to the exact path expected by `backend/main.py`:

```text
backend/models/ppe_yolo26s_v27.pt
```

Start Uvicorn from the `backend` directory because the application uses relative paths for `static/` and `models/`:

```bash
cd backend
../myvenv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## 👨‍💻 Author

**PrasanthPradeep** (https://github.com/PrasanthPradeep/)

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) for object detection and training
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [OpenCV](https://opencv.org/) for computer vision capabilities

---

**⚠️ Safety Notice**: This system is designed to assist with safety monitoring but should not be relied upon as the sole method of ensuring workplace safety compliance. Always follow proper safety protocols and guidelines.
