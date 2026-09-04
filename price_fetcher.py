import io
import requests
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_current_time():
    """محاسبه ساعت دقیق تهران"""
    tehran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(tehran_tz).strftime('%H:%M:%S')

def get_all_prices():
    """دریافت قیمت‌ها و اختصاص آیکون/فینگلیش به هر کدام"""
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
        res = requests.get("https://brsapi.ir/FreeTomanExchangeApi/Short.json", headers=HEADERS, timeout=8)
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

def generate_price_image():
    """تولید تصویر گرافیکی کارت‌ها"""
    prices = get_all_prices()
    
    # تنظیم ابعاد شبکه ۶ در ۳
    cols, rows = 6, 3
    card_w, card_h = 160, 90
    pad_x, pad_y = 10, 10
    img_w = cols * card_w + (cols + 1) * pad_x
    img_h = rows * card_h + (rows + 1) * pad_y + 45
    
    img = Image.new('RGB', (img_w, img_h), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    font_title = font_value = ImageFont.load_default()

    items = list(prices.items())
    
    for idx, (title, val) in enumerate(items[:18]):
        r = idx // cols
        c = idx % cols
        
        x = c * card_w + (c + 1) * pad_x
        y = r * card_h + (r + 1) * pad_y + 40
        
        # ۱. کادر عنوان (سرمه‌ای)
        draw.rounded_rectangle([x, y, x + card_w, y + 38], radius=6, fill='#135270')
        # ۲. کادر قیمت (کرم)
        draw.rounded_rectangle([x, y + 34, x + card_w, y + card_h], radius=6, fill='#FFFDE7', outline='#135270', width=1)
        
        # محاسبه مرکز متن عنوان
        bbox_t = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox_t[2] - bbox_t[0]
        draw.text((x + (card_w - tw)/2, y + 12), title, fill='#FFFFFF', font=font_title)
        
        # محاسبه مرکز متن مقدار
        bbox_v = draw.textbbox((0, 0), val, font=font_value)
        vw = bbox_v[2] - bbox_v[0]
        draw.text((x + (card_w - vw)/2, y + 54), val, fill='#111111', font=font_value)

    # هدر بالای عکس
    header_text = f"⚡ LIVE MARKET - {get_current_time()} (Tehran Time) ⚡"
    bbox_h = draw.textbbox((0, 0), header_text, font=font_title)
    hw = bbox_h[2] - bbox_h[0]
    draw.text(((img_w - hw)/2, 12), header_text, fill='#135270', font=font_title)

    bio = io.BytesIO()
    bio.name = 'prices.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio
