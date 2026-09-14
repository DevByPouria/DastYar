import pandas as pd
import pandas_ta as ta

class TechnicalAnalyzer:
    def __init__(self, prices_df):
        """
        prices_df: DataFrame با ستون‌های 'price' و 'timestamp'
        """
        self.df = prices_df.copy()
        self.signals = []
        self.bullish_score = 0
        self.bearish_score = 0

    def calculate_indicators(self):
        """محاسبه اندیکاتورهای تکنیکال"""
        if len(self.df) < 20:
            return
        
        # میانگین‌های متحرک
        self.df['SMA_10'] = ta.sma(self.df['price'], length=10)
        self.df['SMA_20'] = ta.sma(self.df['price'], length=20)
        self.df['SMA_50'] = ta.sma(self.df['price'], length=50)
        
        # RSI
        self.df['RSI'] = ta.rsi(self.df['price'], length=14)
        
        # ATR برای مدیریت ریسک
        self.df['ATR'] = ta.atr(
            self.df['price'], self.df['price'],
            self.df['price'], length=14
        )

    def analyze_ma_crossover(self):
        """استراتژی کراس‌آور میانگین متحرک (طلا و ارز)"""
        if len(self.df) < 20 or self.df['SMA_10'].isna().all():
            return
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # کراس ۱۰ و ۲۰
        if pd.notna(prev['SMA_10']) and pd.notna(prev['SMA_20']):
            # کراس طلایی
            if prev['SMA_10'] <= prev['SMA_20'] and latest['SMA_10'] > latest['SMA_20']:
                self.signals.append("🟢 کراس طلایی (SMA 10 از 20)")
                self.bullish_score += 3
            # کراس مرگ
            elif prev['SMA_10'] >= prev['SMA_20'] and latest['SMA_10'] < latest['SMA_20']:
                self.signals.append("🔴 کراس مرگ (SMA 10 به زیر 20)")
                self.bearish_score += 3
            # روند
            elif latest['price'] > latest['SMA_20']:
                self.signals.append("📈 قیمت بالای SMA 20 (روند صعودی)")
                self.bullish_score += 1
            else:
                self.signals.append("📉 قیمت زیر SMA 20 (روند نزولی)")
                self.bearish_score += 1

    def analyze_fibonacci(self):
        """استراتژی فیبوناچی بازگشتی"""
        if len(self.df) < 30:
            return
        
        recent = self.df.tail(30)
        high = recent['price'].max()
        low = recent['price'].min()
        diff = high - low
        
        if diff == 0:
            return
        
        latest_price = self.df['price'].iloc[-1]
        
        # سطوح فیبوناچی
        levels = {
            '23.6%': high - diff * 0.236,
            '38.2%': high - diff * 0.382,
            '50.0%': high - diff * 0.500,
            '61.8%': high - diff * 0.618,
            '78.6%': high - diff * 0.786,
        }
        
        for name, level in levels.items():
            if level <= 0:
                continue
            distance = abs(latest_price - level) / level
            if distance < 0.01:  # ۱٪ نزدیکی
                if name == '61.8%':
                    self.signals.append(f"🎯 نزدیک سطح طلایی فیبوناچی (61.8%)")
                    self.bullish_score += 2
                elif name == '50.0%':
                    self.signals.append(f"📍 نزدیک سطح 50% فیبوناچی")
                    self.bullish_score += 1
                elif name == '38.2%':
                    self.signals.append(f"📍 نزدیک سطح 38.2% فیبوناچی")
                    self.bearish_score += 1

    def analyze_breakout(self):
        """استراتژی خط شکست"""
        if len(self.df) < 20:
            return
        
        recent = self.df.tail(20)
        resistance = recent['price'].iloc[:-1].max()
        support = recent['price'].iloc[:-1].min()
        latest = self.df['price'].iloc[-1]
        
        # شکست مقاومت
        if latest > resistance * 1.005:
            self.signals.append(f"🚀 شکست مقاومت ({int(resistance):,})")
            self.bullish_score += 3
        # شکست حمایت
        elif latest < support * 0.995:
            self.signals.append(f"💥 شکست حمایت ({int(support):,})")
            self.bearish_score += 3

    def analyze_rsi(self):
        """تحلیل RSI (اشباع خرید/فروش)"""
        if 'RSI' not in self.df or self.df['RSI'].isna().all():
            return
        
        rsi = self.df['RSI'].iloc[-1]
        if pd.isna(rsi):
            return
        
        if rsi >= 70:
            self.signals.append(f"⚠️ RSI = {rsi:.1f} (اشباع خرید)")
            self.bearish_score += 2
        elif rsi <= 30:
            self.signals.append(f"⚠️ RSI = {rsi:.1f} (اشباع فروش)")
            self.bullish_score += 2

    def get_risk_levels(self, risk_mult=1.5, reward_mult=2.5):
        """سطوح حد ضرر و حد سود بر اساس ATR"""
        if 'ATR' not in self.df or self.df['ATR'].isna().all():
            return None, None
        
        atr = self.df['ATR'].iloc[-1]
        price = self.df['price'].iloc[-1]
        if pd.isna(atr) or pd.isna(price):
            return None, None
        
        stop_loss = int(price - atr * risk_mult)
        take_profit = int(price + atr * reward_mult)
        return stop_loss, take_profit

    def run_all(self):
        """اجرای همه تحلیل‌ها"""
        self.calculate_indicators()
        self.analyze_ma_crossover()
        self.analyze_fibonacci()
        self.analyze_breakout()
        self.analyze_rsi()
        
        return {
            'bullish_score': self.bullish_score,
            'bearish_score': self.bearish_score,
            'net_score': self.bullish_score - self.bearish_score,
            'signals': self.signals,
            'last_price': int(self.df['price'].iloc[-1]) if len(self.df) > 0 else 0,
        }
