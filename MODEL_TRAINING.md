# Protego Model Training Guide

This document has two purposes:

1. Record how the Protego PPE model was trained and installed.
2. Provide a reusable step-by-step workflow for training an Ultralytics YOLO model on another dataset.

The commands use the Ultralytics CLI and work with YOLO26, YOLO11, YOLOv8, and other Ultralytics detection models. Change only the model, dataset, and hardware values described below.

## Quick Workflow

For a new object-detection dataset, follow this order:

1. Prepare or download the dataset in Ultralytics YOLO format.
2. Check `data.yaml`, class names, and label IDs.
3. Create a Python environment and install Ultralytics.
4. Choose a pretrained model and train with a validation split.
5. Validate the saved `best.pt` on the untouched test split.
6. Run predictions on sample images and inspect false positives and missed objects.
7. Deploy `best.pt` only after its results are acceptable for the application.

## 1. Choose or Prepare a Dataset

The workflow supports any dataset that has images and YOLO detection labels. The Protego dataset below is the project example, not a requirement for other users.

### Required YOLO Dataset Layout

Use this structure, or update the paths in `data.yaml` to match your layout:

```text
my-dataset/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

Each image should have a label file with the same filename stem. For example:

```text
train/images/site-001.jpg
train/labels/site-001.txt
```

Each YOLO label line must contain:

```text
class_id center_x center_y width height
```

The coordinates are normalized from `0` to `1`. `class_id` is a zero-based integer that must match the order in `data.yaml`.

### Dataset Configuration Example

```yaml
train: ../train/images
val: ../valid/images
test: ../test/images

nc: 2
names: [helmet, person]
```

If the dataset came from Roboflow, Kaggle, or another tool, inspect the downloaded `data.yaml` before training. Do not assume that class names or class IDs match another dataset.

### Protego Dataset Example

The active dataset is Roboflow Construction Site Safety v27:

https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety

The downloaded dataset is stored in:

```text
Construction Site Safety.v27-yolov8s.yolo26/
```

It contains:

- 2,603 training images
- 114 validation images
- 82 test images
- 10 classes

The class order is:

```text
0 Hardhat
1 Mask
2 NO-Hardhat
3 NO-Mask
4 NO-Safety Vest
5 Person
6 Safety Cone
7 Safety Vest
8 machinery
9 vehicle
```

The v27 dataset already uses the required 10-class format, so no label conversion was needed for this project.

## 2. Preserve the Earlier Dataset

The original 25-class dataset was kept unchanged:

```text
Construction Site Safety.v30-raw-images_latestversion.yolo26/
```

A separate 10-class conversion was also created for comparison:

```text
Construction Site Safety.v30-10class.yolo26/
```

The conversion script is:

```text
scripts/convert_ppe_dataset.py
```

The active training run used v27 because it has about five times more training images than the original v30 training split.

## 3. Prepare the Training Environment

Training can run on Windows, Linux, WSL2, or macOS. An NVIDIA GPU is recommended for practical training speed. The Protego model was trained on Windows with an NVIDIA RTX 4060 Laptop GPU.

On Windows, create and activate a virtual environment in PowerShell:

```powershell
py -3.11 -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install a CUDA-enabled PyTorch build using the command provided by:

https://pytorch.org/get-started/locally/

Then install Ultralytics:

```powershell
pip install ultralytics
```

Verify that CUDA is available:

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"
```

The expected result is `True` followed by the NVIDIA GPU name.

On Linux or WSL2, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install ultralytics
```

If no GPU is available, use `device=cpu` and a small model such as `yolo26n.pt`, `yolo11n.pt`, or `yolov8n.pt`. Training will be slower.

If a model filename is not recognized, update Ultralytics in the active environment:

```powershell
python -m pip install --upgrade ultralytics
```

## 4. Validate the Dataset Before Training

Before training, confirm that the dataset configuration points to the correct split directories:

```powershell
Get-Content ".\Construction Site Safety.v27-yolov8s.yolo26\data.yaml"
```

The file must define `train`, `val`, and `test`, and must contain `nc: 10` with the class order listed above.

Also verify that each image has a matching label and that every label ID is between 0 and 9. Do not change only `nc` without remapping label IDs.

