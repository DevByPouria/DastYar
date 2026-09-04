import os
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
    """اصلاح متون فارسی و راست‌به‌چپ‌سازی دقیق"""
    if not text:
        return ""
    # اتصال حروف فارسی
    reshaped_text = arabic_reshaper.reshape(str(text))
    # مرتب‌سازی اتصالات از راست به چپ
    bidi_text = get_display(reshaped_text)
    return bidi_text

def generate_price_image():
    prices = get_all_prices()
    
    # تنظیم ابعاد کادرها
    cols, rows = 6, 3
    card_w, card_h = 160, 90
    pad_x, pad_y = 10, 10
    img_w = cols * card_w + (cols + 1) * pad_x
    img_h = rows * card_h + (rows + 1) * pad_y + 40
    
    img = Image.new('RGB', (img_w, img_h), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # بارگذاری فونت با مسیر مطلق
    font_path = os.path.join(os.path.dirname(__file__), "Vazirmatn.ttf")
    try:
        font_title = ImageFont.truetype(font_path, 15)
        font_value = ImageFont.truetype(font_path, 16)
    except Exception as e:
        print(f"Font loading error: {e}")
        # فونت جایگزین ساده
        font_title = font_value = ImageFont.load_default()

    items = list(prices.items())
    
    for idx, (title, val) in enumerate(items[:18]):
        r = idx // cols
        c = idx % cols
        
        # محاسبه موقعیت خانه از چپ به راست (ترتیب داده‌ها درست جای‌گذاری می‌شود)
        x = c * card_w + (c + 1) * pad_x
        y = r * card_h + (r + 1) * pad_y + 35
        
        # ۱. کادر بالا (سرمه‌ای)
        draw.rounded_rectangle([x, y, x + card_w, y + 40], radius=6, fill='#135270')
        # ۲. کادر پایین (کرم)
        draw.rounded_rectangle([x, y + 35, x + card_w, y + card_h], radius=6, fill='#FFFDE7', outline='#135270', width=1)
        
        # متن عنوان
        t_text = reshape_text(title)
        bbox_t = draw.textbbox((0, 0), t_text, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
        draw.text((x + (card_w - tw)/2, y + 8), t_text, fill='#FFFFFF', font=font_title)
        
        # متن قیمت
        v_text = reshape_text(val)
        bbox_v = draw.textbbox((0, 0), v_text, font=font_value)
        vw = bbox_v[2] - bbox_v[0]
        draw.text((x + (card_w - vw)/2, y + 50), v_text, fill='#111111', font=font_value)

    # عنوان بالای تصویر
    header_raw = f"تابلو قیمت‌های لحظه‌ای بازار - {get_current_time()}"
    header_text = reshape_text(header_raw)
    bbox_h = draw.textbbox((0, 0), header_text, font=font_title)
    hw = bbox_h[2] - bbox_h[0]
    draw.text(((img_w - hw)/2, 8), header_text, fill='#135270', font=font_title)

    bio = io.BytesIO()
    bio.name = 'prices.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
