import requests
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# کلماتی که اگر در عنوان محصول باشند و کاربر دنبال آنها نباشد، نادیده گرفته می‌شوند
ACCESSORY_KEYWORDS = [
    'قاب', 'کاور', 'گلس', 'محافظ', 'کیف', 'برچسب', 'پایه نگه‌دارنده', 
    'هولدر', 'شارژر', 'کابل', 'بند', 'گارد', 'محافظ صفحه'
]

def search_torob(query):
    """جستجو در موتور ترب (پوشش صدها فروشگاه آنلاین ایران)"""
    products = []
    try:
        url = f"https://api.torob.com/v4/base-product/search/?q={quote(query)}&page=0&size=10"
        response = requests.get(url, headers=HEADERS, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for item in results:
                title = item.get('name1', '')
                
                # فیلتر هوشمند: اگر کاربر عبارت "قاب" یا "کاور" را سرچ نکرده، لوازم جانبی را حذف کن
                is_accessory_search = any(acc in query for acc in ['قاب', 'کاور', 'گلس', 'کیف', 'شارژر', 'کابل', 'هولدر'])
                if not is_accessory_search:
                    if any(acc in title for acc in ACCESSORY_KEYWORDS):
                        continue # اسکیپ کردن لوازم جانبی
                
                price_str = item.get('price_text', 'نامشخص')
                price = item.get('price', 0)
                random_key = item.get('random_key', '')
                
                # ساخت لینک مستقیم محصول در ترب
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
        print(f"Error searching Torob: {e}")
        
    return products

def search_digikala(query):
    """جستجو در دیجی‌کالا با فیلتر هوشمند لوازم جانبی"""
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}"
        response = requests.get(url, headers=HEADERS, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])
            
            for item in items:
                title = item.get('title_fa', '')
                
                # فیلتر لوازم جانبی
                is_accessory_search = any(acc in query for acc in ['قاب', 'کاور', 'گلس', 'کیف', 'شارژر', 'کابل'])
                if not is_accessory_search:
                    if any(acc in title for acc in ACCESSORY_KEYWORDS):
                        continue
                
                price_data = item.get('default_variant', {}).get('price', {})
                price = price_data.get('selling_price', 0) // 10  # ریال به تومان
                
                dk_id = item.get('id')
                product_url = f"https://www.digikala.com/product/dk-{dk_id}/"
                
                products.append({
                    'title': title,
                    'price': price,
                    'price_text': f"{price:,} تومان" if price > 0 else "ناموجود",
                    'shop': 'دیجی‌کالا',
                    'link': product_url
                })
                
                if len(products) >= 3:
                    break
    except Exception as e:
        print(f"Error searching Digikala: {e}")
        
    return products

def search_all_shops(query):
    """ترکیب و اولویت‌بندی نتایج از تمامی منابع (ترب + دیجی‌کالا)"""
    # اولویت اول: ترب (زیرا شامل صدها فروشگاه است)
    results = search_torob(query)
    
    # اگر ترب نتیجه‌ای نداشت یا نتایج کم بود، دیجی‌کالا اضافه می‌شود
    if len(results) < 3:
        dk_results = search_digikala(query)
        results.extend(dk_results)
        
    return results

def format_product_message(products):
    """قالب‌بندی شکیل و هوشمند پیام نتایج"""
    if not products:
        return "❌ متأسفانه محصولی یافت نشد.\nلطفاً نام محصول را دقیق‌تر یا به همراه برند وارد کنید."
    
    message = "🔍 **نتایج یافت‌شده در صدها فروشگاه:**\n\n"
    
    for idx, p in enumerate(products, 1):
        title = p['title']
        price = p['price_text']
        shop = p['shop']
        link = p['link']
        
        message += f"{idx}. **[{title}]({link})**\n"
        message += f"💰 قیمت: `{price}`\n"
        message += f"🏪 منبع: {shop}\n"
        message += "───────────────\n"
        
    return message
