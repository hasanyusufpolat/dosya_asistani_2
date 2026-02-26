"""
PROFESYONEL BOT YAPILANDIRMA DOSYASI
Tüm sistem ayarları, sabitler ve konfigürasyonlar burada merkezi olarak yönetilir
"""

import os
from typing import Dict, List, Any

# ========== BOT TEMEL AYARLARI ==========
BOT_TOKEN = "8530574443:AAHnMkNcNHVbtYIbGrqUmylGh7bikFRZkWU"
ADMIN_ID = 6284943821  # @userinfobot'tan aldığın ID
ADMIN_USERNAME = "yusozone"  # Admin Telegram kullanıcı adı
BOT_USERNAME = "dosya_asistani_bot"
BOT_NAME = "Dosya Asistanı"
BOT_VERSION = "2.0.0"

# ========== ÇALIŞMA SAATLERİ ==========
WORK_HOURS_START = 8  # Sabah 8
WORK_HOURS_END = 20   # Akşam 8
WORK_HOURS_ACTIVE = True  # Çalışma saati kontrolü aktif

# ========== PAKET AYARLARI ==========
DEFAULT_PACKAGE_SIZE = 30  # Varsayılan paket boyutu
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_BATCH_SIZE = 10  # Toplu işlemde maksimum dosya sayısı
TEMP_FILE_RETENTION_HOURS = 24  # Geçici dosyaların saklanma süresi

# ========== KALİTE AYARLARI ==========
QUALITY_LEVELS = {
    'draft': {
        'id': 'draft',
        'name': 'Taslak',
        'emoji': '📄',
        'description': 'Düşük kalite, hızlı işlem',
        'dpi': 150,
        'compression': 80,
        'ocr_scale': 1.5,
        'font_size': 10,
        'line_spacing': 1.0,
        'price_multiplier': 0.5
    },
    'standard': {
        'id': 'standard',
        'name': 'Standart',
        'emoji': '📑',
        'description': 'Normal kalite, dengeli performans',
        'dpi': 200,
        'compression': 85,
        'ocr_scale': 2.0,
        'font_size': 11,
        'line_spacing': 1.15,
        'price_multiplier': 1.0
    },
    'professional': {
        'id': 'professional',
        'name': 'Profesyonel',
        'emoji': '✨',
        'description': 'Yüksek kalite, ofis standardı',
        'dpi': 300,
        'compression': 90,
        'ocr_scale': 2.5,
        'font_size': 12,
        'line_spacing': 1.5,
        'price_multiplier': 1.5
    },
    'premium': {
        'id': 'premium',
        'name': 'Premium',
        'emoji': '💎',
        'description': 'Maksimum kalite, baskıya hazır',
        'dpi': 600,
        'compression': 95,
        'ocr_scale': 3.0,
        'font_size': 14,
        'line_spacing': 2.0,
        'price_multiplier': 2.0
    }
}

# Varsayılan kalite seviyesi
DEFAULT_QUALITY = 'professional'

# ========== DÖNÜŞÜM AYARLARI ==========
SUPPORTED_FORMATS = {
    '.pdf': 'PDF',
    '.doc': 'WORD', '.docx': 'WORD',
    '.xls': 'EXCEL', '.xlsx': 'EXCEL',
    '.ppt': 'POWERPOINT', '.pptx': 'POWERPOINT',
    '.png': 'GORSEL', '.jpg': 'GORSEL', '.jpeg': 'GORSEL',
    '.txt': 'TEXT', '.rtf': 'TEXT',
    '.md': 'MARKDOWN'
}

# Format kategorileri
FORMAT_CATEGORIES = {
    'PDF': 'document',
    'WORD': 'document',
    'EXCEL': 'spreadsheet',
    'POWERPOINT': 'presentation',
    'GORSEL': 'image',
    'TEXT': 'text',
    'MARKDOWN': 'text'
}

