import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# هدرهای کامل برای شبیه‌سازی مرورگر واقعی جهت جلوگیری از بلاک شدن توسط ترب و باسلام
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://torob.com/'
}

def search_torob(query):
    products = []
    try:
        # ساختار جدید و معتبر API ترب
        torob_url = f"https://api.torob.com/v4/base-product/search/?page=0&size=5&q={quote(query)}"
        response = requests.get(torob_url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for item in results:
                title = item.get('name1') or item.get('name2') or 'بدون عنوان'
                price = item.get('price', 0)
                price_text = item.get('price_text', '')
                
                if price and isinstance(price, int) and price > 0:
                    price_str = f"{price:,} تومان"
                elif price_text:
                    price_str = price_text
                else:
                    price_str = "نامشخص"
                
                # استخراج کلید محصول برای ساخت لینک
                random_key = item.get('random_key', '')
                product_url = f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': product_url,
                    'source': 'ترب'
                })
        else:
            print(f"Torob Status Code: {response.status_code}")
    except Exception as e:
        print(f"Torob Search Error: {e}")
        
    return products


def search_digikala(query):
    products = []
    try:
        digi_url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        response = requests.get(digi_url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])[:5]
            
            for item in items:
                title = item.get('title_fa', '')
                price_rrp = item.get('price', {}).get('selling_price', 0)
                
                if price_rrp > 0:
                    price_str = f"{price_rrp // 10:,} تومان"
                else:
                    price_str = "ناموجود"
                
                product_id = item.get('id', '')
                product_url = f"https://www.digikala.com/product/dk-{product_id}/"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': product_url,
                    'source': 'دیجی‌کالا'
                })
    except Exception as e:
        print(f"Digikala Search Error: {e}")
        
    return products


def search_basalam(query):
    products = []
    try:
        # ساختار معتبر سرویس جستجوی باسلام
        basalam_url = f"https://search.basalam.com/ai-engine/v1/search?q={quote(query)}&from=0&size=5"
        response = requests.get(basalam_url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('products', [])[:5]
            
            for item in items:
                title = item.get('title', 'بدون عنوان')
                price_rials = item.get('price', 0)
                
                if price_rials > 0:
                    price_toman = price_rials // 10
                    price_str = f"{price_toman:,} تومان"
                else:
                    price_str = "نامشخص"
                
                vendor = item.get('vendor', {})
                vendor_id = vendor.get('identifier', '')
                product_id = item.get('id', '')
                
                if vendor_id and product_id:
                    product_url = f"https://basalam.com/{vendor_id}/product/{product_id}"
                else:
                    product_url = "https://basalam.com"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': product_url,
                    'source': 'باسلام'
                })
        else:
            print(f"Basalam Status Code: {response.status_code}")
    except Exception as e:
        print(f"Basalam Search Error: {e}")
        
    return products


def search_products(query):
    products = []
    
    # اجرای هم‌زمان با ذخیره صریح نتایج هر بخش
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_torob = executor.submit(search_torob, query)
        future_digi = executor.submit(search_digikala, query)
        future_basalam = executor.submit(search_basalam, query)
        
        # دریافت ۳ نتیجه
        torob_res = future_torob.result()
        digi_res = future_digi.result()
        basalam_res = future_basalam.result()
        
        # افزودن به صورت یکی در میان یا ترتیبی
        products.extend(torob_res)
        products.extend(digi_res)
        products.extend(basalam_res)

    return products


def format_product_message(products):
    if not products:
        return "❌ متأسفانه محصولی با این عنوان پیدا نشد."
    
    msg = "🛒 **نتایج جستجوی کالا (ترب، دیجی‌کالا، باسلام):**\n"
    msg += "───────────────────\n\n"
    
    for idx, p in enumerate(products, 1):
        if p['source'] == 'دیجی‌کالا':
            source_badge = "🔴 [دیجی‌کالا]"
        elif p['source'] == 'ترب':
            source_badge = "🟦 [ترب]"
        else:
            source_badge = "🟢 [باسلام]"
            
        msg += f"{idx}. {source_badge} **{p['title']}**\n"
        msg += f"💰 **قیمت:** {p['price']}\n"
        msg += f"🔗 [مشاهده و خرید محصول]({p['link']})\n"
        msg += "───────────────────\n"
        
    return msg
