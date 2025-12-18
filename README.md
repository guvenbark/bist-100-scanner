# 📈 BIST TARAMA VE ANALİZ ARACI

BIST 100 hisselerini teknik göstergelere göre tarayan, yatırım kararlarınızı destekleyen bir analiz aracı.

## ⚠️ ÖNEMLİ UYARI

Bu araç bir **karar destek sistemi**dir. Yatırım tavsiyesi değildir.
- ✅ Teknik göstergelere göre sinyaller sunar
- ✅ Backtest sonuçlarını gösterir
- ❌ Otomatik alım satım yapmaz
- ❌ Garanti kar vaat etmez

**Risk Uyarısı:** Geçmiş performans gelecek getiriyi garanti etmez. Yatırım kararlarınızı profesyonel danışmanlık alarak veriniz.

## 🎯 Özellikler

- **3 Farklı Strateji:**
  - 21/55 EMA & Heikin Ashi (Trend Takip)
  - RSI V2 (Filtreli Momentum)
  - RSI V3 (Kar Optimizasyonu - ADX + Trailing Stop)

- **Otomatik Periyodik Tarama**: 5-60 dakika aralıklarla
- **İnteraktif Grafikler**: Plotly ile detaylı analiz
- **Backtest Sonuçları**: Geçmiş performans görüntüleme
- **Türkçe Arayüz**: Tam Türkçe destek

## 🚀 Lokal Kurulum

```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
streamlit run main.py
```

Tarayıcınızda `http://localhost:8501` açılacaktır.

## 📊 Kullanım

1. Sol menüden **strateji seçin**
2. **Manuel Tarama** yapın veya otomatik taramayı aktif edin
3. Bulunan sinyalleri **kendi analizinizle** birleştirin
4. **Kendi risk yönetiminize** göre karar verin

## 🛠️ Teknolojiler

- **Streamlit** - Web framework
- **yfinance** - BIST verileri
- **Pandas** - Veri işleme
- **Plotly** - İnteraktif grafikler

## 📈 Backtest Sonuçları Hakkında

Sistemde bulunan backtest sonuçları **geçmiş simülasyonlardır**:
- Gerçek ticaret sonuçları değildir
- Slippage, komisyon içermez
- Risk yönetimi kullanıcıya aittir

**Ortalama Performans:** Test edilen hisselerde %0-20 aralığında değişken getiriler

## 📝 Lisans

MIT License - Eğitim ve araştırma amaçlıdır.
