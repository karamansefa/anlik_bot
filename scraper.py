import requests
from bs4 import BeautifulSoup
from config import SITES

# Bazı siteler bot olduğumuzu anlayıp bizi engelliyor
# Normal bir tarayıcıymış gibi davranmak için bu başlığı ekliyoruz
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def get_news_from_site(site):
    """
    Tek bir siteden haber başlıklarını ve linklerini çeker.
    site → yukarıdaki SITES listesindeki bir eleman
    """
    news_list = []  # Boş liste, bulduğumuz haberleri buraya ekleyeceğiz

    try:
        # Siteye bağlan, sayfanın HTML kodunu al
        response = requests.get(site["url"], headers=HEADERS, timeout=10)
        response.encoding = "utf-8"  # Türkçe karakterler için

        # HTML'yi BeautifulSoup ile okumaya hazır hale getir
        soup = BeautifulSoup(response.text, "html.parser")

        # Sayfadaki tüm linkleri bul
        links = soup.find_all("a", href=True)

        seen_urls = set()  # Aynı linki iki kez eklememek için

        for link in links:
            title = link.get_text(strip=True)  # Linkin yazısı (haber başlığı)
            href = link.get("href", "")         # Linkin adresi

            # Çok kısa yazılar haber başlığı değildir, atla
            if len(title) < 20:
                continue

            # Tam URL oluştur
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = site["base_url"] + href
            else:
                continue  # Geçersiz link, atla

            # Daha önce ekledik mi?
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Listeye ekle
            news_list.append({
                "title": title,
                "url": full_url,
                "source": site["name"]
            })

    except Exception as e:
        print(f"Hata ({site['name']}): {e}")

    return news_list


def get_article_detail(url):
    """
    Bir haberin detay sayfasına gider.
    Haberin görselini ve açıklama metnini çeker.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # OG Image: Sitenin sosyal medya için belirlediği ana görsel
        # Facebook, Twitter gibi platformlar bunu kullanır
        image_url = None
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content")

        # Haberin ilk paragrafını bul (açıklama olarak kullanacağız)
        description = ""
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:          # Çok kısa paragrafları atla
                description = text[:200]  # İlk 200 karakteri al
                break

        return {
            "image_url": image_url,
            "description": description
        }

    except Exception as e:
        print(f"Detay hatası ({url}): {e}")
        return {"image_url": None, "description": ""}


def get_all_news():
    """
    Tüm sitelerden haberleri toplar ve tek liste olarak döner.
    main.py bu fonksiyonu çağıracak.
    """
    all_news = []

    for site in SITES:
        print(f"Taranıyor: {site['name']}...")
        news = get_news_from_site(site)
        all_news.extend(news)  # Listeyi ana listeye ekle
        print(f"  → {len(news)} haber bulundu")

    print(f"\nToplam: {len(all_news)} haber")
    return all_news

# Bu satırlar sadece test için - dosyayı direkt çalıştırınca devreye girer
if __name__ == "__main__":
    haberler = get_all_news()
    print("\n--- İLK 3 HABER ---")
    for haber in haberler[:3]:
        print(f"Başlık: {haber['title']}")
        print(f"URL: {haber['url']}")
        print(f"Kaynak: {haber['source']}")
        print("---")