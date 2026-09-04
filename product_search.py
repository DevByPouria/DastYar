import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# هدر استاندارد برای جلوگیری از مسدود شدن درخواست‌ها توسط سایت‌ها
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.9",
}

def search_torob(query: str, limit: int = 5) -> list:
    """
    جستجوی کالا در سایت ترب (Torob API)
    """
    url = f"https://api.torob.com/v4/base-product/search/?q={quote(query)}&page=0&size={limit}"
    results = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code == 200:
            data = response.json()
            products = data.get("results", [])
            
            for item in products[:limit]:
                title = item.get("name1") or item.get("name2", "بدون عنوان")
                price = item.get("price", 0)
                prk = item.get("random_key", "")
                
                # ساخت لینک مستقیم محصول در ترب
                product_url = f"https://torob.com/p/{prk}/" if prk else "https://torob.com"
                
                formatted_price = f"{price:,} تومان" if isinstance(price, int) and price > 0 else "نامشخص"
                
                results.append({
                    "source": "ترب",
                    "title": title,
                    "price": formatted_price,
                    "raw_price": price if isinstance(price, int) else 0,
                    "url": product_url
                })
    except Exception as e:
        print(f"[!] خطا در دریافت اطلاعات از ترب: {e}")
        
    return results


def search_basalam(query: str, limit: int = 5) -> list:
    """
    جستجوی کالا در بازار باسلام (Basalam API)
    """
    url = f"https://search.basalam.com/ai-engine/v1/search?q={quote(query)}&from=0&size={limit}"
    results = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            
            for item in products[:limit]:
                title = item.get("title", "بدون عنوان")
                # قیمت در باسلام به ریال محاسبه می‌شود (تبدیل به تومان):
                price_rials = item.get("price", 0)
                price_toman = price_rials // 10 if price_rials else 0
                
                vendor = item.get("vendor", {})
                vendor_identifier = vendor.get("identifier", "")
                product_id = item.get("id", "")
                
                # ساخت لینک محصول باسلام
                product_url = f"https://basalam.com/{vendor_identifier}/product/{product_id}" if vendor_identifier and product_id else "https://basalam.com"
                
                formatted_price = f"{price_toman:,} تومان" if price_toman > 0 else "نامشخص"
                
                results.append({
                    "source": "باسلام",
                    "title": title,
                    "price": formatted_price,
                    "raw_price": price_toman,
                    "url": product_url
                })
    except Exception as e:
        print(f"[!] خطا در دریافت اطلاعات از باسلام: {e}")
        
    return results


def search_all_products(query: str, limit_per_source: int = 5, sort_by_price: bool = False) -> list:
    """
    جستجوی هم‌زمان (Fast Asynchronous Execution) در تمام فروشگاه‌ها
    """
    all_results = []
    
    # استفاده از ThreadPoolExecutor برای ارسال هم‌زمان درخواست‌ها و بالابردن سرعت
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_torob = executor.submit(search_torob, query, limit_per_source)
        future_basalam = executor.submit(search_basalam, query, limit_per_source)
        
        for future in as_completed([future_torob, future_basalam]):
            try:
                res = future.result()
                all_results.extend(res)
            except Exception as e:
                print(f"[!] خطا در اجرای جستجو: {e}")
                
    # مرتب‌سازی بر اساس قیمت (در صورت درخواست)
    if sort_by_price:
        all_results = sorted(all_results, key=lambda x: x["raw_price"])

    return all_results
