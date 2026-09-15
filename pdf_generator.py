"""
سازنده PDF از اخبار اقتصادی
با پشتیبانی کامل از فارسی
"""
import os
import requests
from datetime import datetime, timedelta

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import arabic_reshaper
from bidi.algorithm import get_display


FONT_PATH = "/tmp/Vazirmatn-Regular.ttf"
FONT_URL = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf"


def _ensure_font():
    """دانلود فونت فارسی اگه وجود نداره"""
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 10000:
        return True
    try:
        print("[DEBUG] Downloading Vazirmatn font...", flush=True)
        res = requests.get(FONT_URL, timeout=30, allow_redirects=True)
        if res.status_code == 200 and len(res.content) > 10000:
            with open(FONT_PATH, 'wb') as f:
                f.write(res.content)
            print(f"[DEBUG] Font downloaded ({len(res.content)} bytes)", flush=True)
            return True
        print(f"[DEBUG] Font download failed: status={res.status_code}, size={len(res.content)}", flush=True)
    except Exception as e:
        print(f"[DEBUG] Font download error: {e}", flush=True)
    return False


def _fa(text):
    """تبدیل متن فارسی برای PDF (RTL)"""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)


def _to_fa_num(n):
    """تبدیل عدد انگلیسی به فارسی برای حل مشکل Bidi"""
    return str(n).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))


