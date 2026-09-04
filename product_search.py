import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def search_all_shops(query):
    """جستجوی مستقیم، ساده و بدون فیلتر در ترب"""
    products = []
    
    # ساخت URL مستقیم جستجو در ترب
    url = "https://api.torob.com/v4/base-product/search/"
    params = {
        'page': 0,
        'size': 10,
        'query': query  # عین عبارتی که کاربر تایپ کرده
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for item in results:
                title = item.get('name1') or item.get('name2')
                price = item.get('price', 0)
                
                # استخراج لینک محصول در ترب
                web_url = item.get('web_client_absolute_url', '')
                product_url = f"https://torob.com{web_url}" if web_url else "https://torob.com"
                
                if title:
                    products.append({
                        'title': title,
                        'price': price,
                        'link': product_url
                    })
        else:
            print(f"Torob API Status Code: {response.status_code}")

    except Exception as e:
        print(f"Error connecting to Torob: {e}")
        
    return products


def format_product_message(products):
    """فرمت‌دهی و نمایش خروجی"""
    if not products:
        return "❌ متأسفانه محصولی با این عبارت در ترب یافت نشد."
        
    msg = "🛍️ **نتایج جستجو در ترب:**\n\n"
    for idx, item in enumerate(products[:7], 1):
        price_str = f"{item['price']:,} تومان" if item['price'] > 0 else "استعلام قیمت"
        msg += f"{idx}. [{item['title']}]({item['link']})\n💰 **قیمت:** `{price_str}`\n───────────────\n"
        
    return msg
