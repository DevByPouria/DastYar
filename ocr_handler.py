import easyocr
import re
import io
from PIL import Image

# راه‌اندازی موتور OCR یکبار برای همیشه
reader = easyocr.Reader(['fa', 'en'], gpu=False)

def extract_amount_from_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        result = reader.readtext(image, detail=0)
        text = ' '.join(result)
        
        # پیدا کردن اعداد فارسی یا انگلیسی
        numbers = re.findall(r'(\d{1,3}(?:[\,\.]\d{3})*|\d+)', text)
        if numbers:
            amount = numbers[-1].replace(',', '').replace('.', '')
            return int(amount)
        return None
    except Exception as e:
        print(f"OCR Error: {e}")
        return None
