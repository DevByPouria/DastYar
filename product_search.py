import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept-Language': 'fa-IR,fa;q=0.9'
}

# ---------------------------------------------------------
# ۱. جستجو در دیجی‌کالا (مستقیم)
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('products', [])[:limit]
            for item in items:
                price_rrp = item.get('price', {}).get('selling_price', 0)
                price_str = f"{price_rrp // 10:,} تومان" if price_rrp > 0 else "ناموجود"
                products.append({
                    'title': item.get('title_fa', ''),
                    'price': price_str,
                    'link': f"https://www.digikala.com/product/dk-{item.get('id', '')}/"
                })
    except Exception as e:
        print(f"Digikala Error: {e}")
    return products

# ---------------------------------------------------------
# ۲. جستجوی ترب و باسلام از طریق DuckDuckGo
# ---------------------------------------------------------
def search_via_ddg(site_domain, query, limit=5):
    products = []
    try:
        # جستجو به فرمت: site:torob.com/p موبایل سامسونگ
        search_query = f"site:{site_domain} {query}"
        
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=limit)
            
            for r in results:
                # داک‌داک‌گو عنوان و لینک را برمی‌گرداند
                title = r.get('title', 'بدون عنوان')
                link = r.get('href', '')
                
                # حذف کلمات اضافی از عنوان مثل "خرید و قیمت..."
                title = title.replace('خرید و قیمت', '').replace('- ترب', '').replace('باسلام', '').strip()
                
                products.append({
                    'title': title,
                    'price': 'مشاهده در سایت',
                    'link': link
                })
    except Exception as e:
        print(f"DDG Search Error for {site_domain}: {e}")
        
    return products

# ---------------------------------------------------------
# ۳. اجرای هم‌زمان
# ---------------------------------------------------------
def search_products(query):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_digi = executor.submit(search_digikala, query, 5)
        # برای ترب فقط لینک‌های محصول (p) را می‌خواهیم
        f_torob = executor.submit(search_via_ddg, "torob.com/p", query, 5)
        # برای باسلام فقط لینک‌های محصول را می‌خواهیم
        f_basalam = executor.submit(search_via_ddg, "basalam.com/product", query, 5)
        
    return {
        'digi': f_digi.result(),
        'torob': f_torob.result(),
        'basalam': f_basalam.result()
    }

# ---------------------------------------------------------
# ۴. ساخت فرمت پیام‌ها
# ---------------------------------------------------------
def format_product_messages(results_dict):
    messages = []
    
    # دیجی‌کالا
    digi_items = results_dict.get('digi', [])
    if digi_items:
        msg = "🔴 **نتایج جستجو در دیجی‌کالا:**\n───────────────────\n"
        for idx, p in enumerate(digi_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🔴 **دیجی‌کالا:** متأسفانه محصولی یافت نشد.")

    # ترب
    torob_items = results_dict.get('torob', [])
    if torob_items:
        msg = "🟦 **نتایج جستجو در ترب:**\n───────────────────\n"
        for idx, p in enumerate(torob_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟦 **ترب:** متأسفانه محصولی یافت نشد.")

    # باسلام
    basalam_items = results_dict.get('basalam', [])
    if basalam_items:
        msg = "🟢 **نتایج جستجو در باسلام:**\n───────────────────\n"
        for idx, p in enumerate(basalam_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟢 **باسلام:** متأسفانه محصولی یافت نشد.")

    return messages
