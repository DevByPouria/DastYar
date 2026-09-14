class SignalEngine:
    def __init__(self, tech_weight=0.7, fund_weight=0.3):
        self.tech_weight = tech_weight
        self.fund_weight = fund_weight

    def generate(self, tech_result, fund_result, asset_name):
        """تولید سیگنال ترکیبی"""
        tech_score = tech_result.get('net_score', 0)
        fund_score = fund_result.get('score', 0)

        # نرمال‌سازی ساده
        # حداکثر امتیاز تکنیکال معمولاً ~ 10
        norm_tech = max(-10, min(10, tech_score))
        norm_fund = max(-10, min(10, fund_score))

        final = (norm_tech * self.tech_weight) + (norm_fund * self.fund_weight)

        if final >= 5:
            signal_text = "🟢🟢 **خرید قوی**"
        elif final >= 2:
            signal_text = "🟢 **خرید**"
        elif final <= -5:
            signal_text = "🔴🔴 **فروش قوی**"
        elif final <= -2:
            signal_text = "🔴 **فروش**"
        else:
            signal_text = "⚪ **خنثی (انتظار)**"

        # ساخت پیام
        msg = f"📈 **تحلیل ترکیبی {asset_name}**\n"
        msg += "━━━━━━━━━━━━━━━\n"
        msg += f"**سیگنال:** {signal_text}\n"
        msg += f"**امتیاز نهایی:** `{final:+.2f}` / 10\n\n"

        msg += "🔹 **دلایل تکنیکال:**\n"
        if tech_result.get('signals'):
            for s in tech_result['signals'][:5]:
                msg += f"  {s}\n"
        else:
            msg += "  ➖ سیگنال تکنیکال قوی‌ای یافت نشد.\n"

        msg += f"\n{fund_result.get('summary', '')}\n"

        # سطوح ریسک
        sl, tp = tech_result.get('stop_loss'), tech_result.get('take_profit')
        if sl and tp:
            msg += f"\n🎯 **مدیریت ریسک:**\n"
            msg += f"  🛑 حد ضرر: `{sl:,}` تومان\n"
            msg += f"  ✅ حد سود: `{tp:,}` تومان\n"

        msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