def _strip_emoji(text):
    """حذف ایموجی‌ها (فونت فارسی ازشون پشتیبانی نمی‌کنه)"""
    if not text:
        return ""
    emoji_map = {
        '🔴': '[HIGH]', '🟡': '[MED]', '🟢': '[LOW]', '⚪': '[?]',
        '📅': '', '⏰': '', '📖': '', '💡': '', '🥇': '', '💵': '',
        '📊': '', '📈': '', '📉': '', '⚠️': '!', '✅': '[OK]',
        '━━': '=', '─': '-', '—': '-',
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    return text.strip()


def generate_news_pdf(events, bias, bull, bear, title="اخبار اقتصادی"):
    """ساخت PDF از لیست اخبار"""
    if not _ensure_font():
        print("[ERROR] Cannot generate PDF without font", flush=True)
        return None
    
    if not events:
        return None
    
    # ⭐ استفاده از A4 با حاشیه‌ی مناسب
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # ⭐ اضافه کردن فونت
    pdf.add_font("Vazir", "", FONT_PATH)
    pdf.set_font("Vazir", size=11)
    
    # ⭐ محاسبه‌ی عرض قابل استفاده
    epw = pdf.w - pdf.l_margin - pdf.r_margin  # Effective Page Width
    
    # ===== سرصفحه =====
    pdf.set_font("Vazir", size=16)
    pdf.multi_cell(
        epw, 10,
        _fa(f"تحلیل فاندامنتال - {title}"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.ln(2)
    
    pdf.set_font("Vazir", size=10)
    pdf.multi_cell(
        epw, 6,
        _fa(f"تاریخ: {datetime.now().strftime('%Y/%m/%d - %H:%M')}"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.multi_cell(
        epw, 6,
        _fa(f"تعداد اخبار: {len(events)}"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    
    bias_text = {'bullish': 'صعودی', 'bearish': 'نزولی', 'neutral': 'خنثی'}.get(bias, 'خنثی')
    pdf.multi_cell(
        epw, 6,
        _fa(f"بایاس کلی: {bias_text}  |  امتیاز صعودی: {bull}  |  امتیاز نزولی: {bear}"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    
    pdf.ln(3)
    pdf.set_draw_color(150, 150, 150)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(5)
    
    # ===== اخبار =====
    today = datetime.now().date()
    
    # import داخل تابع برای جلوگیری از circular import
    try:
        from news_fetcher import get_news_explanation
    except:
        def get_news_explanation(t):
            return None
    
    for i, ev in enumerate(events, 1):
        try:
            # چک کن فضای کافی هست، اگه نه صفحه جدید
            if pdf.get_y() > 250:
                pdf.add_page()
            
            # ===== عنوان خبر =====
            impact_map = {'High': 'اهمیت بالا', 'Medium': 'اهمیت متوسط', 'Low': 'اهمیت کم'}
            impact_text = impact_map.get(ev.get('impact', 'Low'), 'اهمیت کم')
            
            pdf.set_font("Vazir", size=11)
            # ⭐ تغییر: شماره با اعداد فارسی + مرتب‌سازی جدید
            title_text = f"{_to_fa_num(i)}. [{impact_text}] {ev.get('currency', '?')} - {ev.get('title', '')}"
            pdf.multi_cell(
                epw, 6,
                _fa(_strip_emoji(title_text)),
                new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )
            
            # ===== تاریخ و ساعت =====
            date_label = ''
            if ev.get('parsed_date'):
                ev_date = ev['parsed_date']
                if ev_date == today:
                    date_label = 'امروز'
                elif ev_date == today + timedelta(days=1):
                    date_label = 'فردا'
                else:
                    date_label = ev_date.strftime('%Y/%m/%d')
            
            time_str = ev.get('time', '')
            if date_label:
                info_line = f"   تاریخ: {date_label}"
                if time_str:
                    info_line += f"  |  ساعت: {time_str}"
                pdf.set_font("Vazir", size=9)
                pdf.multi_cell(
                    epw, 5,
                    _fa(info_line),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
            
            # ===== توضیح فارسی =====
            explanation = get_news_explanation(ev.get('title', ''))
            if explanation:
                pdf.set_font("Vazir", size=9)
                pdf.multi_cell(
                    epw, 5,
                    _fa(f"   توضیح: {explanation['desc']}"),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
                pdf.multi_cell(
                    epw, 5,
                    _fa(f"   تأثیر: {explanation['effect']}"),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
                pdf.multi_cell(
                    epw, 5,
                    _fa(f"   طلا: {_strip_emoji(explanation['gold'])}  |  دلار: {_strip_emoji(explanation['dollar'])}"),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
            
            # ===== پیش‌بینی و قبلی =====
            forecast = ev.get('forecast', '')
            previous = ev.get('previous', '')
            actual = ev.get('actual', '')
            
            if forecast and forecast != 'None':
                line = f"   پیش‌بینی: {forecast}"
                if previous and previous != 'None':
                    line += f"  |  قبلی: {previous}"
                if actual and actual != 'None':
                    line += f"  |  واقعی: {actual}"
                pdf.set_font("Vazir", size=9)
                pdf.multi_cell(
                    epw, 5,
                    _fa(line),
                    new_x=XPos.LMARGIN, new_y=YPos.NEXT
                )
            
            # ===== خط جداکننده =====
            pdf.ln(1)
            pdf.set_draw_color(220, 220, 220)
            y = pdf.get_y()
            pdf.line(pdf.l_margin + 3, y, pdf.w - pdf.r_margin - 3, y)
            pdf.ln(3)
        
        except Exception as e:
            print(f"[WARN] PDF row error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            continue
    
        # ===== پاصفحه =====
    if pdf.get_y() > 240:
        pdf.add_page()
    
    pdf.ln(5)
    
    # خط جداکننده بالای پاصفحه
    pdf.set_draw_color(180, 180, 180)
    y = pdf.get_y()
    pdf.line(pdf.l_margin + 20, y, pdf.w - pdf.r_margin - 20, y)
    pdf.ln(4)
    
    pdf.set_font("Vazir", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        epw, 5,
        _fa("این تحلیل صرفاً آماری است و توصیه مالی نیست."),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.multi_cell(
        epw, 5,
        _fa("منبع داده: Forex Factory"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    
    pdf.ln(3)
    
    # ⭐ اطلاعات سازنده
    pdf.set_font("Vazir", size=9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(
        epw, 6,
        _fa("دستیار مالی هوشمند DastYar"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    
    pdf.set_font("Vazir", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        epw, 5,
        _fa("ساخته شده توسط: پوریا"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.multi_cell(
        epw, 5,
        _fa("@DevByPouria"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    pdf.multi_cell(
        epw, 5,
        _fa("github.com/DevByPouria"),
        align='C',
        new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )
    
    # ===== ذخیره =====
    output_path = f"/tmp/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(output_path)
    
    print(f"[DEBUG] PDF saved: {output_path} ({os.path.getsize(output_path)} bytes)", flush=True)
    return output_path
