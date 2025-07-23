import os

import cv2
import torch
from PIL import Image
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer

from backend.src.entities.db_model import ImageSummary, ImageIngestion


def load_model():
    cfg = get_cfg()
    cfg.merge_from_file(r"C:\Users\Deepika Ramesh\Projects\med_rag\asserts\models\config.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.8
    cfg.MODEL.WEIGHTS = r"C:\Users\Deepika Ramesh\Projects\med_rag\asserts\models\model_final.pth"
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    return DefaultPredictor(cfg)


def detect_figures(predictor, image_path):
    image = cv2.imread(image_path)
    outputs = predictor(image)

    v = Visualizer(image[:, :, ::-1], MetadataCatalog.get("coco_2017_train"), scale=1.2)
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))

    return outputs["instances"], out.get_image()[:, :, ::-1]


def crop_detected_regions(instances, image_path, image_id = None, label="Figure", output_folder="cropped"):
    os.makedirs(output_folder, exist_ok=True)
    boxes = instances.pred_boxes.tensor.cpu().numpy()
    classes = instances.pred_classes.cpu().numpy()

    # PubLayNet: label mappings
    label_map = {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}

    im = Image.open(image_path)
    crops = []

    for idx, (box, cls) in enumerate(zip(boxes, classes)):
        if label_map[cls] == label:
            x1, y1, x2, y2 = map(int, box)
            cropped = im.crop((x1, y1, x2, y2))
            crop_path = os.path.join(output_folder,
                                     f"{image_id}_fig_{idx}.jpg")
            cropped.save(crop_path)
            crops.append(crop_path)
            q = ImageSummary.insert(
                image_id=image_id,
                cropped_image_name=f"{image_id}_fig_{idx}",
                summary=""
            )
            q.execute()
    return crops


if __name__ == '__main__':

    predictor = load_model()
    for record in ImageIngestion.select(ImageIngestion.image_id):
        image_id = record.image_id
        image_path = fr"C:\Users\Deepika Ramesh\Projects\med_rag\data\images\{image_id}.jpg"
        instances, vis_image = detect_figures(predictor, image_path)

        figure_crops = crop_detected_regions(instances, image_path, image_id=image_id)
        print(f"Cropped {len(figure_crops)} figures from {image_path}")
