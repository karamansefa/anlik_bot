import json
import os
from scraper import get_all_news, get_article_detail
from image_generator import haber_gorseli_olustur
from telegram_sender import send_photo, send_message

# ---------------------------------------------------
# AYARLAR
# ---------------------------------------------------
SENT_FILE = "sent_news.json"   # Gönderilen haberlerin dosyası
MAX_HABER = 3                   # Her çalışmada max kaç haber gönderilsin


def sent_news_oku():
    """
    Daha önce gönderilen haberlerin URL listesini dosyadan okur.
    Dosya yoksa boş liste döndürür.
    """
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Dosya henüz yok — ilk çalışma
        return []
    except json.JSONDecodeError:
        # Dosya bozuk — boş başla
        print("Uyarı: sent_news.json bozuk, sıfırlanıyor.")
        return []


def sent_news_kaydet(liste):
    """
    Gönderilen URL listesini dosyaya kaydeder.
    500'den fazla URL birikirse eskilerini siler — dosya şişmesin.
    """
    if len(liste) > 500:
        liste = liste[-500:]  # Son 500'ü tut

    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 50)
    print("Çanakkale Anlık Haber Botu Başladı")
    print("=" * 50)

    # ---------------------------------------------------
    # 1. ADIM: Daha önce gönderilenler
    # ---------------------------------------------------
    gonderilen_urls = sent_news_oku()
    print(f"Daha önce gönderilen: {len(gonderilen_urls)} haber")

    # ---------------------------------------------------
    # 2. ADIM: Tüm sitelerden haberleri çek
    # ---------------------------------------------------
    tum_haberler = get_all_news()

    # ---------------------------------------------------
    # 3. ADIM: Yeni haberleri filtrele
    # ---------------------------------------------------
    yeni_haberler = [
        h for h in tum_haberler
        if h["url"] not in gonderilen_urls
    ]
    print(f"Yeni haber sayısı: {len(yeni_haberler)}")

    if not yeni_haberler:
        print("Yeni haber yok. Çıkılıyor.")
        return

    # ---------------------------------------------------
    # 4. ADIM: En fazla MAX_HABER kadar gönder
    # ---------------------------------------------------
    gonderilecekler = yeni_haberler[:MAX_HABER]
    gonderilen_count = 0

    for haber in gonderilecekler:
        print(f"\nİşleniyor: {haber['title'][:50]}...")

        # Haberin detayını çek (görsel + açıklama)
        detay = get_article_detail(haber["url"])

        # Görseli oluştur
        gorsel_yolu = haber_gorseli_olustur(
            baslik=haber["title"],
            aciklama=detay["description"],
            kaynak=haber["source"],
            gorsel_url=detay["image_url"]
        )

        # Telegram mesajını hazırla
        caption = (
            f"<b>{haber['title']}</b>\n\n"
            f"{detay['description']}\n\n"
            f"🔗 <a href='{haber['url']}'>Haberin tamamı</a>\n"
            f"📌 Kaynak: {haber['source']}"
        )

        # Telegram'a gönder
        sonuc = send_photo(gorsel_yolu, caption)

        if sonuc.get("ok"):
            gonderilen_urls.append(haber["url"])
            gonderilen_count += 1
            print(f"  ✅ Gönderildi!")
        else:
            print(f"  ❌ Telegram hatası: {sonuc}")

    # ---------------------------------------------------
    # 5. ADIM: Gönderilenleri kaydet
    # ---------------------------------------------------
    sent_news_kaydet(gonderilen_urls)
    print(f"\n{'=' * 50}")
    print(f"Tamamlandı! {gonderilen_count} haber gönderildi.")
    print(f"{'=' * 50}")


# ---------------------------------------------------
# BAŞLANGIÇ NOKTASI
# ---------------------------------------------------
if __name__ == "__main__":
    main()