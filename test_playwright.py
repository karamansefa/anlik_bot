from playwright.sync_api import sync_playwright
import urllib.parse

# Test verisi
h1 = "ÇANAKKALE'DE TRAFİK"
h2 = "NE ZAMAN ÇÖZÜLECEK"
desc = "Adliye kavşağındaki trafik yoğunluğu devam ediyor"
cat = "TRAFİK"

# URL parametrelerini encode et
# Türkçe karakterler ve boşluklar URL'de sorun çıkarır
# urllib.parse.quote() bunları güvenli karakterlere çevirir
# Örnek: "Ç" → "%C3%87", " " → "%20"
params = urllib.parse.urlencode({
    "h1": h1,
    "h2": h2,
    "desc": desc,
    "cat": cat
})

# HTML dosyasının tam yolu
# Playwright http:// ile çalışır, file:// değil
# O yüzden Python sunucusu açıyoruz
url = f"http://localhost:8000/canakkale-anlik.html?{params}"

print(f"URL: {url}")

with sync_playwright() as p:
    # Chromium tarayıcısını aç
    # headless=True → tarayıcı ekranda görünmez, arka planda çalışır
    # headless=False → tarayıcı görünür (test için)
    browser = p.chromium.launch(headless=False)
    
    # Yeni sayfa aç
    page = browser.new_page()
    
    # Ekran boyutunu ayarla (1000x1000 Instagram kare)
    page.set_viewport_size({"width": 540, "height": 1200})
    
    # Sayfayı aç, tamamen yüklenene kadar bekle
    page.goto(url, wait_until="networkidle")
    
    # 1 saniye bekle (canvas çizimi için)
    page.wait_for_timeout(1000)
    
    # Ekran görüntüsü al
    page.locator("canvas").screenshot(path="playwright_test.png")
    
    print("Görsel oluşturuldu: playwright_test.png")
    
    browser.close()