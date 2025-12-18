# 🚀 Streamlit Cloud Deployment Rehberi

## Adım 1: GitHub'a Yükleme

### A) GitHub Hesabınız Yoksa
1. [github.com](https://github.com) - Ücretsiz hesap açın

### B) Repository Oluşturma
1. GitHub'da "New Repository" tıklayın
2. İsim: `bist-100-scanner` (veya istediğiniz isim)
3. Public olarak oluşturun
4. "Create repository" tıklayın

### C) Kodları Yükleme

Terminal'de şu komutları çalıştırın:

```bash
# Git başlat
cd c:/Users/guvenba/.gemini/antigravity/playground/static-galileo
git init

# Dosyaları ekle
git add .
git commit -m "Initial commit - BIST 100 Scanner"

# GitHub'a bağla (USERNAME ve REPO_NAME'i kendi bilgilerinizle değiştirin)
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Adım 2: Streamlit Cloud'a Deploy

1. **Streamlit Cloud'a Git**: [share.streamlit.io](https://share.streamlit.io)

2. **GitHub ile Giriş Yapın**

3. **"New app" Tıklayın**

4. **Ayarları Yapın**:
   - Repository: `USERNAME/bist-100-scanner`
   - Branch: `main`
   - Main file path: `main.py`

5. **"Deploy!" Tıklayın**

6. **Bekleyin**: 2-3 dakika içinde uygulamanız yayında!

## ✅ Tamamlandı!

Uygulamanız artık `https://USERNAME-bist-100-scanner.streamlit.app` adresinde yayında!

## 🔧 Güncellemeler

Kod değişikliklerinizi GitHub'a push ettiğinizde, Streamlit Cloud otomatik olarak günceller:

```bash
git add .
git commit -m "Güncelleme açıklaması"
git push
```

## ⚡ Hızlı Deploy Alternatifi

GitHub kullanmak istemiyorsanız:

### Render.com ile Deploy

1. [render.com](https://render.com) - Ücretsiz hesap
2. "New Web Service" → Connect GitHub (veya Manuel Deploy)
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run main.py --server.port=$PORT --server.address=0.0.0.0`

## 💡 İpuçları

- **Ücretsiz Limit**: Streamlit Cloud ücretsiz planda 1 app yayınlayabilirsiniz
- **Uyku Modu**: 7 gün kullanılmazsa uyur (ilk açılış biraz yavaş olur)
- **Private App**: Ayarlardan sadece kendinizin erişebileceği şekilde yapabilirsiniz

## 🆘 Sorun mu var?

Deployment sırasında hata alırsanız:
1. `requirements.txt` dosyasını kontrol edin
2. Streamlit Cloud loglarına bakın
3. GitHub repository'nin public olduğundan emin olun
