import os
import cv2
import torch
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer

from backend.src.entities.db_model import ImageSummary, ImageIngestion


def load_model():
    cfg = get_cfg()
    cfg.merge_from_file(r"C:\Users\Deepika Ramesh\Projects\asserts\models\config.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.8
    cfg.MODEL.WEIGHTS = r"C:\Users\Deepika Ramesh\Projects\asserts\models\model_final.pth"
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    return DefaultPredictor(cfg)


def detect_figures(predictor, image_path):
    image = cv2.imread(image_path)
    outputs = predictor(image)

    v = Visualizer(image[:, :, ::-1], MetadataCatalog.get("coco_2017_train"), scale=1.2)
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    return outputs["instances"], out.get_image()[:, :, ::-1]


def crop_and_save(instances, image_path, image_id, label="Figure", output_folder="cropped"):
    os.makedirs(output_folder, exist_ok=True)

    boxes = instances.pred_boxes.tensor.cpu().numpy()
    classes = instances.pred_classes.cpu().numpy()
    label_map = {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}

    im = Image.open(image_path)
    crops = []

    for idx, (box, cls) in enumerate(zip(boxes, classes)):
        if label_map[cls] == label:
            x1, y1, x2, y2 = map(int, box)
            cropped = im.crop((x1, y1, x2, y2))
            crop_path = os.path.join(output_folder, f"{image_id}_fig_{idx}.jpg")
            cropped.save(crop_path)
            crops.append(f"{image_id}_fig_{idx}.jpg")

    # Async-compatible DB insert
    ImageSummary.insert(
        image_id=image_id,
        cropped_image_list=crops,
        summary=""
    ).execute()

    return crops


def process_single_image(predictor, image_id, image_path, output_folder):
    try:
        instances, _ = detect_figures(predictor, image_path)
        cropped = crop_and_save(instances, image_path, image_id=image_id, output_folder=output_folder)
        os.remove(image_path)
        print(f"✅ Cropped {len(cropped)} figures from {image_path}")
        return f"✅ Cropped {len(cropped)} figures from {image_path}"
    except Exception as e:
        return f"❌ Error processing {image_id}: {e}"


def batch_process(predictor, batch_size=8):
    output_folder = r"C:\Users\Deepika Ramesh\Downloads\medical_data\cropped"
    image_dir = r"C:\Users\Deepika Ramesh\Downloads\medical_data\data\images"

    image_records = list(ImageIngestion.select(ImageIngestion.image_id))
    futures = []
    results = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        for record in image_records:
            image_id = record.image_id
            image_path = os.path.join(image_dir, f"{image_id}.jpg")

            if os.path.exists(image_path):
                futures.append(executor.submit(process_single_image, predictor, image_id, image_path, output_folder))

        for future in as_completed(futures):
            results.append(future.result())

    for res in results:
        print(res)


if __name__ == '__main__':
    predictor = load_model()
    batch_process(predictor)
