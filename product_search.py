import re
import requests
from urllib.parse import quote, unquote
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'fa,en;q=0.9'
}

# ---------------------------------------------------------
# ۱. جستجوی دیجی‌کالا (ارتباط مستقیم)
# ---------------------------------------------------------
def search_digikala(query, limit=5):
    products = []
    try:
        url = f"https://api.digikala.com/v1/search/?q={quote(query)}&page=1"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('products', [])[:limit]
            for item in items:
                title = item.get('title_fa', '')
                price_rrp = item.get('price', {}).get('selling_price', 0)
                price_str = f"{price_rrp // 10:,} تومان" if price_rrp > 0 else "ناموجود"
                p_id = item.get('id', '')
                products.append({
                    'title': title,
                    'price': price_str,
                    'link': f"https://www.digikala.com/product/dk-{p_id}/",
                    'source': 'دیجی‌کالا'
                })
    except Exception as e:
        print(f"Digikala Error: {e}")
    return products

# ---------------------------------------------------------
# ۲. جستجوی ترب (از طریق موتور میانجی جهت عبور از مسدودی سرور)
# ---------------------------------------------------------
def search_torob(query, limit=5):
    products = []
    try:
        # جستجوی مستقیم نتایج ترب در html موتور جستجو
        search_url = f"https://html.duckduckgo.com/html/?q=site:torob.com/p/+{quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if res.status_code == 200:
            # استخراج لینک‌ها و عناوین مربوط به محصولات ترب
            matches = re.findall(r'<a class="result__url" href="([^"]+)".*?>(.*?)</a>.*?<a class="result__snippet".*?>(.*?)</a>', res.text, re.DOTALL)
            
            if not matches:
                # الگوی رزرو برای استخراج لینک‌ها
                links = re.findall(r'https://torob\.com/p/[a-zA-Z0-9-]+/', res.text)
                titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', res.text)
                for i in range(min(len(links), limit)):
                    clean_title = re.sub('<[^<]+?>', '', titles[i]) if i < len(titles) else query
                    products.append({
                        'title': clean_title.strip(),
                        'price': 'مشاهده در سایت',
                        'link': links[i],
                        'source': 'ترب'
                    })
            else:
                for match in matches[:limit]:
                    raw_link = match[0]
                    title_raw = match[1]
                    clean_title = re.sub('<[^<]+?>', '', title_raw).strip()
                    
                    # استخراج لینک واقعی ترب از موتور جستجو
                    actual_link = raw_link
                    if "uddg=" in raw_link:
                        actual_link = unquote(raw_link.split("uddg=")[1].split("&")[0])
                    
                    if "torob.com/p/" in actual_link:
                        products.append({
                            'title': clean_title if clean_title else query,
                            'price': 'مشاهده در سایت',
                            'link': actual_link,
                            'source': 'ترب'
                        })
    except Exception as e:
        print(f"Torob Engine Error: {e}")
        
    return products[:limit]

# ---------------------------------------------------------
# ۳. جستجوی باسلام (از طریق موتور میانجی)
# ---------------------------------------------------------
def search_basalam(query, limit=5):
    products = []
    try:
        search_url = f"https://html.duckduckgo.com/html/?q=site:basalam.com/product/+{quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if res.status_code == 200:
            links = re.findall(r'https://basalam\.com/[^/]+/product/\d+', res.text)
            titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', res.text)
            
            # حذف موارد تکراری
            unique_links = list(dict.fromkeys(links))
            
            for i in range(min(len(unique_links), limit)):
                clean_title = re.sub('<[^<]+?>', '', titles[i]) if i < len(titles) else query
                products.append({
                    'title': clean_title.strip(),
                    'price': 'مشاهده در سایت',
                    'link': unique_links[i],
                    'source': 'باسلام'
                })
    except Exception as e:
        print(f"Basalam Engine Error: {e}")
        
    return products[:limit]

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
# ۵. ساخت پیام‌های خروجی تلگرام
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
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید در ترب]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟦 **ترب:** متأسفانه محصولی یافت نشد.")

    # پیام باسلام
    basalam_items = results_dict.get('basalam', [])
    if basalam_items:
        msg = "🟢 **نتایج جستجو در باسلام (۵ مورد برتر):**\n───────────────────\n"
        for idx, p in enumerate(basalam_items, 1):
            msg += f"{idx}. **{p['title']}**\n💰 **قیمت:** {p['price']}\n🔗 [مشاهده و خرید در باسلام]({p['link']})\n\n"
        messages.append(msg)
    else:
        messages.append("🟢 **باسلام:** متأسفانه محصولی یافت نشد.")

    return messages
