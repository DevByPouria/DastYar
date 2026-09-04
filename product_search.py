import requests
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

PERSIAN_NUMBER_MAP = {
    'سون': '7', 'ایت': '8', 'ناین': '9', 'تن': '10',
    'ایکس': 'x', 'پلاس': 'plus', 'پرومکس': 'pro max', 'پرو': 'pro',
    'سیزده': '13', 'چهارده': '14', 'پانزده': '15', 'شانزده': '16'
}

def normalize_query(query):
    q = query.lower()
    for fa, en in PERSIAN_NUMBER_MAP.items():
        q = q.replace(fa, en)
    return q

def search_all_shops(query):
    products = []
    normalized_q = normalize_query(query)
    
    try:
        url = f"https://api.torob.com/v4/base-product/search/?q={quote(normalized_q)}&page=0&size=5"
        response = requests.get(url, headers=HEADERS, timeout=6)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            
            for item in results:
                title = item.get('name1', 'بدون عنوان')
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
    except Exception as e:
        print(f"Error Search: {e}")
        
    return products

def format_product_message(products):
    if not products:
        return "❌ متأسفانه محصول مرتبطی یافت نشد.\nلطفاً نام محصول را دقیق‌تر وارد کنید (مثلاً: آیفون 7 پلاس)."
    
    message = "🔍 **نتایج یافت‌شده در فروشگاه‌ها:**\n\n"
    for idx, p in enumerate(products, 1):
        message += f"{idx}. **[{p['title']}]({p['link']})**\n"
        message += f"💰 قیمت: `{p['price_text']}`\n"
        message += f"🏪 منبع: {p['shop']}\n"
        message += "───────────────\n"
        
    return message