# Dönüşüm haritası (hangi formattan hangilerine dönüşebilir)
CONVERSION_MAP = {
    'WORD': ['PDF', 'EXCEL', 'POWERPOINT', 'GORSEL', 'TEXT'],
    'EXCEL': ['PDF', 'WORD', 'POWERPOINT', 'TEXT'],
    'POWERPOINT': ['PDF', 'WORD', 'GORSEL', 'TEXT'],
    'PDF': ['WORD', 'GORSEL', 'TEXT'],
    'GORSEL': ['PDF', 'WORD', 'TEXT'],
    'TEXT': ['PDF', 'WORD', 'GORSEL'],
    'MARKDOWN': ['PDF', 'WORD', 'HTML']
}

# Buton görünen isimleri
DISPLAY_NAMES = {
    'PDF': '📄 PDF',
    'WORD': '📝 Word',
    'EXCEL': '📊 Excel',
    'POWERPOINT': '📽️ PowerPoint',
    'GORSEL': '🖼️ Görsel',
    'TEXT': '📃 Metin',
    'MARKDOWN': '📝 Markdown'
}

# Dosya uzantıları
EXTENSION_MAP = {
    'PDF': '.pdf',
    'WORD': '.docx',
    'EXCEL': '.xlsx',
    'POWERPOINT': '.pptx',
    'GORSEL': '.png',
    'TEXT': '.txt',
    'MARKDOWN': '.md',
    'HTML': '.html'
}

# ========== AKILLI İŞLEM AYARLARI ==========
# Her işlem için tüketilecek hak sayısı
RIGHTS_COST = {
    'naming': 1,          # Akıllı isimlendirme
    'classification': 1,   # Belge türü tanıma
    'analysis': 1,         # Analiz
    'conversion': 1,       # Dönüşüm
    'smart_edit': 1,       # Akıllı düzenleme
    'summary': 1,          # Özetleme
    'validation': 1,       # Doğrulama
    'quality': 1,          # Kalite optimizasyonu
    'all': 5               # Tüm işlemler
}

# ========== OCR AYARLARI ==========
OCR_LANGUAGES = ['tur', 'eng', 'deu', 'fra', 'spa', 'ita', 'rus']
DEFAULT_OCR_LANGUAGE = 'tur+eng'
OCR_CONFIGS = [
    '--oem 3 --psm 6',     # Varsayılan
    '--oem 3 --psm 3',     # Otomatik sayfa bölme
    '--oem 3 --psm 4',     # Tek sütun
    '--oem 3 --psm 11',    # Sparse text
    '--oem 3 --psm 12'     # Sparse text + osd
]

# ========== VERİTABANI AYARLARI ==========
DATABASE_PATH = 'database/bot.db'
DATABASE_BACKUP_PATH = 'database/backups/'
DATABASE_BACKUP_INTERVAL_HOURS = 24

# ========== LOGLAMA AYARLARI ==========
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILES = {
    'bot': 'bot.log',
    'database': 'database.log',
    'payments': 'payments.log',
    'converters': 'converters.log',
    'analyzer': 'analyzer.log',
    'ai_editor': 'ai_editor.log',
    'quality': 'quality.log'
}

# ========== GEÇİCİ DOSYA AYARLARI ==========
TEMP_DIR = 'temp'
TEMP_CLEANUP_INTERVAL_MINUTES = 60

# ========== PAKET FİYATLARI ==========
PACKAGE_PRICES = {
    '5': {
        'name': 'Başlangıç Paketi',
        'emoji': '🌟',
        'rights': 5,
        'original_price': 300,
        'price': 200,
        'discount': 33,
        'features': [
            '✅ 5 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Temel analiz',
            '✅ 7/24 destek'
        ]
    },
    '15': {
        'name': 'Gümüş Paket',
        'emoji': '🚀',
        'rights': 15,
        'original_price': 750,
        'price': 500,
        'discount': 33,
        'features': [
            '✅ 15 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Öncelikli destek'
        ]
    },
    '30': {
        'name': 'Elmas Paket',
        'emoji': '💎',
        'rights': 30,
        'original_price': 1400,
        'price': 1000,
        'discount': 29,
        'features': [
            '✅ 30 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Belge özetleme',
            '✅ Hata kontrolü',
            '✅ Acil destek hattı'
        ]
    },
    '50': {
        'name': 'Platin Paket',
        'emoji': '👑',
        'rights': 50,
        'original_price': 2000,
        'price': 1500,
        'discount': 25,
        'features': [
            '✅ 50 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Belge özetleme',
            '✅ Hata kontrolü',
            '✅ Kalite optimizasyonu',
            '✅ VIP destek'
        ]
    },
    '75': {
        'name': 'Elit Paket',
        'emoji': '🏆',
        'rights': 75,
        'original_price': 3000,
        'price': 2250,
        'discount': 25,
        'features': [
            '✅ 75 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Belge özetleme',
            '✅ Hata kontrolü',
            '✅ Kalite optimizasyonu',
            '✅ Toplu işlem',
            '✅ 7/24 VIP destek',
            '✅ Özel menajer'
        ]
    }
}

