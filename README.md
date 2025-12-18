# 📈 BIST ALIM SATIM STRATEJİ

BIST 100 hisselerini otomatik olarak tarayan, 21/55 EMA pullback stratejisine göre alım sinyalleri bulan web uygulaması.

## 🎯 Özellikler

- **Otomatik Periyodik Tarama**: 5-60 dakika aralıklarla otomatik tarama
- **Strateji Kuralları**:
  - 21 EMA > 55 EMA (Trend)
  - Fiyat 21 EMA'ya geri çekilme (Pullback)
  - Heikin Ashi mumunun yeşile dönmesi (Sinyal)
- **İnteraktif Grafikler**: Plotly ile detaylı analiz
- **Türkçe Arayüz**: Tam Türkçe kullanıcı deneyimi

## 🚀 Lokal Kurulum

```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
streamlit run main.py
```

Tarayıcınızda `http://localhost:8501` açılacaktır.

## 🌐 Online Kullanım

Bu uygulama Streamlit Cloud üzerinde yayınlanabilir:

1. Bu repository'yi GitHub'a yükleyin
2. [Streamlit Cloud](https://streamlit.io/cloud)'a gidin
3. Repository'nizi bağlayın
4. `main.py` dosyasını seçin
5. Deploy!

## 📊 Kullanım

1. **Otomatik Tarama**: Sol menüden "Otomatik Tarama Aktif" seçeneğini açın
2. **Tarama Aralığı**: İstediğiniz süreyi seçin (5, 10, 15, 30, 60 dakika)
3. **Manuel Tarama**: "Manuel Tarama Yap" butonu ile anında tarayın
4. **Grafik Görüntüleme**: Bulunan hisseleri seçerek detaylı analiz edin

## 🛠️ Teknolojiler

- **Streamlit** - Web framework
- **yfinance** - BIST verileri
- **Pandas** - Veri işleme
- **Plotly** - İnteraktif grafikler

## 📝 Lisans

MIT License - Ticari ve kişisel kullanım için özgür.
