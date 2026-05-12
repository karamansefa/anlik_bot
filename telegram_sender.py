import requests
import os
from dotenv import load_dotenv

# ---------------------------------------------------
# TELEGRAM BİLGİLERİ
# os.environ.get() → GitHub Secrets'tan okur
# Kod içine direkt yazmıyoruz — güvenlik için
# ---------------------------------------------------
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_photo(image_path, caption):
    """
    Telegram'a görsel + açıklama gönderir.

    image_path → görselin bilgisayardaki yolu (örn: /tmp/haber.png)
    caption    → görselin altına yazılacak metin
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo:
        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            },
            files={"photo": photo}
        )

    return response.json()


def send_message(text):
    """
    Telegram'a sadece metin gönderir.
    Hata mesajları veya bildirimler için kullanılır.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
    )

    return response.json()


# ---------------------------------------------------
# TEST BLOĞU
# ---------------------------------------------------
if __name__ == "__main__":
    print(f"Token: {TELEGRAM_TOKEN}")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    sonuc = send_message("Test mesajı - bot çalışıyor!")
    print(sonuc)