# ========== BANKA BİLGİLERİ ==========
BANK_ACCOUNTS = {
    'ziraat': {
        'bank': '🏦 Ziraat Bankası',
        'name': 'YUSUF POLAT',
        'iban': 'TR92 0001 0004 6796 3186 2350 01',
        'branch': 'Şube: 1234',
        'account': 'Hesap No: 12345678'
    }
}

# ========== MESAJ ŞABLONLARI ==========
MESSAGE_TEMPLATES = {
    'welcome': """🤖 **{bot_name}'na hoş geldiniz!** 

━━━━━━━━━━━━━━━━━━━━━
👤 **Kullanıcı:** {user_name}
📦 **Kalan Hakkınız:** {remaining} Dosya

📁 **Desteklenen Formatlar:**
• PDF • Word • Excel • PowerPoint • Görsel

✨ **Akıllı Özellikler:**
• 📛 Akıllı İsimlendirme
• 📄 Belge Türü Tanıma
• 📋 Belge Özetleme
• ✅ Hata ve Eksik Kontrolü
• ⭐ Kalite Optimizasyonu

⏰ **Çalışma Saatleri:** {work_hours}

━━━━━━━━━━━━━━━━━━━━━
Başlamak için butona tıklayın.""",
    
    'rights_status': """📊 **HAK DURUMUNUZ**

━━━━━━━━━━━━━━━━━━━━━
📦 **Kalan Hak:** `{remaining}` Dosya
✅ **Başarılı İşlem:** `{success}`
❌ **Başarısız İşlem:** `{failed}`
📈 **Toplam İşlem:** `{total}`
📅 **Bugünkü İşlem:** `{today}`
📊 **Haftalık İşlem:** `{weekly}`

📊 **Akıllı İşlemler:**
• Analiz: `{analysis}`
• İsimlendirme: `{naming}`
• Sınıflandırma: `{classification}`
• Özetleme: `{summaries}`
• Doğrulama: `{validations}`

━━━━━━━━━━━━━━━━━━━━━""",

    'out_of_hours': """😴 **Bot şu anda çalışma saatleri dışında!**

━━━━━━━━━━━━━━━━━━━━━
🕒 Çalışma saatlerimiz: **{start}:00 - {end}:00**

⏳ {wait_hours} saat sonra ({target}:00'de) tekrar aktif olacağız.

📞 Acil durumlar için: @{admin_username}""",

    'no_rights': """❌ **PAKET HAKKINIZ TÜKENMİŞTİR!**

━━━━━━━━━━━━━━━━━━━━━
📦 Dönüştürme işlemine devam etmek için yeni bir paket satın almanız gerekiyor.

🎁 **SİZE ÖZEL İNDİRİMLİ PAKETLER:**""",

    'smart_menu': """✨ **AKILLI İŞLEMLER MENÜSÜ**

━━━━━━━━━━━━━━━━━━━━━
Aşağıdaki işlemlerden birini seçin:

📛 **Akıllı İsimlendirme** - Dosya içeriğine göre anlamlı isim verir ({naming_cost} hak)
📄 **Belge Türü Tanıma** - Belge türünü otomatik algılar ({classification_cost} hak)
✨ **Akıllı Dönüşüm** - Analiz + dönüşüm ({conversion_cost} hak)
📋 **Belge Özetleme** - 6-7 satırlık özet çıkarır ({summary_cost} hak)
✅ **Hata ve Eksik Kontrolü** - Eksik alanları tespit eder ({validation_cost} hak)
🔁 **Tüm Akıllı İşlemler** - Tüm işlemler tek seferde ({all_cost} hak)
⭐ **Kalite Optimizasyonu** - Belgeyi profesyonel kaliteye yükseltir ({quality_cost} hak)

━━━━━━━━━━━━━━━━━━━━━""",

    'file_actions': """📂 **Dosya yüklendi:** `{file_name}`

📁 **Dosya türü:** {file_type}
📊 **Dosya boyutu:** {file_size}

Ne yapmak istersiniz?""",

    'conversion_success': """✅ **Dönüştürme tamamlandı!**

📁 Kaynak: {source}
📁 Hedef: {target}
⏱️ Süre: {time} saniye
📊 Kalite: %{quality}

📌 **{rights} hak tüketildi.**""",

    'conversion_failed': """❌ **Dönüştürme başarısız!**

📁 Dosya: `{file_name}`
⚠️ Hata: {error}

📂 Yeni dosya yükleyebilirsiniz."""
}

