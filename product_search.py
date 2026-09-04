import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def search_products(query):
    products = []
    
    # ۱. جستجو در دیجی‌کالا (مناسب برای سرورهای خارج از کشور)
    try:
        url_dk = f"https://api.digikala.com/v1/search/?q={query}"
        res = requests.get(url_dk, headers=HEADERS, timeout=7)
        if res.status_code == 200:
            data = res.json()
            items = data.get('data', {}).get('products', [])
            for item in items[:5]:
                title = item.get('title_fa')
                price_data = item.get('price', {})
                price_toman = int(price_data.get('selling_price', 0) / 10) if price_data.get('selling_price') else 0
                uri = item.get('url', {}).get('uri', '')
                product_url = f"https://www.digikala.com{uri}" if uri else "https://www.digikala.com"
                
                if title:
                    products.append({
                        'title': title,
                        'price': price_toman,
                        'link': product_url,
                        'source': 'دیجی‌کالا'
                    })
            if products:
                return products
    except Exception as e:
        print(f"Digikala Search Error: {e}")

    # ۲. فال‌بک به ترب
    try:
        url_torob = f"https://api.torob.com/v4/base-product/search/?page=0&size=5&query={query}"
        res = requests.get(url_torob, headers=HEADERS, timeout=7)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('results', []):
                title = item.get('name1') or item.get('name2')
                price = item.get('price', 0)
                web_url = item.get('web_client_absolute_url', '')
                product_url = f"https://torob.com{web_url}" if web_url else "https://torob.com"
                
                if title:
                    products.append({
                        'title': title,
                        'price': price,
                        'link': product_url,
                        'source': 'ترب'
                    })
    except Exception as e:
        print(f"Torob Search Error: {e}")

    return products


def format_product_message(products):
    if not products:
        return "❌ محصولی یافت نشد یا درگاه ارتباطی فروشگاه‌ها پاسخ نداد."
        
    msg = f"🛍️ **نتایج یافت‌شده (منبع: {products[0]['source']}):**\n\n"
    for idx, item in enumerate(products, 1):
        price_str = f"{item['price']:,} تومان" if item['price'] > 0 else "نامشخص / استعلام قیمت"
        msg += f"{idx}. [{item['title']}]({item['link']})\n💰 **قیمت:** `{price_str}`\n───────────────\n"
        
    return msg