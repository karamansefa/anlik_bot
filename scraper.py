import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from config import SITES

# ---------------------------------------------------
# AYARLAR
# ---------------------------------------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_AGE_HOURS = 1  # Kaç saatlik haberleri al


# ---------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------

def parse_date(date_str):
    """
    RSS tarih formatını Python datetime objesine çevirir.
    Örnek: "Mon, 11 May 2026 14:03:20 +0300" → datetime objesi
    """
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def is_recent(date_str, max_hours=MAX_AGE_HOURS):
    """
    Haberin son max_hours saat içinde yayınlanıp yayınlanmadığını kontrol eder.
    """
    pub_date = parse_date(date_str)
    if not pub_date:
        return True  # Tarih yoksa haberi al (güvenli taraf)

    now = datetime.now(timezone.utc)
    age_hours = (now - pub_date).total_seconds() / 3600
    return age_hours <= max_hours


def get_rss_url(site):
    """
    Sitenin RSS URL'sini döndürür.
    config.py'de rss_url varsa onu, yoksa base_url/rss kullanır.
    """
    return site.get("rss_url", site["base_url"] + "/rss")


# ---------------------------------------------------
# HABER ÇEKME FONKSİYONLARI
# ---------------------------------------------------

def fetch_rss(site):
    """
    Bir sitenin RSS feed'ini çeker ve haberleri döndürür.
    """
    news_list = []
    rss_url = get_rss_url(site)

    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")

        for item in items:
            title = item.find("title")
            link = item.find("link")
            description = item.find("description")
            pub_date = item.find("pubDate")
            image = item.find("image") or item.find("enclosure")
            category = item.find("category")

            # Başlık ve link zorunlu
            if not title or not link:
                continue

            title_text = title.get_text(strip=True)
            link_text = link.get_text(strip=True)
            pub_date_text = pub_date.get_text(strip=True) if pub_date else ""

            # Çok kısa başlıkları atla
            if len(title_text) < 10:
                continue

            # Tarih filtresi — eski haberleri atla
            if pub_date_text and not is_recent(pub_date_text):
                continue

            # Görsel URL'si
            image_url = None
            if image:
                image_url = image.get("url") or image.get_text(strip=True)

            news_list.append({
                "title": title_text,
                "url": link_text,
                "source": site["name"],
                "description": description.get_text(strip=True)[:300] if description else "",
                "image_url": image_url,
                "pub_date": pub_date_text,
                "category": category.get_text(strip=True) if category else ""
            })

    except Exception as e:
        print(f"RSS hatası ({site['name']}): {e}")

    return news_list


def get_article_detail(url):
    """
    Geriye dönük uyumluluk için korundu.
    RSS'den gelen haberler zaten description ve image içeriyor.
    Ancak RSS'de eksik bilgi varsa sayfadan çeker.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        image_url = None
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content")

        description = ""
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                description = text[:300]
                break

        return {"image_url": image_url, "description": description}

    except Exception as e:
        print(f"Detay hatası ({url}): {e}")
        return {"image_url": None, "description": ""}


def get_all_news():
    """
    Tüm sitelerden haberleri RSS üzerinden toplar.
    """
    all_news = []

    for site in SITES:
        print(f"Taranıyor: {site['name']}...")
        news = fetch_rss(site)
        all_news.extend(news)
        print(f"  → {len(news)} haber bulundu")

    print(f"\nToplam: {len(all_news)} haber")
    return all_news


# ---------------------------------------------------
# TEST BLOĞU
# ---------------------------------------------------
if __name__ == "__main__":
    haberler = get_all_news()
    print("\n--- İLK 3 HABER ---")
    for haber in haberler[:3]:
        print(f"Başlık: {haber['title']}")
        print(f"Tarih:  {haber['pub_date']}")
        print(f"Kaynak: {haber['source']}")
        print(f"Görsel: {haber['image_url']}")
        print("---")