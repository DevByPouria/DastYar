import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------
# ۱. توابع اختصاصی برای هر فروشگاه
# ---------------------------------------------------------

def search_torob(query):
    products = []
    try:
        torob_url = f"https://api.torob.com/v4/base-product/search/?page=0&size=5&q={quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(torob_url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('results', []):
                title = item.get('name1') or item.get('name2', 'بدون عنوان')
                price_text = item.get('price_text', 'نامشخص')
                price = item.get('price', 0)
                price_str = f"{price:,} تومان" if price else price_text
                
                random_key = item.get('random_key', '')
                product_url = f"https://torob.com/p/{random_key}/" if random_key else "https://torob.com"
                
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': product_url,
                    'source': 'ترب'
                })
    except Exception as e:
        print(f"Torob Search Error: {e}")
    return products


def search_digikala(query):
    products = []
    try:
        digi_url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        response = requests.get(digi_url, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])[:5]
            
            for item in items:
                title = item.get('title_fa', '')
                price_rrp = item.get('price', {}).get('selling_price', 0) // 10
                price_str = f"{price_rrp:,} تومان" if price_rrp > 0 else "ناموجود"
                
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
        basalam_url = f"https://search.basalam.com/ai-engine/v1/search?q={quote(query)}&from=0&size=5"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(basalam_url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('products', [])[:5]
            
            for item in items:
                title = item.get('title', 'بدون عنوان')
                price_rials = item.get('price', 0)
                price_toman = price_rials // 10 if price_rials else 0
                price_str = f"{price_toman:,} تومان" if price_toman > 0 else "نامشخص"
                
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
    except Exception as e:
        print(f"Basalam Search Error: {e}")
    return products


# ---------------------------------------------------------
# ۲. تابع تجمیع‌کننده هم‌زمان (Fast Parallel Search)
# ---------------------------------------------------------

def search_products(query):
    products = []
    
    # ارسال هم‌زمان درخواست‌ها جهت بالابردن سرعت پاسخ‌دهی ربات
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(search_torob, query),
            executor.submit(search_digikala, query),
            executor.submit(search_basalam, query)
        ]
        
        for future in as_completed(futures):
            try:
                res = future.result()
                products.extend(res)
            except Exception as e:
                print(f"Error gathering results: {e}")

    return products


# ---------------------------------------------------------
# ۳. قالب‌بندی پیام خروجی تلگرام
# ---------------------------------------------------------

def format_product_message(products):
    if not products:
        return "❌ متأسفانه محصولی با این عنوان در ترب، دیجی‌کالا و باسلام پیدا نشد."
    
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
