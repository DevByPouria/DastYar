import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# ۱. جستجو در ترب (Torob)
# ---------------------------------------------------------
def search_torob(query, limit=5):
    products = []
    try:
        # ایجاد Session جهت حفظ هدرها و کوکی‌ها
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://torob.com',
            'Referer': f'https://torob.com/search/?query={quote(query)}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })
        
        # Endpoint دقیق API ترب
        url = f"https://api.torob.com/v4/base-product/search/?page=0&size={limit}&query={quote(query)}"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])[:limit]
            
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
                
                random_key = item.get('random_key', '')
                product_url = f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': product_url,
                    'source': 'ترب'
                })
        else:
            print(f"Torob HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Torob Search Error: {e}")
        
    return products


# ---------------------------------------------------------
# ۲. جستجو در دیجی‌کالا (Digikala)
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])[:limit]
            
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


# ---------------------------------------------------------
# ۳. جستجو در باسلام (Basalam)
# ---------------------------------------------------------
def search_basalam(query, limit=5):
    products = []
    try:
        # Endpoint جدید وب‌سایت باسلام
        url = "https://search.basalam.com/ai-engine/v1/search"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://basalam.com/'
        }
        params = {
            'q': query,
            'from': 0,
            'size': limit
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('products', [])[:limit]
            
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
            print(f"Basalam HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Basalam Search Error: {e}")
        
    return products


# ---------------------------------------------------------
# ۴. فراخوانی هم‌زمان منابع
# ---------------------------------------------------------
def search_products(query):
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_digi = executor.submit(search_digikala, query, 5)
        future_torob = executor.submit(search_torob, query, 5)
        future_basalam = executor.submit(search_basalam, query, 5)
        
        digi_res = future_digi.result()
        torob_res = future_torob.result()
        basalam_res = future_basalam.result()
        
    return {
        'digi': digi_res,
        'torob': torob_res,
        'basalam': basalam_res
    }


# ---------------------------------------------------------
# ۵. ساخت پیام‌های تفکیک‌شده برای تلگرام
# ---------------------------------------------------------
def format_product_messages(results_dict):
    messages = []
    
    # پیام دیجی‌کالا
    digi_items = results_dict.get('digi', [])
    if digi_items:
        msg = "🔴 **نتایج جستجو در دیجی‌کالا (۵ مورد برتر):**\n───────────────────\n"
        for idx, p in enumerate(digi_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🔴 **دیجی‌کالا:** متأسفانه محصولی یافت نشد.")

    # پیام ترب
    torob_items = results_dict.get('torob', [])
    if torob_items:
        msg = "🟦 **نتایج جستجو در ترب (۵ مورد برتر):**\n───────────────────\n"
        for idx, p in enumerate(torob_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟦 **ترب:** متأسفانه محصولی یافت نشد.")

    # پیام باسلام
    basalam_items = results_dict.get('basalam', [])
    if basalam_items:
        msg = "🟢 **نتایج جستجو در باسلام (۵ مورد برتر):**\n───────────────────\n"
        for idx, p in enumerate(basalam_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟢 **باسلام:** متأسفانه محصولی یافت نشد.")

    return messages
