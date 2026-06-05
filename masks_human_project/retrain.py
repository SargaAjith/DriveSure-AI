from ultralytics import YOLO

model = YOLO("best.pt")  # start from existing weights

model.train(
    data="dataset.yaml",
    epochs=50,           # fine-tune only, not full retrain
    imgsz=640,
    batch=8,
    lr0=0.0001,          # low LR — fine-tuning
    lrf=0.01,
    optimizer="AdamW",
    patience=15,
    augment=True,
    mosaic=0.5,
    mixup=0.0,
    project="runs/finetune",
    name="damage_neg_v2",
    exist_ok=True,
    pretrained=True,
    resume=False
)

print("Training complete.")
print("New model: runs/finetune/damage_neg_v2/weights/best.pt")
