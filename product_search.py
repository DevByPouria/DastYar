import random
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------
# لیست پراکسی‌های استخراج‌شده از متنی که فرستادید
# ---------------------------------------------------------
PROXIES_LIST = [
    "http://45.131.4.93:80",
    "http://45.131.4.227:80",
    "http://45.131.4.115:80",
    "http://45.131.4.91:80",
    "http://45.131.4.34:80",
    "http://45.131.4.47:80",
    "http://45.131.4.154:80",
    "http://45.131.4.219:80",
    "http://45.131.4.16:80",
    "http://45.131.4.176:80",
    "http://45.131.4.190:80",
    "http://45.131.4.232:80",
    "http://45.131.4.168:80",
    "http://45.131.4.131:80",
    "http://45.131.4.221:80",
    "http://45.131.4.204:80",
    "http://45.131.4.186:80",
    "http://45.131.4.97:80",
    "http://45.131.4.181:80",
    "http://45.131.4.166:80"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'fa-IR,fa;q=0.9'
}

def get_random_proxy():
    proxy_url = random.choice(PROXIES_LIST)
    return {"http": proxy_url, "https": proxy_url}

# ---------------------------------------------------------
# ۱. جستجو در دیجی‌کالا (بدون نیاز به پراکسی)
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        response = requests.get(url, headers=HEADERS, timeout=8)
        
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
        print(f"Digikala Search Error: {e}")
        
    return products

# ---------------------------------------------------------
# ۲. جستجو در ترب (با چرخش روی لیست پراکسی‌ها)
# ---------------------------------------------------------
def search_torob(query, limit=5):
    products = []
    url = f"https://api.torob.com/v4/base-product/search/?sort=buy_box_price&page=0&size={limit}&q={quote(query)}"
    
    # ۳ بار تلاش با پراکسی‌های مختلف در صورت بروز خطا
    for _ in range(3):
        try:
            proxies = get_random_proxy()
            response = requests.get(url, headers=HEADERS, proxies=proxies, timeout=5)
            
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
                break # در صورت موفقیت از حلقه خارج می‌شود
        except Exception as e:
            print(f"Torob Proxy Error: {e}")
            continue
            
    return products

# ---------------------------------------------------------
# ۳. جستجو در باسلام (با چرخش روی لیست پراکسی‌ها)
# ---------------------------------------------------------
def search_basalam(query, limit=5):
    products = []
    url = f"https://search.basalam.com/ai-engine/v1/search?q={quote(query)}&from=0&size={limit}"
    
    # ۳ بار تلاش با پراکسی‌های مختلف در صورت بروز خطا
    for _ in range(3):
        try:
            proxies = get_random_proxy()
            response = requests.get(url, headers=HEADERS, proxies=proxies, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('products', [])[:limit]
                
                for item in items:
                    title = item.get('title', 'بدون عنوان')
                    price_rials = item.get('price', 0)
                    price_str = f"{price_rials // 10:,} تومان" if price_rials > 0 else "نامشخص"
                    
                    vendor = item.get('vendor', {})
                    vendor_id = vendor.get('identifier', '')
                    product_id = item.get('id', '')
                    product_url = f"https://basalam.com/{vendor_id}/product/{product_id}" if vendor_id and product_id else "https://basalam.com"
                    
                    products.append({
                        'title': title,
                        'price': price_str,
                        'link': product_url,
                        'source': 'باسلام'
                    })
                break # در صورت موفقیت از حلقه خارج می‌شود
        except Exception as e:
            print(f"Basalam Proxy Error: {e}")
            continue
            
    return products

# ---------------------------------------------------------
# ۴. فراخوانی هم‌زمان
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
