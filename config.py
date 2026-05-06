# ---------------------------------------------------
# Telegram
# ---------------------------------------------------
TELEGRAM_TOKEN = None
TELEGRAM_CHAT_ID = None

# ---------------------------------------------------
# Bot ayarları
# ---------------------------------------------------
MAX_NEWS_PER_RUN = 3
SERVER_PORT = 8765

# ---------------------------------------------------
# Haber siteleri
# ---------------------------------------------------
SITES = [
    {
        "name": "Çanakkale Haber",
        "url": "https://www.canakkalehaber.com/",
        "base_url": "https://www.canakkalehaber.com"
    },
    {
        "name": "Çanakkale Gündem",
        "url": "https://canakkalegundem.net/",
        "base_url": "https://canakkalegundem.net"
    },
    {
        "name": "Çanakkale Olay",
        "url": "https://www.canakkaleolay.com/",
        "base_url": "https://www.canakkaleolay.com"
    },
    {
        "name": "Çanakkale Manşet",
        "url": "https://www.canakkalemanset.com/",
        "base_url": "https://www.canakkalemanset.com"
    }
]

# ---------------------------------------------------
# Kategori kuralları
# Kök kelime kullanılır — tüm çekimler yakalanır
# Örnek: "gözalt" → gözaltı, gözaltına, gözaltında
# ---------------------------------------------------
CATEGORY_RULES = {
    "ASAYİŞ": [
        "kaza", "çarpış", "yaral", "öldü", "hayatın kaybett",
        "cinayet", "kavga", "hırsız", "operasyon",
        "gözalt", "tutuklam", "tutukland", "yakaland",
        "uyuşturucu", "yangın", "göçmen", "kaçakç", "suç",
        "ihbar", "şüpheli", "silah", "bıçak",
        "darp", "saldırı", "gasp", "dolandırıcı",
        "kaçtı", "firari", "aranan", "ceset", "intihar", "boğuldu"
    ],

    "TRAFİK": [
        "trafik", "kavşak", "ulaşım", "asfalt",
        "köprü", "kapan", "yol çalışm", "otobüs",
        "araç", "sürücü", "tıkandı", "yaya",
        "direksiyon", "hakimiyet", "takla", "devrildi",
        "çarpıştı", "kaza yaptı", "park halinde",
        "çarptı", "ezdi", "motosiklet", "tır",
        "kamyon", "zincirleme", "alt geçit"
    ],

    "HAVA": [
        "hava", "yağış", "fırtına", "kar", "sıcaklık",
        "soğuk", "meteoroloji", "sel", "taşkın", "don",
        "sis", "dolu", "rüzgar", "uyarı",
        "deprem", "afet", "heyelan", "çığ", "buz"
    ],

    "SPOR": [
        "maç", "futbol", "basketbol", "voleybol",
        "şampiyon", "maraton", "turnuva", "lig",
        "gol", "skor", "deplasman", "puan", "antrenman",
        "teknik direktör", "transfer", "forma",
        "saha", "hakem", "kupa", "final"
    ],

    "ETKİNLİK": [
        "etkinlik", "festival", "konser", "sergi",
        "tiyatro", "kutlam", "tören", "anma", "fuar",
        "sempozyum", "buluşm", "toplantı", "söyleşi",
        "davet", "panel", "konferans", "ödül",
        "seremon", "gala", "lansman"
    ],

    "DUYURU": [
        "belediye", "vali", "kaymakam", "ihale",
        "proje", "yatırım", "meclis", "duyur",
        "hizmet", "başvur", "ücret", "tarife",
        "karar", "yönetmelik", "genelge", "açıklam",
        "çağrı", "talep"
    ],

    "KÜLTÜR": [
        "kültür", "sanat", "müze", "tarih",
        "arkeoloj", "edebiyat", "kitap", "resim",
        "heykel", "şiir", "film", "sinema",
        "gelenek", "folklo", "türkü", "dans",
        "tablo", "halk", "miras", "kazı"
    ],
}

DEFAULT_CATEGORY = "GÜNDEM"