For another dataset, check the number of classes from its own `data.yaml`; do not assume it is `10`. The `nc` value, `names` list, and label IDs must agree. Keep validation and test images separate from training images.

## 5. Select a Model and Train

Use a pretrained checkpoint from the same model family you want to train. The model family does not need to match the dataset format beyond being supported by the installed Ultralytics version.

Examples:

```text
YOLO26: yolo26n.pt, yolo26s.pt, yolo26m.pt
YOLO11: yolo11n.pt, yolo11s.pt, yolo11m.pt
YOLOv8: yolov8n.pt, yolov8s.pt, yolov8m.pt
```

For detection, use the regular detection checkpoint, not a segmentation, pose, classification, or OBB checkpoint. A model trained for one task cannot be used unchanged for another task.

The following section first records the Protego YOLO26s run, then provides a reusable command for any supported YOLO version.

There is no single best epoch count for every dataset. `epochs=200` was the maximum configured for this project, not a requirement. Early stopping ended this run at epoch 187, and the best checkpoint was from epoch 147. Ultralytics saves the best validation checkpoint as `best.pt`, so training can stop before the configured maximum without losing the best model.

Recommended starting settings:

| Dataset size            | Starting epochs | Patience |
| ----------------------- | --------------: | -------: |
| Fewer than 1,000 images |         100-150 |    20-30 |
| 1,000-10,000 images     |         150-250 |    30-50 |
| More than 10,000 images |         200-300 |    40-60 |

These are starting points, not guarantees. Use a validation split and keep early stopping enabled. More epochs do not automatically improve accuracy; if validation mAP stops improving, more training can waste time or overfit.

Choose the model size according to hardware:

- `yolo26n.pt`: fastest and suitable for CPU or low-memory GPUs
- `yolo26s.pt`: good accuracy/speed balance and used for this project
- `yolo26m.pt` or larger: potentially more accurate, but requires more VRAM and inference time

Choose `batch` based on available GPU memory. Start with `batch=8` on an 8 GB GPU, reduce to `4` or `2` if CUDA runs out of memory, or use `batch=-1` to let Ultralytics select an automatic batch size on supported GPU training.

From the project root, with the Windows virtual environment active, run:

The following command reproduces the Protego v27 training run. For another project, replace the `model`, `data`, `name`, and hardware-dependent values as described below.

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

For another dataset, keep the same command structure but change `data` and choose the model, `epochs`, `batch`, and `imgsz` for that dataset and hardware. A practical default is `epochs=150` to `200`, `patience=30` to `50`, and `imgsz=640`.

### Reusable Training Template

Use this template for a different YOLO detection dataset:

```powershell
yolo detect train `
  model="yolo26s.pt" `
  data="path\to\your\data.yaml" `
  epochs=150 `
  imgsz=640 `
  batch=8 `
  device=0 `
  workers=4 `
  patience=30 `
  project="runs" `
  name="my_yolo26_training"
```

Replace `yolo26s.pt` with another supported detection checkpoint when needed, for example `yolo11s.pt` or `yolov8s.pt`. Also rename the run to match the model family, such as `my_yolo11_training` or `my_yolov8_training`.

On Linux or macOS, use the same command with backslashes removed and normal shell line continuations:

```bash
yolo detect train \
  model=yolo26s.pt \
  data=/path/to/my-dataset/data.yaml \
  epochs=150 \
  imgsz=640 \
  batch=8 \
  device=0 \
  workers=4 \
  patience=30 \
  project=runs \
  name=my_yolo26_training
```

Change these values:

- `model`: choose a pretrained detection checkpoint such as `yolo26n.pt`, `yolo26s.pt`, `yolo11s.pt`, or `yolov8s.pt`.
- `data`: point to the dataset's `data.yaml` file.
- `epochs`: set the maximum training duration; early stopping may finish sooner.
- `imgsz`: use `640` normally; increase it for very small objects if GPU memory allows.
- `batch`: start at `8` on an 8 GB GPU, then reduce to `4` or `2` if needed.
- `device`: use `0` for the first NVIDIA GPU or `cpu` when no compatible GPU is available.
- `workers`: use `2-4` on a typical Windows machine; reduce it if data loading causes problems.
- `name`: choose a unique run name so earlier results are not overwritten.

