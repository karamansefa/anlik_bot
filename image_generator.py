import os
import threading
import urllib.parse
import http.server
from playwright.sync_api import sync_playwright

# ---------------------------------------------------
# AYARLAR
# ---------------------------------------------------

# HTML şablonunun bulunduğu klasör
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Görselin kaydedileceği yol
OUTPUT_PATH = os.path.join(BASE_DIR, "haber_gorseli.png")

# Sunucu portu
PORT = 8765


# ---------------------------------------------------
# SUNUCU
# ---------------------------------------------------

class SilentHandler(http.server.SimpleHTTPRequestHandler):
    """
    Sessiz HTTP sunucusu.
    Normalde her istek terminale yazdırılır.
    Biz bunu istemiyoruz — log mesajlarını gizliyoruz.
    """
    def log_message(self, format, *args):
        pass  # Hiçbir şey yazdırma

    def log_error(self, format, *args):
        pass  # Hataları da gizle


def start_server():
    """
    Arka planda HTTP sunucusu başlatır.
    Bu sunucu HTML şablonunu Playwright'a sunar.
    """
    os.chdir(BASE_DIR)  # Doğru klasörde çalış
    server = http.server.HTTPServer(("localhost", PORT), SilentHandler)
    # daemon=True → Ana program bitince sunucu da biter
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server


# ---------------------------------------------------
# ANA FONKSİYON
# ---------------------------------------------------

def create_news_image(title, description, source, image_url=None, category=""):
    """
    Haber görseli oluşturur.

    Parametreler:
    title       → haberin başlığı
    description → haberin kısa açıklaması  
    source      → kaynak site adı
    image_url   → arka plan görseli URL'si (opsiyonel)
    category    → haber kategorisi (TRAFİK, ASAYİŞ vb.)

    Döndürür:
    output_path → oluşturulan görselin yolu
    """

    # ---------------------------------------------------
    # 1. ADIM: Başlığı ikiye böl (h1 ve h2)
    # ---------------------------------------------------
    # Örnek: "Çanakkale'de trafik sorunu devam ediyor"
    # h1 → "ÇANAKKALE'DE TRAFİK SORUNU"
    # h2 → "DEVAM EDİYOR"
    words = title.split()
    mid = len(words) // 2
    h1 = " ".join(words[:mid]).upper()
    h2 = " ".join(words[mid:]).upper()

    # ---------------------------------------------------
    # 2. ADIM: URL parametrelerini hazırla
    # ---------------------------------------------------
    params = urllib.parse.urlencode({
        "h1": h1,
        "h2": h2,
        "desc": description[:200] if description else "",
        "cat": category,
        "img": image_url or ""
    })

    url = f"http://localhost:{PORT}/canakkale-anlik.html?{params}"

    # ---------------------------------------------------
    # 3. ADIM: Playwright ile ekran görüntüsü al
    # ---------------------------------------------------
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Arka planda çalış
        page = browser.new_page()
        page.set_viewport_size({"width": 540, "height": 1200})

        # Sayfayı aç, ağ trafiği durene kadar bekle
        page.goto(url, wait_until="networkidle")

        # Canvas çizimi için ekstra bekle
        page.wait_for_timeout(1500)

        # Sadece canvas elementini yakala
        page.locator("canvas").screenshot(path=OUTPUT_PATH)

        browser.close()

    print(f"Görsel oluşturuldu: {OUTPUT_PATH}")
    return OUTPUT_PATH


# ---------------------------------------------------
# TEST BLOĞU
# ---------------------------------------------------
if __name__ == "__main__":
    # Sunucuyu başlat
    server = start_server()
    print(f"Sunucu başladı: http://localhost:{PORT}")

    # Test
    path = create_news_image(
        title="Çanakkale'de Troya Maratonu heyecanı başladı",
        description="Çanakkale'de düzenlenen Troya Maratonu'na bu yıl binlerce sporcu katıldı.",
        source="Çanakkale Haber",
        category="ETKİNLİK"
    )

    print(f"Test tamamlandı: {path}")
    server.shutdown()