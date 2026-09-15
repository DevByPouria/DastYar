"""
موتور تحلیل تکنیکال حرفه‌ای
با ۷ استراتژی مختلف
"""
import pandas as pd
import pandas_ta_classic as ta


class TechnicalAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        self.signals = []
        self.bull_score = 0
        self.bear_score = 0
        self.confidence = 0  # 0-100

    # ============================================
    # ۱. محاسبه‌ی همه‌ی اندیکاتورها
    # ============================================
    def calculate_indicators(self):
        if len(self.df) < 20:
            return

        price = self.df['price']

        # میانگین‌های متحرک
        if len(self.df) >= 10:
            self.df['SMA_10'] = ta.sma(price, length=10)
        if len(self.df) >= 20:
            self.df['SMA_20'] = ta.sma(price, length=20)
        if len(self.df) >= 50:
            self.df['SMA_50'] = ta.sma(price, length=50)
        if len(self.df) >= 200:
            self.df['SMA_200'] = ta.sma(price, length=200)
        self.df['EMA_9'] = ta.ema(price, length=9)
        self.df['EMA_21'] = ta.ema(price, length=21)

        # RSI
        self.df['RSI'] = ta.rsi(price, length=14)

        # MACD
        macd = ta.macd(price, fast=12, slow=26, signal=9)
        if macd is not None:
            self.df['MACD'] = macd.iloc[:, 0]
            self.df['MACD_signal'] = macd.iloc[:, 2]
            self.df['MACD_hist'] = macd.iloc[:, 1]

        # Bollinger Bands
        bb = ta.bbands(price, length=20, std=2)
        if bb is not None:
            self.df['BB_lower'] = bb.iloc[:, 0]
            self.df['BB_mid'] = bb.iloc[:, 1]
            self.df['BB_upper'] = bb.iloc[:, 2]

        # ATR
        self.df['ATR'] = ta.atr(
            self.df['high'] if 'high' in self.df else price,
            self.df['low'] if 'low' in self.df else price,
            price, length=14
        )

    # ============================================
    # ۲. کراس‌آور SMA 50/200 + Fallback به SMA_50
    # ============================================
    def strategy_ma_50_200(self):
        # حداقل ۵۰ رکورد برای SMA_50
        if len(self.df) < 50:
            return
        if 'SMA_50' not in self.df or self.df['SMA_50'].isna().all():
            return
        
        latest = self.df.iloc[-1]
        price = latest['price']
        
        if pd.isna(latest['SMA_50']):
            return
        
        # ===== اگه SMA_200 نداریم، فقط SMA_50 رو چک کن =====
        if 'SMA_200' not in self.df or self.df['SMA_200'].isna().all():
            if price > latest['SMA_50'] * 1.002:
                self.signals.append("🟢 قیمت بالای SMA 50 (روند صعودی کوتاه‌مدت)")
                self.bull_score += 2
                self.confidence += 8
            elif price < latest['SMA_50'] * 0.998:
                self.signals.append("🔴 قیمت زیر SMA 50 (روند نزولی کوتاه‌مدت)")
                self.bear_score += 2
                self.confidence += 8
            return
        
        # ===== اگه SMA_200 داریم، تحلیل کامل =====
        prev = self.df.iloc[-2]
        
        if pd.isna(prev['SMA_50']) or pd.isna(prev['SMA_200']):
            return
        
        # Golden Cross (تازه اتفاق افتاده)
        if prev['SMA_50'] <= prev['SMA_200'] and latest['SMA_50'] > latest['SMA_200']:
            self.signals.append("🌟 Golden Cross (SMA 50/200) — روند صعودی بلندمدت")
            self.bull_score += 4
            self.confidence += 15
        # Death Cross (تازه اتفاق افتاده)
        elif prev['SMA_50'] >= prev['SMA_200'] and latest['SMA_50'] < latest['SMA_200']:
            self.signals.append("💀 Death Cross (SMA 50/200) — روند نزولی بلندمدت")
            self.bear_score += 4
            self.confidence += 15
        # SMA_50 بالای SMA_200 (روند صعودی موجود)
        elif latest['SMA_50'] > latest['SMA_200']:
            self.signals.append("🟢 SMA 50 بالای SMA 200 (روند صعودی)")
            self.bull_score += 2
            self.confidence += 8
        # SMA_50 زیر SMA_200 (روند نزولی موجود)
        else:
            self.signals.append("🔴 SMA 50 زیر SMA 200 (روند نزولی)")
            self.bear_score += 2
            self.confidence += 8

    # ============================================
    # ۳. کراس‌آور EMA 9/21 (نسخه حساس‌تر)
    # ============================================
    def strategy_ema_9_21(self):
        if 'EMA_21' not in self.df or self.df['EMA_21'].isna().all():
            return

        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]

        if pd.isna(latest['EMA_9']) or pd.isna(latest['EMA_21']):
            return

        # ===== حالت ۱: EMA 9 بالای EMA 21 (مومنتوم صعودی) =====
        if latest['EMA_9'] > latest['EMA_21']:
            # چک کن آیا کراس تازه اتفاق افتاده
            if not pd.isna(prev['EMA_9']) and not pd.isna(prev['EMA_21']):
                if prev['EMA_9'] <= prev['EMA_21']:
                    self.signals.append("🚀 کراس صعودی EMA 9/21 (سیگنال تازه)")
                    self.bull_score += 2
                    self.confidence += 8
                else:
                    self.signals.append("🟢 EMA 9 بالای EMA 21 (مومنتوم صعودی)")
                    self.bull_score += 1
                    self.confidence += 4
        # ===== حالت ۲: EMA 9 زیر EMA 21 (مومنتوم نزولی) =====
        else:
            if not pd.isna(prev['EMA_9']) and not pd.isna(prev['EMA_21']):
                if prev['EMA_9'] >= prev['EMA_21']:
                    self.signals.append("💥 کراس نزولی EMA 9/21 (سیگنال تازه)")
                    self.bear_score += 2
                    self.confidence += 8
                else:
                    self.signals.append("🔴 EMA 9 زیر EMA 21 (مومنتوم نزولی)")
                    self.bear_score += 1
                    self.confidence += 4

    # ============================================
    # ۴. MACD (نسخه حساس‌تر)
    # ============================================
    def strategy_macd(self):
        if 'MACD' not in self.df or self.df['MACD'].isna().all():
            return

        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]

        if pd.isna(latest['MACD']) or pd.isna(latest['MACD_signal']):
            return

        # ===== حالت ۱: MACD بالای Signal (صعودی) =====
        if latest['MACD'] > latest['MACD_signal']:
            # چک کن کراس تازه اتفاق افتاده
            if not pd.isna(prev['MACD']) and not pd.isna(prev['MACD_signal']):
                if prev['MACD'] <= prev['MACD_signal']:
                    self.signals.append("📈 کراس صعودی MACD (سیگنال تازه)")
                    self.bull_score += 3
                    self.confidence += 10
                else:
                    self.signals.append("🟢 MACD بالای Signal (صعودی)")
                    self.bull_score += 1
                    self.confidence += 4
        # ===== حالت ۲: MACD زیر Signal (نزولی) =====
        else:
            if not pd.isna(prev['MACD']) and not pd.isna(prev['MACD_signal']):
                if prev['MACD'] >= prev['MACD_signal']:
                    self.signals.append("📉 کراس نزولی MACD (سیگنال تازه)")
                    self.bear_score += 3
                    self.confidence += 10
                else:
                    self.signals.append("🔴 MACD زیر Signal (نزولی)")
                    self.bear_score += 1
                    self.confidence += 4

        # ===== هیستوگرام =====
        if 'MACD_hist' in self.df and not pd.isna(latest['MACD_hist']):
            if not pd.isna(prev['MACD_hist']):
                if latest['MACD_hist'] > 0 and latest['MACD_hist'] > prev['MACD_hist']:
                    self.signals.append("📊 MACD Histogram صعودی (شتاب مثبت)")
                    self.bull_score += 1
                elif latest['MACD_hist'] < 0 and latest['MACD_hist'] < prev['MACD_hist']:
                    self.signals.append("📊 MACD Histogram نزولی (شتاب منفی)")
                    self.bear_score += 1

    # ============================================
    # ۵. RSI
    # ============================================
    def strategy_rsi(self):
        if 'RSI' not in self.df or self.df['RSI'].isna().all():
            return

        rsi = self.df['RSI'].iloc[-1]
        if pd.isna(rsi):
            return

        if rsi >= 70:
            self.signals.append(f"⚠️ RSI = {rsi:.1f} (اشباع خرید)")
            self.bear_score += 3
            self.confidence += 8
        elif rsi <= 30:
            self.signals.append(f"⚠️ RSI = {rsi:.1f} (اشباع فروش)")
            self.bull_score += 3
            self.confidence += 8
        elif 45 <= rsi <= 55:
            self.signals.append(f"⚖️ RSI = {rsi:.1f} (خنثی)")
        elif rsi > 55:
            self.signals.append(f"🟢 RSI = {rsi:.1f} (مومنتوم صعودی)")
            self.bull_score += 1
        else:
            self.signals.append(f"🔴 RSI = {rsi:.1f} (مومنتوم نزولی)")
            self.bear_score += 1

    # ============================================
    # ۶. Bollinger Bands
    # ============================================
    def strategy_bollinger(self):
        if 'BB_upper' not in self.df or self.df['BB_upper'].isna().all():
            return

        latest = self.df.iloc[-1]
        price = latest['price']

        if pd.isna(latest['BB_upper']):
            return

        # لمس باند بالا → احتمال برگشت
        if price >= latest['BB_upper'] * 0.998:
            self.signals.append("⚠️ قیمت روی Bollinger Upper (احتمال برگشت)")
            self.bear_score += 2
        # لمس باند پایین → احتمال برگشت
        elif price <= latest['BB_lower'] * 1.002:
            self.signals.append("⚠️ قیمت روی Bollinger Lower (احتمال برگشت)")
            self.bull_score += 2
        # نزدیک باند بالا (هشدار)
        elif price >= latest['BB_upper'] * 0.99:
            self.signals.append("📈 قیمت نزدیک Bollinger Upper")
            self.bear_score += 1
        # نزدیک باند پایین (فرصت)
        elif price <= latest['BB_lower'] * 1.01:
            self.signals.append("📉 قیمت نزدیک Bollinger Lower")
            self.bull_score += 1

    # ============================================
    # ۷. Breakout + Support/Resistance
    # ============================================
    def strategy_breakout(self):
        if len(self.df) < 20:
            return

        recent = self.df.tail(20)
        resistance = recent['price'].iloc[:-1].max()
        support = recent['price'].iloc[:-1].min()
        latest = self.df['price'].iloc[-1]

        # شکست مقاومت
        if latest > resistance * 1.005:
            self.signals.append(f"🚀 شکست مقاومت ({int(resistance):,})")
            self.bull_score += 3
            self.confidence += 12
        # شکست حمایت
        elif latest < support * 0.995:
            self.signals.append(f"💥 شکست حمایت ({int(support):,})")
            self.bear_score += 3
            self.confidence += 12
        # نزدیک سطوح
        elif latest > resistance * 0.995:
            self.signals.append(f"📍 نزدیک مقاومت ({int(resistance):,})")
            self.bear_score += 1
        elif latest < support * 1.005:
            self.signals.append(f"📍 نزدیک حمایت ({int(support):,})")
            self.bull_score += 1

    # ============================================
    # ۸. فیبوناچی
    # ============================================
    def strategy_fibonacci(self):
        if len(self.df) < 30:
            return

        recent = self.df.tail(30)
        high = recent['price'].max()
        low = recent['price'].min()
        diff = high - low

        if diff == 0:
            return

        latest = self.df['price'].iloc[-1]
        levels = {
            '23.6%': high - diff * 0.236,
            '38.2%': high - diff * 0.382,
            '50.0%': high - diff * 0.500,
            '61.8%': high - diff * 0.618,
        }

        for name, level in levels.items():
            if level <= 0:
                continue
            distance = abs(latest - level) / level
            if distance < 0.008:
                if name == '61.8%':
                    self.signals.append("🎯 سطح طلایی فیبوناچی (61.8%)")
                    self.bull_score += 2
                    self.confidence += 6
                elif name == '50.0%':
                    self.signals.append("📍 سطح 50% فیبوناچی")
                    self.bull_score += 1
                elif name == '38.2%':
                    self.signals.append("📍 سطح 38.2% فیبوناچی")
                    self.bear_score += 1

    # ============================================
    # اجرای همه
    # ============================================
    def run_all(self):
        self.calculate_indicators()
        self.strategy_ma_50_200()
        self.strategy_ema_9_21()
        self.strategy_macd()
        self.strategy_rsi()
        self.strategy_bollinger()
        self.strategy_breakout()
        self.strategy_fibonacci()

        net = self.bull_score - self.bear_score
        self.confidence = min(100, self.confidence)

        return {
            'bull_score': self.bull_score,
            'bear_score': self.bear_score,
            'net_score': net,
            'confidence': self.confidence,
            'signals': self.signals,
            'last_price': float(self.df['price'].iloc[-1]) if len(self.df) > 0 else 0,
        }

    # ============================================
    # سطوح ریسک بر اساس جهت
    # ============================================
    def get_risk_levels(self, direction='BUY', risk_mult=1.5, reward_mult=2.5):
        if 'ATR' not in self.df or self.df['ATR'].isna().all():
            return None, None, None

        atr = self.df['ATR'].iloc[-1]
        price = self.df['price'].iloc[-1]
        if pd.isna(atr) or pd.isna(price):
            return None, None, None

        if direction == 'BUY':
            sl = price - atr * risk_mult
            tp = price + atr * reward_mult
        else:  # SELL
            sl = price + atr * risk_mult
            tp = price - atr * reward_mult

        risk = abs(price - sl)
        reward = abs(tp - price)
        rr = reward / risk if risk > 0 else 0

        return int(sl), int(tp), round(rr, 2)
