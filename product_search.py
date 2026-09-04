import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# ۱. جستجو در دیجی‌کالا
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=8)
        
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
# ۲. جستجو در ترب (روش شبیه‌سازی اپلیکیشن جهت عبور از مسدودی IP)
# ---------------------------------------------------------
def search_torob(query, limit=5):
    products = []
    try:
        # استفاده از API ساختار موبایل ترب
        url = f"https://api.torob.com/v4/base-product/search/?sort=buy_box_price&page=0&size={limit}&q={quote(query)}"
        
        # هدرهای کاملاً شبیه‌سازی شده اندروید
        headers = {
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive'
        }
        
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])[:limit]
            
            for item in results:
                title = item.get('name1') or item.get('name2') or 'بدون عنوان'
                price_text = item.get('price_text') or f"{item.get('price', 0):,} تومان"
                random_key = item.get('random_key', '')
                
                products.append({
                    'title': title,
                    'price': price_text if price_text != '0 تومان' else 'نامشخص',
                    'link': f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com",
                    'source': 'ترب'
                })
    except Exception as e:
        print(f"Torob Error: {e}")
    return products

# ---------------------------------------------------------
# ۳. جستجو در باسلام (سرویس موتور جستجوی باسلام)
# ---------------------------------------------------------
def search_basalam(query, limit=5):
    products = []
    try:
        url = "https://search.basalam.com/ai-engine/v1/search"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'application/json'
        }
        params = {'q': query, 'from': 0, 'size': limit}
        
        response = requests.get(url, headers=headers, params=params, timeout=8)
        
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
    except Exception as e:
        print(f"Basalam Error: {e}")
    return products

# ---------------------------------------------------------
# ۴. مدیریت دریافت هم‌زمان
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
# ۵. قالب‌بندی پیام‌های خروجی
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
