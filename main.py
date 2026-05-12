import json
import os
from collections import defaultdict
from scraper import get_all_news, get_article_detail
from image_generator import create_news_image, start_server
from telegram_sender import send_photo, send_message
from config import CATEGORY_RULES, DEFAULT_CATEGORY, MAX_NEWS_PER_RUN, SERVER_PORT
from rewriter import rewrite_news

# ---------------------------------------------------
# AYARLAR
# ---------------------------------------------------
SENT_FILE = "sent_news.json"


def sent_news_oku():
    """
    Daha önce gönderilen haberlerin URL listesini dosyadan okur.
    Dosya yoksa boş liste döndürür.
    """
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Uyarı: sent_news.json bozuk, sıfırlanıyor.")
        return []


def sent_news_kaydet(liste):
    """
    Gönderilen URL listesini dosyaya kaydeder.
    500'den fazla URL birikirse eskilerini siler.
    """
    if len(liste) > 500:
        liste = liste[-500:]

    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)


def determine_category(title):
    """
    Haber başlığına göre kategori belirler.
    Hiçbir kategoriye uymuyorsa DEFAULT_CATEGORY döner.
    """
    t = title.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in t for k in keywords):
            return category
    return DEFAULT_CATEGORY


def gonderilecek_haberleri_sec(yeni_haberler):
    """
    Gönderilecek haberleri seçer.

    1. TUR: Her siteden 1'er haber al
    2. TUR: Slot dolmadıysa kalan haberlerle tamamla

    Örnek:
    - 3 siteden haber var → her birinden 1 = 3 haber
    - 1 siteden haber var → o siteden 3 haber
    """
    site_counts = defaultdict(int)
    gonderilecekler = []

    # 1. TUR: Her siteden 1'er haber al
    for haber in yeni_haberler:
        site = haber["source"]
        if site_counts[site] < 1 and len(gonderilecekler) < MAX_NEWS_PER_RUN:
            gonderilecekler.append(haber)
            site_counts[site] += 1

    # 2. TUR: Slot dolmadıysa kalan haberleri ekle
    if len(gonderilecekler) < MAX_NEWS_PER_RUN:
        for haber in yeni_haberler:
            if len(gonderilecekler) >= MAX_NEWS_PER_RUN:
                break
            if haber not in gonderilecekler:
                gonderilecekler.append(haber)

    return gonderilecekler


def main():
    print("=" * 50)
    server = start_server()
    print("Sunucu başladı")
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
        server.shutdown()
        return

    # ---------------------------------------------------
    # 4. ADIM: Gönderilecek haberleri seç
    # ---------------------------------------------------
    gonderilecekler = gonderilecek_haberleri_sec(yeni_haberler)
    gonderilen_count = 0

    for haber in gonderilecekler:
        print(f"\nİşleniyor: {haber['title'][:50]}...")

        # Haberin detayını çek
        detay = get_article_detail(haber["url"])

        # Haberi yeniden yaz
        print(f"  Yeniden yazılıyor...")
        yeni_baslik, yeni_aciklama = rewrite_news(
            haber["title"],
            detay["description"]
        )
        print(f"  Yeni başlık: {yeni_baslik[:50]}...")

        # Görseli oluştur
        gorsel_yolu = create_news_image(
            title=yeni_baslik,
            description=yeni_aciklama,
            source=haber["source"],
            image_url=detay["image_url"],
            category=determine_category(haber["title"])
        )

        # Telegram mesajını hazırla
        caption = (
            f"<b>{yeni_baslik}</b>\n\n"
            f"{yeni_aciklama}\n\n"
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
    server.shutdown()


# ---------------------------------------------------
# BAŞLANGIÇ NOKTASI
# ---------------------------------------------------
if __name__ == "__main__":
    main()