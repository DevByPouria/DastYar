import requests
import re
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# جایگزینی کلمات تلفظی با اعداد و کلمات استاندارد
PERSIAN_NUMBER_MAP = {
    'سون': '7', 'ایت': '8', 'ناین': '9', 'تن': '10',
    'ایکس': 'x', 'پلاس': 'plus', 'پرومکس': 'pro max', 'پرو': 'pro',
    'سیزده': '13', 'چهارده': '14', 'پانزده': '15', 'شانزده': '16'
}

ACCESSORY_KEYWORDS = [
    'قاب', 'کاور', 'گلس', 'محافظ', 'کیف', 'برچسب', 'پایه نگه‌دارنده', 
    'هولدر', 'شارژر', 'کابل', 'بند', 'گارد', 'محافظ صفحه', 'باتری'
]

def normalize_query(query):
    """استانداردسازی عبارت جستجو (تبدیل سون به 7 و ...)"""
    q = query.lower()
    for fa, en in PERSIAN_NUMBER_MAP.items():
        q = q.replace(fa, en)
    return q

def is_relevant(title, query_tokens):
    """بررسی انطباق دقیق محصول با عبارت درخواستی کاربر"""
    title_lower = title.lower()
    # اگر کلماتی مثل 7 یا plus یا iphone در جستجو بوده، باید حتماً در عنوان هم باشند
    for token in query_tokens:
        if len(token) > 1 and token not in ['گوشی', 'موبایل', 'سامسونگ', 'اپل']:
            if token not in title_lower:
                return False
    return True

def search_torob(query):
    products = []
    normalized_q = normalize_query(query)
    query_tokens = [t for t in re.split(r'\s+', normalized_q) if t]
    
    try:
        url = f"https://api.torob.com/v4/base-product/search/?q={quote(normalized_q)}&page=0&size=20"
        response = requests.get(url, headers=HEADERS, timeout=6)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            
            for item in results:
                title = item.get('name1', '')
                title_lower = title.lower()
                
                # ۱. فیلتر حذف لوازم جانبی
                is_acc_search = any(acc in query for acc in ['قاب', 'کاور', 'گلس', 'شارژر', 'کابل'])
                if not is_acc_search and any(acc in title_lower for acc in ACCESSORY_KEYWORDS):
                    continue
                
                # ۲. فیلتر انطباق دقیق (حذف گوشی‌های غیرمرتبط)
                if not is_relevant(title, query_tokens):
                    continue
                
                price_str = item.get('price_text', 'نامشخص')
                price = item.get('price', 0)
                random_key = item.get('random_key', '')
                product_url = f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com"
                
                products.append({
                    'title': title,
                    'price': price,
                    'price_text': price_str,
                    'shop': 'ترب (چندین فروشگاه)',
                    'link': product_url
                })
                
                if len(products) >= 5:
                    break
    except Exception as e:
        print(f"Error Torob: {e}")
        
    return products

def search_all_shops(query):
    return search_torob(query)

def format_product_message(products):
    if not products:
        return "❌ متأسفانه محصول مرتبطی یافت نشد.\nلطفاً نام محصول را دقیق‌تر وارد کنید (مثلاً: آیفون 7 پلاس)."
    
    message = "🔍 **نتایج یافت‌شده در صدها فروشگاه:**\n\n"
    for idx, p in enumerate(products, 1):
        message += f"{idx}. **[{p['title']}]({p['link']})**\n"
        message += f"💰 قیمت: `{p['price_text']}`\n"
        message += f"🏪 منبع: {p['shop']}\n"
        message += "───────────────\n"
        
    return message
