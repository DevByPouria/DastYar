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

        # ===== تعیین سیگنال =====
        if final >= 5:
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

        # ===== خلاصه‌ی فاندامنتال =====
        bias = fund_result.get('bias', 'neutral')
        bias_map = {'bullish': '🟢 صعودی', 'bearish': '🔴 نزولی', 'neutral': '⚪ خنثی'}
        msg += f"\n📰 **فاندامنتال:** {bias_map.get(bias, '⚪ خنثی')}"
        msg += f" (تحلیل {analyzed} خبر)\n"

        # ===== مدیریت ریسک =====
        sl = tech_result.get('stop_loss')
        tp = tech_result.get('take_profit')
        rr = tech_result.get('risk_reward')

        if sl and tp and signal_emoji in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
            msg += f"\n🎯 **مدیریت ریسک:**\n"
            msg += f"  🛑 حد ضرر: `${sl:,}`\n"
            msg += f"  ✅ حد سود: `${tp:,}`\n"
            if rr:
                msg += f"  📊 نسبت ریسک/ریوارد: `1:{rr}`\n"
        elif signal_emoji == 'NEUTRAL':
            msg += f"\n⚪ **سیگنال قوی نیست — انتظار بکش**\n"

        msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
