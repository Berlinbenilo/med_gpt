from pathlib import Path
from typing import List
from uuid import uuid4
import layoutparser as lp
from PyPDF2 import PdfReader
import pdf2image
import numpy as np
from PIL import Image

from src.constants.properties import IMAGE_PATH, SERVER_URL


class PyPDFExtraction(object):
    def __init__(self, pdf_path: str, model: lp.Detectron2LayoutModel = None):
        self.pdf_path = pdf_path
        self.reader = PdfReader(self.pdf_path)
        self.length = len(self.reader.pages)
        self.model = model

    def extract_text(self, page_num: int) -> str:
        page = self.reader.pages[page_num]
        return page.extract_text()

    def extract_image(self, page_num: int) ->List[str]:
        page = self.reader.pages[page_num]
        image_urls = []

        Path(IMAGE_PATH).mkdir(parents=True, exist_ok=True)
        for count, image_file_object in enumerate(page.images):
            image_id = str(uuid4())
            with open(f"{IMAGE_PATH}/{image_id}.png", "wb") as fp:
                fp.write(image_file_object.data)
            image_urls.append(f"{SERVER_URL}/{image_id}")
        return image_urls

    @staticmethod
    def crop_figures(layout: lp.Layout, image: np.ndarray):
        Path(IMAGE_PATH).mkdir(parents=True, exist_ok=True)
        figure_blocks = lp.Layout([b for b in layout if b.type == 'figure'])
        image_urls = []
        for i, figure_block in enumerate(figure_blocks):
            x1, y1, x2, y2 = int(figure_block.coordinates[0]), int(figure_block.coordinates[1]), \
                int(figure_block.coordinates[2]), int(figure_block.coordinates[3])
            image_id = str(uuid4())
            cropped_figure = image[y1:y2, x1 - 20:x2 + 20]
            cropped_img = Image.fromarray(cropped_figure)
            cropped_img.save(f'{IMAGE_PATH}/{image_id}.png')
            image_urls.append(f"{SERVER_URL}/{image_id}")
        return image_urls

    def extract_image_detectron(self, page_num: int = 0) -> lp.Layout:
        image = np.asarray(pdf2image.convert_from_path(self.pdf_path)[page_num])
        layout_result = self.model.detect(image)
        image_urls = self.crop_figures(layout_result, image)
        return image_urls

