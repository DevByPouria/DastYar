import requests
import json
import re
from bs4 import BeautifulSoup

def search_digikala(query):
    """جستجو در دیجیکالا و برگرداندن ۵ محصول برتر"""
    try:
        url = f"https://api.digikala.com/v1/product/search/?q={query}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        products = []
        if 'data' in data and 'products' in data['data']:
            for product in data['data']['products'][:10]:
                # فیلتر کردن محصولات با کیفیت بالا
                if product.get('rating', {}).get('rate', 0) >= 3:
                    products.append({
                        'name': product.get('title', 'بدون نام'),
                        'price': product.get('default_variant', {}).get('price', 0),
                        'rating': product.get('rating', {}).get('rate', 0),
                        'image': product.get('images', [{}])[0].get('url', ''),
                        'url': f"https://www.digikala.com/product/{product.get('id', '')}",
                        'shop': 'دیجیکالا'
                    })
        
        # مرتب‌سازی بر اساس قیمت (ارزان‌ترین اول)
        products.sort(key=lambda x: x['price'])
        return products[:5]
    except Exception as e:
        print(f"Digikala search error: {e}")
        return []

def search_torob(query):
    """جستجو در ترب و برگرداندن ۵ محصول برتر"""
    try:
        url = f"https://api.torob.com/v3/search/?query={query}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        products = []
        if 'results' in data:
            for item in data['results'][:10]:
                if item.get('rating', 0) >= 3:
                    products.append({
                        'name': item.get('name', 'بدون نام'),
                        'price': item.get('price', 0),
                        'rating': item.get('rating', 0),
                        'image': item.get('image', ''),
                        'url': item.get('url', ''),
                        'shop': 'ترب'
                    })
        
        products.sort(key=lambda x: x['price'])
        return products[:5]
    except Exception as e:
        print(f"Torob search error: {e}")
        return []

def search_all_shops(query):
    """جستجو در همه‌ی فروشگاه‌ها و ترکیب نتایج"""
    all_products = []
    
    # جستجو در دیجیکالا
    digi_products = search_digikala(query)
    all_products.extend(digi_products)
    
    # جستجو در ترب
    torob_products = search_torob(query)
    all_products.extend(torob_products)
    
    # حذف محصولات تکراری بر اساس نام
    seen = set()
    unique_products = []
    for product in all_products:
        if product['name'] not in seen:
            seen.add(product['name'])
            unique_products.append(product)
    
    # مرتب‌سازی نهایی بر اساس قیمت
    unique_products.sort(key=lambda x: x['price'])
    
    return unique_products[:5]

def format_product_message(products):
    """قالب‌بندی محصولات برای ارسال به کاربر"""
    if not products:
        return "❌ محصولی پیدا نشد. لطفاً عبارت دیگری را امتحان کنید."
    
    message = "🛍️ **بهترین محصولات پیدا شده**\n\n"
    for i, product in enumerate(products, 1):
        message += f"**{i}. {product['name']}**\n"
        message += f"💰 قیمت: {product['price']:,} تومان\n"
        message += f"⭐ امتیاز: {product['rating']}/5\n"
        message += f"🏪 فروشگاه: {product['shop']}\n"
        message += f"🔗 [لینک خرید]({product['url']})\n\n"
    
    return message
