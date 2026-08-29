import os
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def rewrite_news(title, description):
    """
    Haberi Groq API ile yeniden yazar.
    Hata durumunda orijinal haberi döndürür, bot durmaz.
    """
    prompt = f"""Sen bir Türkçe haber editörüsün. Aşağıdaki haberi SADECE TÜRKÇE olarak yeniden yaz.

KESİNLİKLE UYULMASI GEREKEN KURALLAR:
- Yabancı dil kullanma
- Uydurma bilgi ekleme
- BAŞLIK: tam olarak 6-8 kelime olmalı
- AÇIKLAMA: tam olarak 2 cümle olmalı, toplam 20-25 kelime olmalı
- Her cümle nokta ile bitmeli
- Açıklama haberin özünü yansıtmalı

Başlık: {title}
Açıklama: {description}

SADECE şu formatta yaz:
BAŞLIK: yeniden yazılmış başlık
AÇIKLAMA: yeniden yazılmış açıklama"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Sen yalnızca Türkçe konuşan bir haber editörüsün. Asla başka dil kullanma. Verilen kelime sayısı kurallarına kesinlikle uy."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=15
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"]

        lines = text.strip().split("\n")
        new_title = title
        new_description = description

        for line in lines:
            if line.startswith("BAŞLIK:"):
                new_title = line.replace("BAŞLIK:", "").strip()
            elif line.startswith("AÇIKLAMA:"):
                new_description = line.replace("AÇIKLAMA:", "").strip()

        return new_title, new_description
    
    except Exception as e:
        print(f"Groq hatası: {e}")
        print(f"Groq response: {response.text[:300] if 'response' in dir() else 'response yok'}")
        return title, description


def generate_image_prompt(title, category):
    """
    Haber başlığı ve kategorisinden İngilizce görsel prompt üretir.
    Pollinations.ai için kullanılır.

    Akış:
    Türkçe başlık → Groq → İngilizce prompt → Pollinations → Görsel
    """
    prompt_text = f"""Aşağıdaki Türkçe haber için Pollinations.ai'ye gönderilecek
bir İngilizce görsel prompt yaz.

Kurallar:
- Maksimum 10 kelime
- Fotoğraf gerçekçi tarzda olsun
- Metin, yazı, harf içermesin
- Türkiye'ye uygun görsel olsun
- Sadece prompt yaz, başka hiçbir şey yazma

Haber başlığı: {title}
Kategori: {category}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Sen görsel prompt üretiyorsun. Sadece İngilizce prompt yaz, başka hiçbir şey yazma."
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=10
        )
        data = response.json()
        prompt = data["choices"][0]["message"]["content"].strip()

        # Tırnak işaretlerini temizle
        prompt = prompt.strip('"').strip("'")
        print(f"  Görsel prompt: {prompt}")
        return prompt

    except Exception as e:
        print(f"  Prompt hatası: {e}")
        print(f"  Groq response: {response.text[:300] if 'response' in dir() else 'response yok'}")
        # Hata olursa kategori bazlı varsayılan prompt
        varsayilan = {
            "TRAFİK": "traffic accident Turkey street photorealistic",
            "HAVA": "stormy weather Turkey landscape photorealistic",
            "ASAYİŞ": "police operation Turkey city photorealistic",
            "SPOR": "sports event Turkey stadium photorealistic",
            "ETKİNLİK": "cultural event Turkey outdoor photorealistic",
            "EĞİTİM": "university students Turkey campus photorealistic",
            "KÜLTÜR": "Turkish culture art museum photorealistic",
            "DUYURU": "city hall Turkey announcement photorealistic",
        }
        return varsayilan.get(category, "Canakkale Turkey city photorealistic")


# ---------------------------------------------------
# TEST BLOĞU
# ---------------------------------------------------
if __name__ == "__main__":
    # rewrite_news testi
    baslik = "Çanakkale'de trafik kazası: 2 kişi yaralandı"
    aciklama = "Merkez ilçede meydana gelen trafik kazasında 2 kişi yaralanarak hastaneye kaldırıldı."

    yeni_baslik, yeni_aciklama = rewrite_news(baslik, aciklama)
    print(f"Orijinal başlık   : {baslik}")
    print(f"Yeni başlık       : {yeni_baslik}")
    print(f"---")
    print(f"Orijinal açıklama : {aciklama}")
    print(f"Yeni açıklama     : {yeni_aciklama}")
    print(f"---")

    # generate_image_prompt testi
    prompt = generate_image_prompt(yeni_baslik, "TRAFİK")
    print(f"Görsel prompt     : {prompt}")