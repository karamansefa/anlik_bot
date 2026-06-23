import os
import threading
import urllib.parse
import http.server
import urllib.parse as url_parse
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "haber_gorseli.png")
BG_PATH = os.path.join(BASE_DIR, "haber_gorseli_bg.png")
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


def gorsel_olustur(prompt):
    """
    Stability AI ile görsel üretir.
    Ücretsiz 25 kredi ile başlar.
    """
    import requests as req

    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
    print(f"  DEBUG key uzunluk: {len(STABILITY_API_KEY) if STABILITY_API_KEY else 0}")
    print(f"  DEBUG key repr: {repr(STABILITY_API_KEY)}")
    

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*"
    }

    body = {
        "prompt": prompt,
        "output_format": "png",
        "width": 1024,
        "height": 1024,
    }

    try:
        response = req.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers=headers,
            files={"none": ""},
            data=body,
            timeout=60
        )

        if response.status_code == 200:
            with open(BG_PATH, "wb") as f:
                f.write(response.content)
            print(f"  AI görsel oluşturuldu: {BG_PATH}")
            return BG_PATH
        else:
            print(f"  Stability hatası: {response.status_code} - {response.text[:100]}")
            return None

    except Exception as e:
        print(f"  Görsel üretim hatası: {e}")
        return None

def turkce_buyut(text):
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
    for isaret in [".", "!", "?"]:
        son = metin.rfind(isaret)
        if son > 0:
            return metin[:son + 1]
    return metin


def create_news_image(title, description, source, image_prompt="", category=""):
    """
    Haber görseli oluşturur.
    title        → haberin başlığı
    description  → haberin kısa açıklaması
    source       → kaynak site adı
    image_prompt → AI görsel prompt'u (Hugging Face'e gönderilir)
    category     → haber kategorisi
    """
    # Başlığı ikiye böl
    words = title.split()
    mid = len(words) // 2
    h1 = turkce_buyut(" ".join(words[:mid]))
    h2 = turkce_buyut(" ".join(words[mid:]))

    # Açıklamayı son tam cümlede kes
    temiz_aciklama = _son_cumlede_kes(description) if description else ""

    # AI görsel üret
    bg_path = None
    if image_prompt:
        bg_path = gorsel_olustur(image_prompt)

    params = urllib.parse.urlencode({
        "h1": h1,
        "h2": h2,
        "desc": temiz_aciklama,
        "cat": category,
        "img": f"http://localhost:{PORT}/haber_gorseli_bg.png" if bg_path else ""
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
        image_prompt="marathon runners on a coastal road Turkey Canakkale photorealistic",
        category="ETKİNLİK"
    )

    print(f"Test tamamlandı: {path}")
    server.shutdown()