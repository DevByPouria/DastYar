import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as curl_requests

# ---------------------------------------------------------
# ۱. جستجو در دیجی‌کالا
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        response = curl_requests.get(url, impersonate="chrome110", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])[:limit]
            
            for item in items:
                title = item.get('title_fa', '')
                price_rrp = item.get('price', {}).get('selling_price', 0)
                price_str = f"{price_rrp // 10:,} تومان" if price_rrp > 0 else "ناموجود"
                product_id = item.get('id', '')
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': f"https://www.digikala.com/product/dk-{product_id}/",
                    'source': 'دیجی‌کالا'
                })
    except Exception as e:
        print(f"Digikala Error: {e}")
    return products

# ---------------------------------------------------------
# ۲. جستجو در ترب (با شبیه‌سازی مرورگر واقعی Chrome)
# ---------------------------------------------------------
def search_torob(query, limit=5):
    products = []
    try:
        url = f"https://api.torob.com/v4/base-product/search/?sort=buy_box_price&page=0&size={limit}&q={quote(query)}"
        
        # impersonate="chrome110" اثرانگشت مرورگر کروم واقعی را ایجاد می‌کند
        response = curl_requests.get(url, impersonate="chrome110", timeout=10)
        
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
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com",
                    'source': 'ترب'
                })
        else:
            print(f"Torob HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"Torob Error: {e}")
    return products

# ---------------------------------------------------------
# ۳. جستجو در باسلام (با شبیه‌سازی مرورگر واقعی Chrome)
# ---------------------------------------------------------
def search_basalam(query, limit=5):
    products = []
    try:
        url = f"https://search.basalam.com/ai-engine/v1/search?q={quote(query)}&from=0&size={limit}"
        response = curl_requests.get(url, impersonate="chrome110", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('products', [])[:limit]
            
            for item in items:
                title = item.get('title', 'بدون عنوان')
                price_rials = item.get('price', 0)
                price_str = f"{price_rials // 10:,} تومان" if price_rials > 0 else "نامشخص"
                
                vendor_id = item.get('vendor', {}).get('identifier', '')
                product_id = item.get('id', '')
                link = f"https://basalam.com/{vendor_id}/product/{product_id}" if vendor_id and product_id else "https://basalam.com"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': link,
                    'source': 'باسلام'
                })
        else:
            print(f"Basalam HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"Basalam Error: {e}")
    return products

# ---------------------------------------------------------
# ۴. فراخوانی هم‌زمان
# ---------------------------------------------------------
def search_products(query):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_digi = executor.submit(search_digikala, query, 5)
        f_torob = executor.submit(search_torob, query, 5)
        f_basalam = executor.submit(search_basalam, query, 5)
        
        digi_res = f_digi.result()
        torob_res = f_torob.result()
        basalam_res = f_basalam.result()
        
    return {
        'digi': digi_res,
        'torob': torob_res,
        'basalam': basalam_res
    }

# ---------------------------------------------------------
# ۵. ساخت پیام‌های خروجی
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
