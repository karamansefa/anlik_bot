import os
import threading
import urllib.parse
import http.server
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "haber_gorseli.png")
PORT = 8765


class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def log_error(self, format, *args):
        pass


def start_server():
    os.chdir(BASE_DIR)
    server = http.server.HTTPServer(("localhost", PORT), SilentHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server


def turkce_buyut(text):
    """
    Türkçe karakterleri doğru büyütür.
    Python upper() → 'i' = 'I' (YANLIŞ)
    Bu fonksiyon → 'i' = 'İ' (DOĞRU)
    """
    return (text
        .replace("i", "İ")
        .replace("ı", "I")
        .replace("ğ", "Ğ")
        .replace("ü", "Ü")
        .replace("ş", "Ş")
        .replace("ö", "Ö")
        .replace("ç", "Ç")
        .upper()
    )


def _son_cumlede_kes(metin):
    """
    Metni son tam cümlede keser.
    Nokta, ünlem veya soru işaretinde biter.
    Bitmiyorsa olduğu gibi döner.
    """
    for isaret in [".", "!", "?"]:
        son = metin.rfind(isaret)
        if son > 0:
            return metin[:son + 1]
    return metin


def create_news_image(title, description, source, image_url=None, category=""):
    """
    Haber görseli oluşturur.
    title       → haberin başlığı
    description → haberin kısa açıklaması
    source      → kaynak site adı
    image_url   → arka plan görseli URL'si (opsiyonel)
    category    → haber kategorisi
    """
    # Başlığı ikiye böl
    words = title.split()
    mid = len(words) // 2
    h1 = turkce_buyut(" ".join(words[:mid]))
    h2 = turkce_buyut(" ".join(words[mid:]))

    # Açıklamayı son tam cümlede kes
    temiz_aciklama = _son_cumlede_kes(description) if description else ""

    params = urllib.parse.urlencode({
        "h1": h1,
        "h2": h2,
        "desc": temiz_aciklama,
        "cat": category,
        "img": image_url or ""
    })

    url = f"http://localhost:{PORT}/canakkale-anlik.html?{params}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1000, "height": 1800},
            device_scale_factor=2
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.locator("canvas").screenshot(path=OUTPUT_PATH)
        browser.close()

    print(f"Görsel oluşturuldu: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    server = start_server()
    print(f"Sunucu başladı: http://localhost:{PORT}")

    path = create_news_image(
        title="Çanakkale'de Troya Maratonu heyecanı başladı",
        description="Çanakkale'de düzenlenen Troya Maratonu'na bu yıl binlerce sporcu katıldı. Etkinlik büyük ilgi gördü.",
        source="Çanakkale Haber",
        category="ETKİNLİK"
    )

    print(f"Test tamamlandı: {path}")
    server.shutdown()