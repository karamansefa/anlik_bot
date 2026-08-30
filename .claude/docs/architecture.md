# Çanakkale Anlık Haber Botu — Mimari Notlar

## Mevcut Akış
RSS/kaynak haber → `rewrite_news()` (Groq openai/gpt-oss-20b) ile TR başlık/açıklama yeniden yazımı → `generate_image_prompt()` (aynı model) ile İngilizce görsel prompt üretimi → Pollinations.ai (model=flux-realism) ile görsel → PIL/tasarım şablonu üzerine bindirme.

## Aktif Servisler
- **LLM:** Groq API, model: `openai/gpt-oss-20b`
- **Görsel:** Pollinations.ai, model: `flux-realism`
- **CI/CD:** GitHub Actions (public repo, sınırsız dakika)
- **Mesajlaşma:** Telegram Bot API

## Mimari Kararlar

### 1. Kategori Bazlı Routing — STATİK vs DİNAMİK
- **STATİK** (Pollinations'a hiç gidilmez): resmi tatiller, dini/milli bayramlar, hava durumu, eczane nöbetçi
- **DİNAMİK** (Groq + Pollinations): trafik, asayiş, yangın, spor, etkinlik, eğitim, kültür, duyuru
- Uygulama: `config.py`'de `STATIC_CATEGORIES` set'i + `STATIC_IMAGE_POOL` dict'i

### 2. Lokasyon Doğruluğu — Gerçekçi Sınır
Diffusion modelleri Biga/Ayvacık gibi ilçeleri görsel olarak bilemez. Görsel işi sadece olay atmosferini vermek. Yer bilgisi şablonun başlık metninde zaten var.
- **Kısa vade:** kategori bazlı fallback promptlar
- **Orta vade:** ilçe bazlı küratörlü fotoğraf + PIL ikon bindirme
- **Kural:** metin/harf asla görsele bastırılmaz (diffusion modelleri yazıyı güvenilir basamaz)

### 3. LLM Çıktı Sağlamlığı
Şu an `line.startswith("BAŞLIK:")` ile parse ediliyor — kırılgan. Groq `openai/gpt-oss-20b` strict JSON schema mode destekliyor. Geçiş yapılacak:
```python
"response_format": {
    "type": "json_schema",
    "json_schema": {
        "name": "rewritten_news",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "baslik": {"type": "string"},
                "aciklama": {"type": "string"}
            },
            "required": ["baslik", "aciklama"],
            "additionalProperties": False
        }
    }
}
```

### 4. Pollinations.ai Parametreleri

Endpoint: `GET https://image.pollinations.ai/prompt/{prompt}`

Parametreler: `model`, `width`, `height`, `seed`, `nologo`, `enhance`, `private`, `referrer`

Rate limit:
- Anonim: 15sn/istek
- Seed tier (ücretsiz kayıt): 5sn/istek + filigransız

Kayıt: `auth.pollinations.ai` — 31 Mart 2025 sonrası kayıtsız kullanımda filigran riski var.


### 5. Türkçe'ye Özgü Tuzak
`str.upper()/.lower()` Türkçe I/İ/ı/i harflerini yanlış çevirir. İlçe adı eşleştirmesinde manuel karakter haritası kullan.

## Önerilen Geliştirme Sırası
1. JSON schema mode geçişi (yüksek etki, düşük risk)
2. Kategori routing — statik/dinamik ayrımı
3. Pollinations Seed tier kaydı + parametre ayarları
4. Lokasyon hibrit yaklaşımı
5. `tenacity` retry, `logging`, cache ile sağlamlaştırma

## Öğrenme Notları
- **24.06.2026:** GitHub Secrets'a key eklemek yetmez; `haber.yml` workflow'undaki `env:` bloğuna da satır olarak eklenmesi şart. Eksikse `os.getenv()` hep `None` döner.
- **Debug tekniği:** `repr()` + uzunluk kontrolü ile debug print — GitHub Actions loglarında key'i açığa çıkarmadan teşhis için etkili.
- **Lokal API testi:** `python -c "import requests; r = requests.post(...); print(r.status_code)"` ile GitHub Actions'ı beklemeden direkt API'yi test et.
- **Groq model değişimi:** `llama-3.3-70b-versatile` deprecated, şu an aktif: `openai/gpt-oss-20b`. Aktif modelleri görmek için: `GET https://api.groq.com/openai/v1/models`