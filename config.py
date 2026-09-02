import os

# توکن ربات - از متغیر محیطی می‌خونه
TOKEN = os.getenv('TOKEN')

# تنظیمات سرور
PORT = int(os.getenv('PORT', 10000))

# لینک‌های API برای گرفتن قیمت
TGJU_URL = "https://www.tgju.org/price-chart/"

# لیست فروشگاه‌های آنلاین برای جستجو
SHOP_APIS = {
    "digikala": "https://api.digikala.com/v1/",
    "torob": "https://api.torob.com/v3/",
}
