import random

def search_all_shops(query):
    sample_products = [
        {
            'name': f'محصول نمونه ۱ برای "{query}"',
            'price': random.randint(100000, 5000000),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'shop': 'دیجیکالا',
            'url': 'https://www.digikala.com'
        },
        {
            'name': f'محصول نمونه ۲ برای "{query}"',
            'price': random.randint(200000, 6000000),
            'rating': round(random.uniform(3.0, 4.8), 1),
            'shop': 'ترب',
            'url': 'https://www.torob.com'
        },
        {
            'name': f'محصول نمونه ۳ برای "{query}"',
            'price': random.randint(150000, 4000000),
            'rating': round(random.uniform(4.0, 5.0), 1),
            'shop': 'دیجیکالا',
            'url': 'https://www.digikala.com'
        }
    ]
    return sample_products

def format_product_message(products):
    if not products:
        return "❌ محصولی پیدا نشد. لطفاً عبارت دیگری را امتحان کنید."
    
    message = "🛍️ بهترین محصولات پیدا شده (نسخه آزمایشی)\n\n"
    for i, product in enumerate(products, 1):
        message += f"{i}. {product['name']}\n"
        message += f"💰 قیمت: {product['price']:,} تومان\n"
        message += f"⭐ امتیاز: {product['rating']}/5\n"
        message += f"🏪 فروشگاه: {product['shop']}\n"
        message += f"🔗 لینک خرید: {product['url']}\n\n"
    
    return message
