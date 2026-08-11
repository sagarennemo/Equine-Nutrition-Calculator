import pytesseract
from pytesseract import Output
import pdfplumber
import cv2
import numpy as np
import pdf2image
 
from preprocessing import process_report_image


def ocr_with_confidence(img):
    data = pytesseract.image_to_data(img, lang="swe", config="--psm 6", output_type=Output.DICT)
    words = [w for w in data['text'] if w.strip()]
    confidences = [c for w, c in zip(data['text'], data['conf']) if w.strip()]

    full_text = " ".join(words)
    if confidences: 
        avg_conf = sum(confidences) / len(confidences)
    else:
        avg_conf = 0

    return full_text, avg_conf

def handle_pdf(path):
    page_texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                lines = [
                    " ".join(str(cell) if cell else "" for cell in row)
                    for row in table
                ]
                page_texts.append("\n".join(lines))
            else:
                page_texts.append(page.extract_text() or "")
 
    text = "\n".join(page_texts)
 
    if text and len(text.strip()) > 20:
        return {'type': 'text', 'content': text}
    else:
        try:
            images = pdf2image.convert_from_path(path)
            converted = [
                cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                for img in images
            ]
            return {'type': 'images', 'content': converted}
        except Exception as e:
            raise ValueError(f"could not process PDF: {path}") from e

def load_document(path):
    if path.lower().endswith('.pdf'):
        return handle_pdf(path)
    elif path.lower().endswith(('.jpg', '.jpeg', '.png')):
        img = cv2.imread(path)
        assert img is not None, f"could not read {path}"
        return {'type': 'image', 'content': img}
    else:
        raise ValueError(f"unsupported file type: {path}")
    
    
def process_all(paths):
    results = []
 
    for path in paths:
        try:
            doc = load_document(path)
 
            if doc['type'] == 'text':
                text = doc['content']
                conf = None
 
            elif doc['type'] == 'images':
                # doc['content'] is a LIST of images (one per PDF page) —
                # accumulate results across all of them, don't overwrite
                page_results = [
                    ocr_with_confidence(process_report_image(img))
                    for img in doc['content']
                ]
                text = "\n".join(t for t, c in page_results)
                confs = [c for t, c in page_results if c is not None]
                conf = sum(confs) / len(confs) if confs else None
 
            elif doc['type'] == 'image':
                processed = process_report_image(doc['content'])
                text, conf = ocr_with_confidence(processed)
 
            results.append({
                "source_file": path,
                "text": text,
                "confidence": conf,
             })
 
        except Exception as e:
            results.append({"source_file": path, "error": str(e)})
            continue
 
    return results