import requests

def search_digikala(query):
    try:
        url = f"https://api.digikala.com/v1/product/search/?q={query}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        products = []
        if 'data' in data and 'products' in data['data']:
            for product in data['data']['products'][:10]:
                if product.get('rating', {}).get('rate', 0) >= 3:
                    products.append({
                        'name': product.get('title', 'بدون نام'),
                        'price': product.get('default_variant', {}).get('price', 0),
                        'rating': product.get('rating', {}).get('rate', 0),
                        'image': product.get('images', [{}])[0].get('url', ''),
                        'url': f"https://www.digikala.com/product/{product.get('id', '')}",
                        'shop': 'دیجیکالا'
                    })
        
        products.sort(key=lambda x: x['price'])
        return products[:5]
    except Exception as e:
        print(f"Digikala search error: {e}")
        return []

def search_torob(query):
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
    all_products = []
    all_products.extend(search_digikala(query))
    all_products.extend(search_torob(query))
    
    seen = set()
    unique_products = []
    for product in all_products:
        if product['name'] not in seen:
            seen.add(product['name'])
            unique_products.append(product)
    
    unique_products.sort(key=lambda x: x['price'])
    return unique_products[:5]

def format_product_message(products):
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
