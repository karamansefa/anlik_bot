import json
import os
import re
from collections import defaultdict
from scraper import get_all_news, get_article_detail
from image_generator import create_news_image, start_server
from telegram_sender import send_photo, send_message
from config import CATEGORY_RULES, DEFAULT_CATEGORY, MAX_NEWS_PER_RUN, SERVER_PORT
from rewriter import rewrite_news, generate_image_prompt

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


def determine_category(title, description=""):
    """
    Haber başlığı ve açıklamasına göre kategori belirler.
    Tam kelime eşleşmesi kullanır — 'kar' kelimesi
    'kariyer' içinde eşleşmez.
    """
    t = (title + " " + description).lower()

    for category, keywords in CATEGORY_RULES.items():
        for kelime in keywords:
            pattern = r'\b' + re.escape(kelime) + r'\b'
            if re.search(pattern, t):
                return category

    return DEFAULT_CATEGORY


def groq_category(title, description=""):
    """
    Groq API ile haber kategorisi belirler.
    Sadece determine_category() GÜNDEM döndürdüğünde çağrılır.
    """
    from rewriter import GROQ_API_KEY
    import requests

    prompt = f"""Aşağıdaki Türkçe haberi EN UYGUN kategoriye yerleştir.

KATEGORİLER VE ANLAMLARI:
- TRAFİK: trafik kazası, yol çalışması, araç kazası
- HAVA: hava durumu, yağış, fırtına, deprem
- ASAYİŞ: suç, hırsızlık, uyuşturucu, operasyon, tutuklama
- SPOR: futbol, basketbol, maç, turnuva, spor müsabakası
- ETKİNLİK: konser, festival, sergi, tören, kutlama
- DUYURU: belediye kararı, ihale, resmi açıklama
- KÜLTÜR: sanat, müze, tarih, edebiyat
- EĞİTİM: okul, üniversite, öğrenci, eğitim, kurs
- GÜNDEM: diğer haberler

Sadece kategori adını yaz, başka hiçbir şey yazma.

Başlık: {title}
Açıklama: {description}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Sen Türkçe haber kategorilendiren bir asistansın. Sadece kategori adını yaz."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=10
        )
        data = response.json()
        kategori = data["choices"][0]["message"]["content"].strip().upper()

        gecerli_kategoriler = list(CATEGORY_RULES.keys()) + ["GÜNDEM"]
        if kategori in gecerli_kategoriler:
            return kategori
        return DEFAULT_CATEGORY

    except Exception as e:
        print(f"  Groq kategori hatası: {e}")
        return DEFAULT_CATEGORY


def get_category(title, description=""):
    """
    Hibrit kategori belirleme fonksiyonu.
    1. Önce manuel liste ile dene
    2. GÜNDEM dönerse → Groq'a sor
    3. Groq da GÜNDEM dönerse → GÜNDEM kalsın
    """
    manuel_kategori = determine_category(title, description)

    if manuel_kategori == DEFAULT_CATEGORY:
        print(f"  Kategori belirsiz, AI'ya soruluyor...")
        return groq_category(title, description)

    return manuel_kategori


def gonderilecek_haberleri_sec(yeni_haberler):
    """
    Gönderilecek haberleri seçer.
    1. TUR: Her siteden 1'er haber al
    2. TUR: Slot dolmadıysa kalan haberlerle tamamla
    """
    site_counts = defaultdict(int)
    gonderilecekler = []

    for haber in yeni_haberler:
        site = haber["source"]
        if site_counts[site] < 1 and len(gonderilecekler) < MAX_NEWS_PER_RUN:
            gonderilecekler.append(haber)
            site_counts[site] += 1

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

        # Kategoriyi belirle — hem görsel hem şablon için kullanılır
        kategori = get_category(haber["title"], detay["description"])

        # Görsel prompt üret
        gorsel_prompt = generate_image_prompt(yeni_baslik, kategori)

        # Görseli oluştur
        gorsel_yolu = create_news_image(
            title=yeni_baslik,
            description=yeni_aciklama,
            source=haber["source"],
            image_prompt=gorsel_prompt,
            category=kategori
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