import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def search_digikala(query):
    """جستجوی مستقیم در دیجی‌کالا (بدون بلاکی آی‌پی‌های خارج از کشور)"""
    url = f"https://api.digikala.com/v1/search/?q={query}"
    products = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=7)
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])
            
            for item in items[:7]:
                title = item.get('title_fa')
                price_data = item.get('price', {})
                # قیمت به ریال است، به تومان تبدیل می‌کنیم
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
    except Exception as e:
        print(f"Digikala Search Error: {e}")
        
    return products


def search_torob(query):
    """جستجو در ترب"""
    url = "https://api.torob.com/v4/base-product/search/"
    params = {'page': 0, 'size': 7, 'query': query}
    products = []
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=7)
        if response.status_code == 200:
            data = response.json()
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


def search_all_shops(query):
    # اول از دیجی‌کالا می‌گیره (چون روی Render بلاک نمیشه)
    products = search_digikala(query)
    
    # اگر دیجی‌کالا خالی بود یا به مشکل خورد، ترب رو تست می‌کنه
    if not products:
        products = search_torob(query)
        
    return products


def format_product_message(products):
    if not products:
        return "❌ مشکلی در برقراری ارتباط با فروشگاه‌ها رخ داد یا محصولی یافت نشد. لطفاً مجدداً تلاش کنید."
        
    msg = f"🛍️ **نتایج یافت‌شده (منبع: {products[0]['source']}):**\n\n"
    for idx, item in enumerate(products, 1):
        price_str = f"{item['price']:,} تومان" if item['price'] > 0 else "استعلام قیمت"
        msg += f"{idx}. [{item['title']}]({item['link']})\n💰 **قیمت:** `{price_str}`\n───────────────\n"
        
    return msg
