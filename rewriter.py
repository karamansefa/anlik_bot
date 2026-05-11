import os
import requests
from dotenv import load_dotenv

# .env dosyasını oku
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def rewrite_news(title, description):
    """
    Haberi Groq API ile yeniden yazar.
    Aynı manayı farklı kelimelerle ifade eder.
    """
    prompt = f"""Sen bir haber editörüsün. Aşağıdaki haberi aynı bilgileri koruyarak farklı kelimelerle yeniden yaz. Telif sorunu yaşanmaması için cümle yapısını değiştir ama haberin özünü koru. Türkçe yaz.

Başlık: {title}
Açıklama: {description}

Şu formatta cevap ver:
BAŞLIK: yeniden yazılmış başlık
AÇIKLAMA: yeniden yazılmış açıklama"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
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

        # Başlık ve açıklamayı ayır
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


# Test bloğu
if __name__ == "__main__":
    baslik = "Çanakkale'de trafik kazası: 2 kişi yaralandı"
    aciklama = "Merkez ilçede meydana gelen trafik kazasında 2 kişi yaralanarak hastaneye kaldırıldı."

    yeni_baslik, yeni_aciklama = rewrite_news(baslik, aciklama)
    print(f"Orijinal başlık : {baslik}")
    print(f"Yeni başlık     : {yeni_baslik}")
    print(f"---")
    print(f"Orijinal açıklama : {aciklama}")
    print(f"Yeni açıklama     : {yeni_aciklama}")