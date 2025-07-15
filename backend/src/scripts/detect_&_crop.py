import os
from uuid import uuid4

import cv2
import torch
from PIL import Image
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from pdf2image import convert_from_path

from backend.src.entities.db_model import ImageSummary


def _pdf_to_image(pdf_path, output_folder="images", dpi=200, file_id=None):
    os.makedirs(output_folder, exist_ok=True)
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=r"C:\poppler-24.08.0\Library\bin")
    image_paths = []

    for i, page in enumerate(pages):
        image_path = os.path.join(output_folder, f"{file_id}_page_{i+1}.jpg")
        page.save(image_path, "JPEG")
        image_paths.append(image_path)

    return image_paths

def load_model():
    cfg = get_cfg()
    cfg.merge_from_file(r"C:\Users\Deepika Ramesh\Projects\med_rag\asserts\models\config.yaml")
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.8
    cfg.MODEL.WEIGHTS = r"C:\Users\Deepika Ramesh\Downloads\model_final (2).pth"
    cfg.MODEL.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    return DefaultPredictor(cfg)

def detect_figures(predictor, image_path):
    image = cv2.imread(image_path)
    outputs = predictor(image)

    v = Visualizer(image[:, :, ::-1], MetadataCatalog.get("coco_2017_train"), scale=1.2)
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))

    return outputs["instances"], out.get_image()[:, :, ::-1]


def crop_detected_regions(instances, image_path, label="Figure", output_folder="cropped", file_id=None, file_name=None):
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
            crop_path = os.path.join(output_folder, f"{file_id}_{os.path.basename(image_path).split('.')[0]}_fig_{idx}.jpg")
            cropped.save(crop_path)
            crops.append(crop_path)
            q = ImageSummary.insert(
                file_id = file_id,
                full_page_name = os.path.basename(image_path).split('.')[0],
                cropped_image_name = f"{file_id}_{os.path.basename(image_path).split('.')[0]}_fig_{idx}",
                file_name = file_name,
                summary = ""
            )
            q.execute()
    return crops

if __name__ == '__main__':
    pdf_path = r"C:\Users\Deepika Ramesh\Downloads\medical_data\5_6125289260120543446 (1).pdf"
    file_id = str(uuid4())  # Unique identifier for the file
    image_paths = _pdf_to_image(pdf_path, file_id = file_id)
    predictor = load_model()
    file_name = os.path.basename(pdf_path).split('.')[0]
    for img_path in image_paths:
        instances, vis_image = detect_figures(predictor, img_path)

        # vis_path = img_path.replace(".jpg", "_vis.jpg")
        # Image.fromarray(vis_image).save(vis_path)

        # Crop and save figure regions
        figure_crops = crop_detected_regions(instances, img_path, file_id=file_id, file_name = file_name)
        print(f"Cropped {len(figure_crops)} figures from {img_path}")