# ========== DİĞER SABİTLER ==========
# Destek iletişim
SUPPORT_USERNAME = "yusozone"
SUPPORT_CHAT = "t.me/yusozone"

# Varsayılan dil
DEFAULT_LANGUAGE = 'tr'

# Maksimum deneme sayısı
MAX_RETRY_COUNT = 3

# Zaman aşımı (saniye)
TIMEOUT_SECONDS = 300  # 5 dakika

# ========== YARDIMCI FONKSİYONLAR ==========
def get_work_hours_string() -> str:
    """Çalışma saatlerini string olarak döndür"""
    return f"{WORK_HOURS_START:02d}:00 - {WORK_HOURS_END:02d}:00"

def get_package_info(package_id: str) -> Dict:
    """Paket bilgilerini döndür"""
    return PACKAGE_PRICES.get(package_id, {})

def get_rights_cost(operation: str) -> int:
    """İşlem maliyetini döndür"""
    return RIGHTS_COST.get(operation, 1)

def get_quality_level(level_id: str) -> Dict:
    """Kalite seviyesi bilgilerini döndür"""
    return QUALITY_LEVELS.get(level_id, QUALITY_LEVELS[DEFAULT_QUALITY])

def is_supported_format(file_ext: str) -> bool:
    """Dosya uzantısının desteklenip desteklenmediğini kontrol et"""
    return file_ext.lower() in SUPPORTED_FORMATS

def get_format_type(file_ext: str) -> str:
    """Dosya uzantısına göre format tipini döndür"""
    return SUPPORTED_FORMATS.get(file_ext.lower(), 'UNKNOWN')

def get_display_name(format_type: str) -> str:
    """Format tipine göre görünen adı döndür"""
    return DISPLAY_NAMES.get(format_type, format_type)

def get_extension(format_type: str) -> str:
    """Format tipine göre dosya uzantısını döndür"""
    return EXTENSION_MAP.get(format_type, '.bin')

def get_conversion_options(source_type: str) -> List[str]:
    """Kaynak tipe göre dönüştürülebilecek hedef tipleri döndür"""
    return CONVERSION_MAP.get(source_type, ['PDF'])


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Config dosyası test ediliyor...")
    print("=" * 50)
    print(f"🤖 Bot: {BOT_NAME} v{BOT_VERSION}")
    print(f"👑 Admin: @{ADMIN_USERNAME}")
    print(f"⏰ Çalışma saatleri: {get_work_hours_string()}")
    print(f"📦 Varsayılan paket: {DEFAULT_PACKAGE_SIZE} hak")
    print(f"📁 Desteklenen format: {len(SUPPORTED_FORMATS)}")
    print(f"✨ Kalite seviyesi: {len(QUALITY_LEVELS)}")
    print("=" * 50)
    print("✅ Config dosyası hazır!")