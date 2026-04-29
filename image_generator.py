import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
import os

# ---------------------------------------------------
# RENKLER
# RGB formatı: (Kırmızı, Yeşil, Mavi) — 0-255 arası
# ---------------------------------------------------
KIRMIZI = (200, 30, 30)
KOYU_KIRMIZI = (150, 15, 15)
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
SEFFAF_SIYAH = (0, 0, 0, 180)  # 4. değer: saydamlık (0=tam şeffaf, 255=tam opak)

# ---------------------------------------------------
# BOYUTLAR
# Instagram kare formatı: 1080x1080 piksel
# ---------------------------------------------------
GENISLIK = 1080
YUKSEKLIK = 1080


def gorsel_indir(url):
    """
    URL'den görsel indirir ve PIL Image olarak döndürür.
    Başarısız olursa None döndürür.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        return img
    except Exception as e:
        print(f"Görsel indirme hatası: {e}")
        return None


def font_yukle(boyut, kalin=False):
    """
    Sisteme uygun font yükler.
    Windows ve Linux için farklı font yolları dener.
    """
    # Windows font yolları
    windows_fontlar = [
        f"C:/Windows/Fonts/{'arialbd' if kalin else 'arial'}.ttf",
        f"C:/Windows/Fonts/{'calibrib' if kalin else 'calibri'}.ttf",
    ]
    # Linux font yolları (GitHub Actions Linux kullanır)
    linux_fontlar = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if kalin else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans{'-Bold' if kalin else ''}.ttf",
    ]

    for font_yolu in windows_fontlar + linux_fontlar:
        try:
            return ImageFont.truetype(font_yolu, boyut)
        except:
            continue

    # Hiçbiri bulunamazsa varsayılan font
    print("Uyarı: Sistem fontu bulunamadı, varsayılan kullanılıyor.")
    return ImageFont.load_default()


def metin_sar(metin, max_karakter):
    """
    Uzun metni belirli karakter sayısında satırlara böler.
    Türkçe karakterleri destekler.
    """
    return textwrap.wrap(metin, width=max_karakter)


def haber_gorseli_olustur(baslik, aciklama, kaynak, gorsel_url=None):
    """
    Ana fonksiyon — haber kartı görselini oluşturur.

    Parametreler:
    baslik      → haberin başlığı (h1 + h2 olarak ikiye bölünecek)
    aciklama    → haberin kısa açıklaması
    kaynak      → hangi siteden geldi (örn: Çanakkale Haber)
    gorsel_url  → arka plan görseli URL'si (yoksa düz renk kullanılır)

    Döndürür:
    output_path → oluşturulan görselin bilgisayardaki yolu
    """

    # ---------------------------------------------------
    # 1. ADIM: CANVAS OLUŞTUR (boş tuval)
    # RGBA = Red, Green, Blue, Alpha (saydamlık)
    # ---------------------------------------------------
    canvas = Image.new("RGBA", (GENISLIK, YUKSEKLIK), (*SIYAH, 255))

    # ---------------------------------------------------
    # 2. ADIM: ARKA PLAN GÖRSELİ
    # ---------------------------------------------------
    if gorsel_url:
        arka_plan = gorsel_indir(gorsel_url)
        if arka_plan:
            # Görseli 1080x1080'e sığdır (kırparak)
            arka_plan = arka_plan.resize((GENISLIK, YUKSEKLIK), Image.LANCZOS)
            canvas.paste(arka_plan, (0, 0))

    # Üstüne koyu yarı şeffaf katman ekle (metinler okunabilsin)
    karanlik_katman = Image.new("RGBA", (GENISLIK, YUKSEKLIK), SEFFAF_SIYAH)
    canvas.paste(karanlik_katman, (0, 0), karanlik_katman)

    # ---------------------------------------------------
    # 3. ADIM: SOL KIRMIZI ÇUBUK + ÇANAKKALE YAZISI
    # ---------------------------------------------------
    draw = ImageDraw.Draw(canvas)

    # Kırmızı dikey çubuk (sol kenar)
    draw.rectangle([30, 0, 65, YUKSEKLIK], fill=KIRMIZI)

    # ÇANAKKALE yazısını dikey yaz
    font_dikey = font_yukle(28, kalin=True)

    # Yazıyı önce yatay oluştur, sonra döndür
    dikey_yazi = Image.new("RGBA", (400, 40), (0, 0, 0, 0))
    dikey_draw = ImageDraw.Draw(dikey_yazi)
    dikey_draw.text((10, 10), "ÇANAKKALE", font=font_dikey, fill=BEYAZ)
    dikey_yazi = dikey_yazi.rotate(90, expand=True)  # 90 derece döndür
    canvas.paste(dikey_yazi, (5, 230), dikey_yazi)  # Sol çubuğa yapıştır

    # ---------------------------------------------------
    # 4. ADIM: LOGO ALANI (sağ üst köşe)
    # Şimdilik metin olarak yazıyoruz
    # ---------------------------------------------------
    font_logo = font_yukle(28, kalin=True)
    draw.text((GENISLIK - 220, 30), "ÇANAKKALE", font=font_logo, fill=BEYAZ)
    draw.text((GENISLIK - 180, 65), "ANLIK", font=font_logo, fill=KIRMIZI)

    # ---------------------------------------------------
    # 5. ADIM: BAŞLIK KUTULARI
    # ---------------------------------------------------
    font_h1 = font_yukle(52, kalin=True)
    font_h2 = font_yukle(44, kalin=True)
    font_aciklama = font_yukle(32, kalin=False)
    font_kaynak = font_yukle(26, kalin=False)

    # Başlığı ikiye böl
    kelimeler = baslik.split()
    orta = len(kelimeler) // 2
    h1 = " ".join(kelimeler[:orta]).upper()
    h2 = " ".join(kelimeler[orta:]).upper()

    # Alt bölümün başlangıç noktası
    alt_y = YUKSEKLIK - 420
    sol_x = 85
    sag_x = GENISLIK - 40

    # H1 kutusu — beyaz arka plan, kırmızı yazı
    draw.rectangle([sol_x, alt_y, sag_x, alt_y + 85], fill=BEYAZ)
    draw.text((sol_x + 15, alt_y + 15), h1[:35], font=font_h1, fill=KIRMIZI)

    # H2 kutusu — kırmızı arka plan, beyaz yazı
    draw.rectangle([sol_x, alt_y + 90, sag_x, alt_y + 170], fill=KIRMIZI)
    draw.text((sol_x + 15, alt_y + 100), h2[:35], font=font_h2, fill=BEYAZ)

    # ---------------------------------------------------
    # 6. ADIM: AÇIKLAMA METNİ
    # ---------------------------------------------------
    if aciklama:
        satirlar = metin_sar(aciklama[:250], max_karakter=45)
        metin_y = alt_y + 185
        for satir in satirlar[:5]:  # En fazla 5 satır
            draw.text((sol_x, metin_y), satir, font=font_aciklama, fill=BEYAZ)
            metin_y += 42  # Satır aralığı

    # ---------------------------------------------------
    # 7. ADIM: KAYNAK BİLGİSİ (alt köşe)
    # ---------------------------------------------------
    draw.text(
        (sol_x, YUKSEKLIK - 50),
        f"Kaynak: {kaynak}",
        font=font_kaynak,
        fill=(180, 180, 180)  # Açık gri
    )

    # ---------------------------------------------------
    # 8. ADIM: GÖRSELİ KAYDET
    # ---------------------------------------------------
    output_path = "test_haber.png"
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Görsel oluşturuldu: {output_path}")
    return output_path


# ---------------------------------------------------
# TEST BLOĞU
# ---------------------------------------------------
if __name__ == "__main__":
    haber_gorseli_olustur(
        baslik="Çanakkale'de Troya Maratonu heyecanı başladı",
        aciklama="Çanakkale'de düzenlenen Troya Maratonu'na bu yıl binlerce sporcu katıldı.",
        kaynak="Çanakkale Haber",
        gorsel_url=None  # Şimdilik boş, düz siyah arka plan kullanılacak
    )