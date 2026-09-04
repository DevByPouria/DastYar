import io
import requests
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_current_time():
    tehran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(tehran_tz).strftime('%H:%M:%S')

def reshape_text(text):
    """اصلاح متون فارسی برای Pillow"""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

def get_all_prices():
    prices = {
        'انس طلا': '4477/60', 'مثقال ۱۷': '101,210,000', 'گرم ۱۸': '23,364,421',
        'سکه امامی': '233,500,000', 'سکه نیم': '119,500,000', 'سکه ربع': '64,500,000',
        'نقره(اونس)': '66/91', 'شمش گرمی': '34,933,391', 'بیت کوین': '81,174/1',
        'ارزش سکه': '228,026,130', 'نفت': '95/70', 'تتر': '221,599',
        'سکه پارسیان': '25,116,752', 'سکه قدیم': '230,500,000', 'گرم خرید': '23,052,895',
        'لیر ترکیه': '4,640', 'ریال عمان': '579,000', 'اتریوم': '2506/23'
    }
    try:
        res = requests.get("https://brsapi.ir/FreeTomanExchangeApi/Short.json", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('gold', []):
                if '18' in item.get('name', ''):
                    prices['گرم ۱۸'] = f"{int(item.get('price', 0)):,}"
            for item in data.get('currency', []):
                if 'دلار' in item.get('name', ''):
                    prices['تتر'] = f"{int(item.get('price', 0)):,}"
            for item in data.get('coin', []):
                if 'امامی' in item.get('name', ''):
                    prices['سکه امامی'] = f"{int(item.get('price', 0)):,}"
    except Exception as e:
        print(f"Error fetching API: {e}")
        
    return prices

def generate_price_image():
    prices = get_all_prices()
    
    # ابعاد تصویر
    cols, rows = 6, 3
    card_w, card_h = 160, 90
    pad_x, pad_y = 10, 10
    img_w = cols * card_w + (cols + 1) * pad_x
    img_h = rows * card_h + (rows + 1) * pad_y + 40
    
    img = Image.new('RGB', (img_w, img_h), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # بارگذاری فونت (فایل Vazirmatn.ttf را کنار پروژه قرار دهید)
    try:
        font_title = ImageFont.truetype("Vazirmatn.ttf", 15)
        font_value = ImageFont.truetype("Vazirmatn.ttf", 17)
    except:
        font_title = font_value = ImageFont.load_default()

    items = list(prices.items())
    
    for idx, (title, val) in enumerate(items[:18]):
        r = idx // cols
        c = idx % cols
        
        # محاسبه موقعیت کارت (راست به چپ)
        x = img_w - ((c + 1) * card_w + (c + 1) * pad_x)
        y = r * card_h + (r + 1) * pad_y + 35
        
        # ۱. بخش بالایی (کادر سرمه‌ای)
        draw.rounded_rectangle([x, y, x + card_w, y + 40], radius=8, fill='#135270')
        # ۲. بخش پایینی (کادر کرم)
        draw.rounded_rectangle([x, y + 35, x + card_w, y + card_h], radius=8, fill='#FFFDE7', outline='#135270', width=1)
        
        # متن عنوان
        t_text = reshape_text(title)
        bbox_t = draw.textbbox((0, 0), t_text, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
        draw.text((x + (card_w - tw)/2, y + 8), t_text, fill='#FFFFFF', font=font_title)
        
        # متن مقدار
        v_text = reshape_text(val)
        bbox_v = draw.textbbox((0, 0), v_text, font=font_value)
        vw = bbox_v[2] - bbox_v[0]
        draw.text((x + (card_w - vw)/2, y + 50), v_text, fill='#111111', font=font_value)

    # عنوان بالای تصویر
    header_text = reshape_text(f"💎 تابلو قیمت‌های لحظه‌ای بازار - {get_current_time()}")
    bbox_h = draw.textbbox((0, 0), header_text, font=font_title)
    hw = bbox_h[2] - bbox_h[0]
    draw.text(((img_w - hw)/2, 8), header_text, fill='#135270', font=font_title)

    # ذخیره تصویر در حافظه RAM
    bio = io.BytesIO()
    bio.name = 'prices.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
