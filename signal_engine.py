class SignalEngine:
    def __init__(self, tech_weight=0.65, fund_weight=0.35):
        self.tech_weight = tech_weight
        self.fund_weight = fund_weight

    def generate(self, tech_result, fund_result, asset_name):
        """تولید سیگنال ترکیبی با Confluence Scoring"""
        tech_score = tech_result.get('net_score', 0)
        fund_score = fund_result.get('score', 0)
        tech_conf = tech_result.get('confidence', 0)
        analyzed = fund_result.get('analyzed_count', 0)

        # نرمال‌سازی
        norm_tech = max(-10, min(10, tech_score))
        norm_fund = max(-10, min(10, fund_score))

        # امتیاز ترکیبی
        final = (norm_tech * self.tech_weight) + (norm_fund * self.fund_weight)

        # Confidence نهایی
        total_conf = tech_conf
        if analyzed >= 5:
            total_conf = min(100, tech_conf + 15)
        elif analyzed >= 2:
            total_conf = min(100, tech_conf + 8)

        # ===== تشخیص حالت مختلط =====
        tech_sign = 1 if tech_score > 0 else (-1 if tech_score < 0 else 0)
        fund_sign = 1 if fund_score > 0 else (-1 if fund_score < 0 else 0)
        is_mixed = (tech_sign * fund_sign == -1 and 
                    abs(tech_score) >= 2 and 
                    abs(fund_score) >= 2)

        # ===== تعیین سیگنال =====
        if is_mixed:
            signal_text = "⚖️ **مختلط (سیگنال‌های متناقض)**"
            signal_emoji = "MIXED"
        elif final >= 5:
            signal_text = "🟢🟢 **خرید قوی**"
            signal_emoji = "STRONG_BUY"
        elif final >= 2:
            signal_text = "🟢 **خرید**"
            signal_emoji = "BUY"
        elif final <= -5:
            signal_text = "🔴🔴 **فروش قوی**"
            signal_emoji = "STRONG_SELL"
        elif final <= -2:
            signal_text = "🔴 **فروش**"
            signal_emoji = "SELL"
        else:
            signal_text = "⚪ **خنثی (انتظار)**"
            signal_emoji = "NEUTRAL"

        # ===== ساخت پیام =====
        msg = f"📈 **تحلیل ترکیبی {asset_name}**\n"
        msg += "━━━━━━━━━━━━━━━\n"
        msg += f"**سیگنال:** {signal_text}\n"
        msg += f"**امتیاز نهایی:** `{final:+.2f}` / 10\n"
        msg += f"**اطمینان:** `{total_conf}%`\n\n"

        # ===== دلایل تکنیکال =====
        msg += "🔹 **تحلیل تکنیکال:**\n"
        if tech_result.get('signals'):
            for s in tech_result['signals'][:6]:
                msg += f"  {s}\n"
        else:
            msg += "  ➖ سیگنال تکنیکال قوی‌ای یافت نشد.\n"

        # ===== خلاصه‌ی فاندامنتال با امتیاز عددی =====
        bias = fund_result.get('bias', 'neutral')
        bias_map = {'bullish': '🟢 صعودی', 'bearish': '🔴 نزولی', 'neutral': '⚪ خنثی'}
        fund_emoji = '🟢' if fund_score > 0 else ('🔴' if fund_score < 0 else '⚪')
        msg += f"\n📰 **فاندامنتال:** {bias_map.get(bias, '⚪ خنثی')} ({fund_emoji} `{fund_score:+d}`)"
        msg += f" — تحلیل {analyzed} خبر\n"

        # ===== امتیاز تکنیکال =====
        tech_emoji = '🟢' if tech_score > 0 else ('🔴' if tech_score < 0 else '⚪')
        msg += f"🔧 **تکنیکال:** {tech_emoji} `{tech_score:+d}`\n"

        # ===== مدیریت ریسک =====
        sl = tech_result.get('stop_loss')
        tp = tech_result.get('take_profit')
        rr = tech_result.get('risk_reward')

        if is_mixed:
            msg += f"\n⚖️ **سیگنال‌ها متناقضن — ورود نکن**\n"
            msg += f"   🔧 تکنیکال: `{tech_score:+d}`  |  📰 فاندامنتال: `{fund_score:+d}`\n"
        elif sl and tp and signal_emoji in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
            msg += f"\n🎯 **مدیریت ریسک:**\n"
            msg += f"  🛑 حد ضرر: `${sl:,}`\n"
            msg += f"  ✅ حد سود: `${tp:,}`\n"
            if rr:
                msg += f"  📊 نسبت ریسک/ریوارد: `1:{rr}`\n"
        elif signal_emoji == 'NEUTRAL':
            msg += f"\n⚪ **سیگنال قوی نیست — انتظار بکش**\n"

        msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
