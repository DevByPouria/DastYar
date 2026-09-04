import requests

def search_products(query):
    products = []
    
    # ---------------------------------------------------------
    # ۱. جستجو در ترب (Torob)
    # ---------------------------------------------------------
    try:
        torob_url = f"https://api.torob.com/v4/base-product/search/?page=0&size=5&query={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(torob_url, headers=headers, timeout=7)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('results', []):
                title = item.get('name1', 'بدون عنوان')
                price_text = item.get('price_text', 'نامشخص')
                # اگر قیمت به صورت عدد باشد
                price = item.get('price', 0)
                price_str = f"{price:,} تومان" if price else price_text
                
                # ساخت لینک محصول در ترب
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

    # ---------------------------------------------------------
    # ۲. جستجو در دیجی‌کالا (Digikala)
    # ---------------------------------------------------------
    try:
        digi_url = f"https://api.digikala.com/v1/search/?q={query}&page=1"
        response = requests.get(digi_url, timeout=7)
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


def format_product_message(products):
    if not products:
        return "❌ متأسفانه محصولی با این عنوان در ترب و دیجی‌کالا پیدا نشد."
    
    msg = "🛒 **نتایج جستجوی کالا (ترب و دیجی‌کالا):**\n"
    msg += "───────────────────\n\n"
    
    for idx, p in enumerate(products, 1):
        source_badge = "🔴 [دیجی‌کالا]" if p['source'] == 'دیجی‌کالا' else "🟦 [ترب]"
        msg += f"{idx}. {source_badge} **{p['title']}**\n"
        msg += f"💰 **قیمت:** {p['price']}\n"
        msg += f"🔗 [مشاهده و خرید محصول]({p['link']})\n"
        msg += "───────────────────\n"
        
    return msg
