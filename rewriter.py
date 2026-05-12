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
        return title, description


if __name__ == "__main__":
    baslik = "Çanakkale'de trafik kazası: 2 kişi yaralandı"
    aciklama = "Merkez ilçede meydana gelen trafik kazasında 2 kişi yaralanarak hastaneye kaldırıldı."

    yeni_baslik, yeni_aciklama = rewrite_news(baslik, aciklama)
    print(f"Orijinal başlık   : {baslik}")
    print(f"Yeni başlık       : {yeni_baslik}")
    print(f"---")
    print(f"Orijinal açıklama : {aciklama}")
    print(f"Yeni açıklama     : {yeni_aciklama}")