Do not change `nc` or the class names manually unless the label IDs in every annotation file match the new class order. The class order in `data.yaml` must match the numeric IDs in the YOLO label files.

Training stopped at epoch 187 because early stopping detected no improvement for 40 epochs. The best checkpoint was observed at epoch 147. This confirms why `best.pt`, rather than the final epoch, should be deployed.

The important output file is:

```text
runs\ppe_yolo26s_v27\weights\best.pt
```

Use `best.pt` for deployment. `last.pt` is only the final checkpoint and is not necessarily the best-performing checkpoint.

## 6. Evaluate on the Test Split

The test split was kept separate from training and validation. Evaluate the best checkpoint with:

```powershell
yolo detect val `
  model="runs\ppe_yolo26s_v27\weights\best.pt" `
  data="Construction Site Safety.v27-yolov8s.yolo26\data.yaml" `
  split=test `
  device=0
```

For another dataset or YOLO version, use the same validation command with the paths for that run:

```powershell
yolo detect val `
  model="runs\my_yolo26_training\weights\best.pt" `
  data="path\to\your\data.yaml" `
  split=test `
  device=0
```

Use `split=val` when the dataset has no test split, but treat the result as validation performance rather than a final unbiased test score. Check precision, recall, mAP@0.50, and mAP@0.50:0.95. For safety applications, pay particular attention to recall for classes representing missing PPE.

The final test results were:

| Metric        | Result |
| ------------- | -----: |
| Precision     |  92.0% |
| Recall        |  74.6% |
| mAP@0.50      |  80.6% |
| mAP@0.50:0.95 |  55.1% |

Important violation-class results:

| Class            | Precision | Recall | mAP@0.50 |
| ---------------- | --------: | -----: | -------: |
| `NO-Hardhat`     |     86.6% |  63.1% |    65.7% |
| `NO-Mask`        |     90.2% |  82.0% |    87.2% |
| `NO-Safety Vest` |     97.2% |  76.2% |    83.6% |

## 7. Install the Trained Protego Model

This section applies to the Protego application. For another application, copy `best.pt` to that application's model directory and update its model-loading code.

Copy the best checkpoint into the backend model directory and rename it:

```text
runs\ppe_yolo26s_v27\weights\best.pt
```

to:

```text
backend\models\ppe_yolo26s_v27.pt
```

The backend loads this model from `backend/main.py`.

## 8. Use Both Models at Runtime in Protego

The application uses two compatible 10-class models:

```text
backend/models/ppe_yolo26s_v27.pt
backend/models/ppe_yolo.pt
```

The YOLO26s model is the primary model. The original YOLOv8 model is used as a second detector because it sometimes detects violations that YOLO26s misses.

For each frame, the backend:

1. Runs both models.
2. Combines their detections.
3. Removes duplicate boxes when the class matches and IoU is at least `0.5`.
4. Draws the merged detections on the output frame.
5. Logs `NO-Hardhat`, `NO-Mask`, and `NO-Safety Vest` as high-severity violations.

This ensemble improves detection coverage, but it requires more inference time because two models run for each detection cycle.

## 9. Start Protego

Start Uvicorn from the `backend` directory because the application uses relative paths for `static/` and `models/`:

```bash
cd backend
../myvenv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

On Windows, use the activated environment and run:

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

Open the dashboard at:

```text
http://127.0.0.1:8080
```

The server should print the loaded 10-class mapping when startup succeeds.

## 10. Verify the Runtime Pipeline

The live pipeline was checked by:

- Starting the FastAPI server successfully.
- Loading `ppe_yolo26s_v27.pt` and confirming all 10 classes.
- Sending a JPEG frame through `/ws/safety`.
- Confirming that the response contained `frame`, `violations`, and `logs`.
- Running inference on a real dataset image.

The WebSocket endpoint is:

```text
ws://127.0.0.1:8080/ws/safety
```

## Notes

- The model metrics describe test-set performance, not guaranteed real-world accuracy.
- The model may miss violations in images that differ substantially from construction-site training images, such as clean portrait photos.
- For further improvement, add labeled images from the actual deployment camera, especially difficult `NO-Hardhat`, `NO-Mask`, and `NO-Safety Vest` examples.
- The system is an assistance tool and should not be the only workplace safety control.
