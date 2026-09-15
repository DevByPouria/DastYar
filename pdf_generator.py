"""
سازنده PDF از اخبار اقتصادی
با پشتیبانی کامل از فارسی
"""
import os
import requests
from datetime import datetime, timedelta

from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display


FONT_PATH = "/tmp/Vazirmatn-Regular.ttf"
FONT_URL = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf"


def _ensure_font():
    """دانلود فونت فارسی اگه وجود نداره"""
    if os.path.exists(FONT_PATH):
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


def _strip_emoji(text):
    """حذف ایموجی‌ها (فونت فارسی ازشون پشتیبانی نمی‌کنه)"""
    if not text:
        return ""
    # لیست ساده از ایموجی‌های رایج
    emoji_map = {
        '🔴': '[H]', '🟡': '[M]', '🟢': '[L]', '⚪': '[?]',
        '📅': '', '⏰': '', '📖': '', '💡': '', '🥇': '', '💵': '',
        '📊': '', '📈': '', '📉': '', '⚠️': '!', '✅': 'OK',
        '━━': '=', '─': '-',
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    return text


def generate_news_pdf(events, bias, bull, bear, title="اخبار اقتصادی"):
    """ساخت PDF از لیست اخبار"""
    if not _ensure_font():
        print("[ERROR] Cannot generate PDF without font", flush=True)
        return None
    
    if not events:
        return None
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("Vazir", "", FONT_PATH, uni=True)
    pdf.set_font("Vazir", size=12)
    
    # ===== سرصفحه =====
    pdf.set_font("Vazir", size=18)
    pdf.cell(0, 12, _fa(f"تحلیل فاندامنتال — {title}"), ln=1, align='C')
    pdf.ln(3)
    
    pdf.set_font("Vazir", size=11)
    pdf.cell(0, 8, _fa(f"تاریخ گزارش: {datetime.now().strftime('%Y/%m/%d - %H:%M')}"), ln=1, align='C')
    pdf.cell(0, 8, _fa(f"تعداد اخبار: {len(events)}"), ln=1, align='C')
    
    bias_text = {'bullish': 'صعودی', 'bearish': 'نزولی', 'neutral': 'خنثی'}.get(bias, 'خنثی')
    pdf.cell(0, 8, _fa(f"بایاس کلی: {bias_text}"), ln=1, align='C')
    pdf.cell(0, 8, _fa(f"امتیاز صعودی: {bull} | امتیاز نزولی: {bear}"), ln=1, align='C')
    
    pdf.ln(3)
    pdf.set_draw_color(150, 150, 150)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # ===== اخبار =====
    today = datetime.now().date()
    
    for i, ev in enumerate(events, 1):
        try:
            # امتیاز importance
            impact_map = {'High': 'اهمیت بالا', 'Medium': 'اهمیت متوسط', 'Low': 'اهمیت کم'}
            impact_text = impact_map.get(ev.get('impact', 'Low'), 'اهمیت کم')
            
            # عنوان خبر
            pdf.set_font("Vazir", size=12)
            title_text = f"{i}. [{impact_text}] {ev.get('currency', '?')} - {ev.get('title', '')}"
            pdf.multi_cell(0, 7, _fa(_strip_emoji(title_text)))
            
            # تاریخ و ساعت
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
                info_line = f"تاریخ: {date_label}"
                if time_str:
                    info_line += f"  |  ساعت: {time_str}"
                pdf.set_font("Vazir", size=10)
                pdf.cell(0, 6, _fa(info_line), ln=1)
            
            # توضیح فارسی
            from news_fetcher import get_news_explanation
            explanation = get_news_explanation(ev.get('title', ''))
            if explanation:
                pdf.set_font("Vazir", size=10)
                pdf.multi_cell(0, 6, _fa(f"توضیح: {explanation['desc']}"))
                pdf.multi_cell(0, 6, _fa(f"تأثیر: {explanation['effect']}"))
                pdf.multi_cell(0, 6, _fa(f"طلا: {_strip_emoji(explanation['gold'])}  |  دلار: {_strip_emoji(explanation['dollar'])}"))
            
            # پیش‌بینی و قبلی
            forecast = ev.get('forecast', '')
            previous = ev.get('previous', '')
            if forecast and forecast != 'None':
                line = f"پیش‌بینی: {forecast}"
                if previous and previous != 'None':
                    line += f"  |  قبلی: {previous}"
                pdf.set_font("Vazir", size=10)
                pdf.cell(0, 6, _fa(line), ln=1)
            
            # خط جداکننده
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)
        
        except Exception as e:
            print(f"[WARN] PDF row error: {e}", flush=True)
            continue
    
    # ===== پاصفحه =====
    pdf.ln(5)
    pdf.set_font("Vazir", size=9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _fa("این تحلیل صرفاً آماری است و توصیه مالی نیست."))
    pdf.multi_cell(0, 5, _fa("منبع: Forex Factory"))
    pdf.multi_cell(0, 5, _fa("ربات: DastYar"))
    
    # ===== ذخیره =====
    output_path = f"/tmp/news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(output_path)
    
    print(f"[DEBUG] PDF saved: {output_path}", flush=True)
    return output_path
