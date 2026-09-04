import os
import io
import time
import threading
import requests
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# متغیرهای حافظه موقت (Cache) برای افزایش سرعت
CACHED_PRICES = {}
LAST_FETCH_TIME = 0
CACHE_TTL = 60  # اعتبار قیمت‌ها به ثانیه (۱ دقیقه)

def get_current_time():
    tehran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(tehran_tz).strftime('%H:%M:%S')

def fetch_prices_from_api():
    """دریافت داده‌ها از شبکه (مرحله کند)"""
    prices = {
        '⚜️ Gold 18k': '23,364,421', 
        '🪙 Sekke Emami': '233,500,000', 
        '💵 USD / Tether': '221,599',
        '🔱 Mesghal 17': '101,210,000', 
        '🪙 Sekke Nim': '119,500,000', 
        '🪙 Sekke Rob': '64,500,000',
        '🌐 Ounce Gold': '4,477/60', 
        '🥈 Ounce Silver': '66/91', 
        '🪙 Sekke Ghadim': '230,500,000',
        '🥇 Parsian': '25,116,752', 
        '🧱 Shmesh': '34,933,391', 
        '📊 Sekke Value': '228,026,130',
        '₿ Bitcoin': '81,174/1', 
        '💎 Ethereum': '2506/23', 
        '🛢️ Oil': '95/70',
        '🇹🇷 Lir': '4,640', 
        '🇴🇲 OMR': '579,000', 
        '🛒 Gold Buy': '23,052,895'
    }
    
    try:
        res = requests.get("https://brsapi.ir/FreeTomanExchangeApi/Short.json", headers=HEADERS, timeout=3)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('gold', []):
                if '18' in item.get('name', ''):
                    prices['⚜️ Gold 18k'] = f"{int(item.get('price', 0)):,}"
            for item in data.get('currency', []):
                if 'دلار' in item.get('name', ''):
                    prices['💵 USD / Tether'] = f"{int(item.get('price', 0)):,}"
            for item in data.get('coin', []):
                if 'امامی' in item.get('name', ''):
                    prices['🪙 Sekke Emami'] = f"{int(item.get('price', 0)):,}"
    except Exception as e:
        print(f"Error fetching API: {e}")
        
    return prices

def get_all_prices():
    """دریافت سریع قیمت‌ها از حافظه کش بدون معطلی شبکه"""
    global CACHED_PRICES, LAST_FETCH_TIME
    now = time.time()
    
    # اگر کش خالی است یا بیشتر از ۶۰ ثانیه گذشته، بروزرسانی کن
    if not CACHED_PRICES or (now - LAST_FETCH_TIME) > CACHE_TTL:
        CACHED_PRICES = fetch_prices_from_api()
        LAST_FETCH_TIME = now
        
    return CACHED_PRICES

def generate_price_image():
    """تولید فوق‌العاده سریع تصویر"""
    prices = get_all_prices()
    
    cols, rows = 6, 3
    card_w, card_h = 180, 100
    pad_x, pad_y = 12, 12
    img_w = cols * card_w + (cols + 1) * pad_x
    img_h = rows * card_h + (rows + 1) * pad_y + 50
    
    img = Image.new('RGB', (img_w, img_h), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    font_path = os.path.join(os.path.dirname(__file__), "Vazirmatn.ttf")
    try:
        font_title = ImageFont.truetype(font_path, 16)
        font_value = ImageFont.truetype(font_path, 20)
        font_header = ImageFont.truetype(font_path, 18)
    except:
        font_title = font_value = font_header = ImageFont.load_default()

    items = list(prices.items())
    
    for idx, (title, val) in enumerate(items[:18]):
        r = idx // cols
        c = idx % cols
        
        x = c * card_w + (c + 1) * pad_x
        y = r * card_h + (r + 1) * pad_y + 45
        
        draw.rounded_rectangle([x, y, x + card_w, y + 42], radius=8, fill='#135270')
        draw.rounded_rectangle([x, y + 38, x + card_w, y + card_h], radius=8, fill='#FFFDE7', outline='#135270', width=1)
        
        bbox_t = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
        draw.text((x + (card_w - tw)/2, y + 10), title, fill='#FFFFFF', font=font_title)
        
        bbox_v = draw.textbbox((0, 0), val, font=font_value)
        vw = bbox_v[2] - bbox_v[0]
        draw.text((x + (card_w - vw)/2, y + 56), val, fill='#111111', font=font_value)

    header_text = f"⚡ LIVE MARKET - {get_current_time()} (Tehran Time) ⚡"
    bbox_h = draw.textbbox((0, 0), header_text, font=font_header)
    hw = bbox_h[2] - bbox_h[0]
    draw.text(((img_w - hw)/2, 12), header_text, fill='#135270', font=font_header)

    bio = io.BytesIO()
    bio.name = 'prices.png'
    img.save(bio, 'PNG', optimize=True)
    bio.seek(0)
    return bio
