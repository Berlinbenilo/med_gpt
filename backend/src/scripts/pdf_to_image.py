import os
import uuid

import PyPDF2
from pdf2image import convert_from_path

from backend.src.entities.db_model import ImageIngestion
import pandas as pd


def _pdf_to_image(pdf_path, output_folder="data/images", dpi=200, file_id=None, file_name=None, batch_size=100):
    os.makedirs(output_folder, exist_ok=True)

    # store data in pdfReader
    pdfReader = PyPDF2.PdfReader(pdf_path)
    total_pages = len(pdfReader.pages)
    print("total pages:", total_pages)

    for start_page in range(1, total_pages + 1, batch_size):
        end_page = min(start_page + batch_size - 1, total_pages)
        batch_pages = convert_from_path(
            pdf_path,
            dpi=dpi,
            poppler_path=r"C:\poppler-24.08.0\Library\bin",
            first_page=start_page,
            last_page=end_page
        )
        print(f"Converting pages {start_page} to {end_page}...")

        for i, page in enumerate(batch_pages, start=start_page):
            image_id = f"{file_id}_page_{i}"
            image_path = os.path.join(output_folder, f"{image_id}.jpg")
            page.save(image_path, "JPEG")
            ImageIngestion.insert({
                "file_id": file_id,
                "image_id": image_id,
                "file_name": f"{file_name}.pdf",
            }).execute()


def main():
    notes = pd.read_csv("medgpt.csv")['filelist'].tolist()
    output_path = r"C:\Users\Deepika Ramesh\Downloads\medical_data\data\images"
    for note in notes:
        if note:
            file_name = note.strip()
            file_id = str(uuid.uuid4())
            pdf_path = fr"C:\Users\Deepika Ramesh\Downloads\medical_data\pdfs\{file_name}.pdf"
            _pdf_to_image(pdf_path, output_folder=output_path, file_id=file_id, file_name=file_name)
            print(f"Processed {file_name} with ID {file_id}")


if __name__ == "__main__":
    main()
