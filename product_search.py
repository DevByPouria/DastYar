import requests

def search_all_shops(query):
    """جستجوی واقعی محصولات در API دیجیکالا"""
    products = []
    
    try:
        # API رسمی جستجوی دیجیکالا
        url = f"https://api.digikala.com/v1/search/?q={query}&page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('products', [])
            
            for item in items[:5]:  # ۵ محصول برتر
                title = item.get('title_fa', 'بدون عنوان')
                product_id = item.get('id')
                
                # قیمت به ریال است و به تومان تبدیل می‌شود
                price_rr = item.get('price', {}).get('selling_price', 0)
                price_toman = price_rr // 10
                
                rating = item.get('rating', {}).get('rate', 0)
                # تبدیل از ۱۰۰ به ۵
                rating_5 = round((rating / 20), 1) if rating else "ثبت نشده"
                
                product_url = f"https://www.digikala.com/product/dk-{product_id}/"
                
                products.append({
                    'name': title,
                    'price': price_toman,
                    'rating': rating_5,
                    'shop': 'دیجیکالا',
                    'url': product_url
                })
    except Exception as e:
        print(f"Error searching Digikala: {e}")

    return products

def format_product_message(products):
    if not products:
        return "❌ هیچ محصولی با این عنوان پیدا نشد."
    
    message = "🛍️ **نتایج جستجوی واقعی**\n\n"
    for i, product in enumerate(products, 1):
        message += f"{i}. **{product['name']}**\n"
        if product['price'] > 0:
            message += f"💰 قیمت: {product['price']:,} تومان\n"
        else:
            message += "💰 قیمت: ناموجود\n"
        message += f"⭐ امتیاز: {product['rating']}\n"
        message += f"🏪 فروشگاه: {product['shop']}\n"
        message += f"🔗 [لینک مشاهده و خرید]({product['url']})\n\n"
    
    return message
