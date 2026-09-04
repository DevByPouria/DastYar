import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8'
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
# ۲. جستجوی ترب و باسلام از طریق گوگل (جهت بای‌پاس تحریم و IP)
# ---------------------------------------------------------
def search_via_google(site_domain, query, limit=5):
    products = []
    try:
        google_url = f"https://www.google.com/search?q=site:{site_domain}+{quote(query)}"
        res = requests.get(google_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # استخراج لینک‌ها و عناوین نتایج جستجو
            results = soup.find_all('div', class_='g')
            
            for g in results:
                title_elem = g.find('h3')
                link_elem = g.find('a')
                if title_elem and link_elem:
                    href = link_elem.get('href', '')
                    if href.startswith('http'):
                        products.append({
                            'title': title_elem.text,
                            'price': 'مشاهده در سایت',
                            'link': href
                        })
                if len(products) >= limit:
                    break
    except Exception as e:
        print(f"Google Search Error for {site_domain}: {e}")
    return products

# ---------------------------------------------------------
# ۳. اجرای هم‌زمان
# ---------------------------------------------------------
def search_products(query):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_digi = executor.submit(search_digikala, query, 5)
        f_torob = executor.submit(search_via_google, "torob.com/p", query, 5)
        f_basalam = executor.submit(search_via_google, "basalam.com/product", query, 5)
        
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
