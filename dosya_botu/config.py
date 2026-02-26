"""
PROFESYONEL BOT YAPILANDIRMA DOSYASI - GELİŞMİŞ VERSİYON
Tüm sistem ayarları, sabitler ve konfigürasyonlar burada merkezi olarak yönetilir
Environment değişkenleri ile güvenli yapılandırma, tip güvenliği ve validasyon
"""

import os
import sys
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

# ========== ENVIRONMENT YÖNETİMİ ==========
# .env dosyasından environment değişkenlerini yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv yoksa normal environment kullan

class Environment(Enum):
    """Çalışma ortamı tipleri"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# Aktif ortam
ENVIRONMENT = Environment(os.getenv('ENVIRONMENT', 'development'))

# ========== GÜVENLİK AYARLARI ==========
# Token'ı environment'dan al (en güvenli yöntem)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8530574443:AAHnMkNcNHVbtYIbGrqUmylGh7bikFRZkWU')
ADMIN_ID = int(os.getenv('ADMIN_ID', '6284943821'))
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'yusozone')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'dosya_asistani_bot')
BOT_NAME = os.getenv('BOT_NAME', 'Dosya Asistanı')
BOT_VERSION = os.getenv('BOT_VERSION', '2.0.0')

# Güvenlik anahtarları
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-encryption-key-change-in-production')

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '10'))  # Dakikada maksimum istek
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # Saniye cinsinden pencere

# ========== ÇALIŞMA SAATLERİ (7/24 AKTİF) ==========
# Not: Çalışma saatleri kontrolü devre dışı, bot 7/24 hizmet veriyor
WORK_HOURS_ACTIVE = False
WORK_HOURS_START = 0
WORK_HOURS_END = 23
WORK_HOURS_STRING = "7/24 HİZMET"

# ========== PAKET AYARLARI ==========
DEFAULT_PACKAGE_SIZE = int(os.getenv('DEFAULT_PACKAGE_SIZE', '30'))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '50')) * 1024 * 1024  # MB'dan byte'a çevir
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '10'))
TEMP_FILE_RETENTION_HOURS = int(os.getenv('TEMP_FILE_RETENTION_HOURS', '24'))

# ========== KALİTE AYARLARI ==========
@dataclass
class QualityLevel:
    """Kalite seviyesi veri sınıfı"""
    id: str
    name: str
    emoji: str
    description: str
    dpi: int
    compression: int
    ocr_scale: float
    font_size: int
    line_spacing: float
    price_multiplier: float

QUALITY_LEVELS = {
    'draft': QualityLevel(
        id='draft',
        name='Taslak',
        emoji='📄',
        description='Düşük kalite, hızlı işlem',
        dpi=150,
        compression=80,
        ocr_scale=1.5,
        font_size=10,
        line_spacing=1.0,
        price_multiplier=0.5
    ),
    'standard': QualityLevel(
        id='standard',
        name='Standart',
        emoji='📑',
        description='Normal kalite, dengeli performans',
        dpi=200,
        compression=85,
        ocr_scale=2.0,
        font_size=11,
        line_spacing=1.15,
        price_multiplier=1.0
    ),
    'professional': QualityLevel(
        id='professional',
        name='Profesyonel',
        emoji='✨',
        description='Yüksek kalite, ofis standardı',
        dpi=300,
        compression=90,
        ocr_scale=2.5,
        font_size=12,
        line_spacing=1.5,
        price_multiplier=1.5
    ),
    'premium': QualityLevel(
        id='premium',
        name='Premium',
        emoji='💎',
        description='Maksimum kalite, baskıya hazır',
        dpi=600,
        compression=95,
        ocr_scale=3.0,
        font_size=14,
        line_spacing=2.0,
        price_multiplier=2.0
    )
}

# Varsayılan kalite seviyesi
DEFAULT_QUALITY = os.getenv('DEFAULT_QUALITY', 'professional')

# ========== DÖNÜŞÜM AYARLARI ==========
class FileType(str, Enum):
    """Dosya tipleri (Enum ile tip güvenliği)"""
    PDF = "PDF"
    WORD = "WORD"
    EXCEL = "EXCEL"
    POWERPOINT = "POWERPOINT"
    GORSEL = "GORSEL"
    TEXT = "TEXT"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    UNKNOWN = "UNKNOWN"

# Desteklenen formatlar (uzantı -> tip)
SUPPORTED_FORMATS: Dict[str, FileType] = {
    '.pdf': FileType.PDF,
    '.doc': FileType.WORD, '.docx': FileType.WORD,
    '.xls': FileType.EXCEL, '.xlsx': FileType.EXCEL,
    '.ppt': FileType.POWERPOINT, '.pptx': FileType.POWERPOINT,
    '.png': FileType.GORSEL, '.jpg': FileType.GORSEL, '.jpeg': FileType.GORSEL,
    '.txt': FileType.TEXT, '.rtf': FileType.TEXT,
    '.md': FileType.MARKDOWN,
}

# Format kategorileri
FORMAT_CATEGORIES: Dict[FileType, str] = {
    FileType.PDF: 'document',
    FileType.WORD: 'document',
    FileType.EXCEL: 'spreadsheet',
    FileType.POWERPOINT: 'presentation',
    FileType.GORSEL: 'image',
    FileType.TEXT: 'text',
    FileType.MARKDOWN: 'text',
}

# Dönüşüm haritası (hangi formattan hangilerine dönüşebilir)
CONVERSION_MAP: Dict[FileType, List[FileType]] = {
    FileType.WORD: [FileType.PDF, FileType.EXCEL, FileType.POWERPOINT, FileType.TEXT],
    FileType.EXCEL: [FileType.PDF, FileType.WORD, FileType.POWERPOINT, FileType.TEXT],
    FileType.POWERPOINT: [FileType.PDF, FileType.WORD, FileType.TEXT],
    FileType.PDF: [FileType.WORD, FileType.TEXT],
    FileType.GORSEL: [FileType.PDF, FileType.WORD, FileType.TEXT],
    FileType.TEXT: [FileType.PDF, FileType.WORD],
    FileType.MARKDOWN: [FileType.PDF, FileType.WORD, FileType.HTML],
}

# Buton görünen isimleri
DISPLAY_NAMES: Dict[FileType, str] = {
    FileType.PDF: '📄 PDF',
    FileType.WORD: '📝 Word',
    FileType.EXCEL: '📊 Excel',
    FileType.POWERPOINT: '📽️ PowerPoint',
    FileType.GORSEL: '🖼️ Görsel',
    FileType.TEXT: '📃 Metin',
    FileType.MARKDOWN: '📝 Markdown',
    FileType.HTML: '🌐 HTML',
}

# Dosya uzantıları
EXTENSION_MAP: Dict[FileType, str] = {
    FileType.PDF: '.pdf',
    FileType.WORD: '.docx',
    FileType.EXCEL: '.xlsx',
    FileType.POWERPOINT: '.pptx',
    FileType.GORSEL: '.png',
    FileType.TEXT: '.txt',
    FileType.MARKDOWN: '.md',
    FileType.HTML: '.html',
}

# ========== AKILLI İŞLEM AYARLARI ==========
@dataclass
class RightsCost:
    """İşlem maliyetleri"""
    naming: int = 1
    classification: int = 1
    analysis: int = 1
    conversion: int = 1
    smart_edit: int = 1
    summary: int = 1
    validation: int = 1
    quality: int = 1
    all: int = 5

RIGHTS_COST = RightsCost()

# ========== OCR AYARLARI ==========
OCR_LANGUAGES = ['tur', 'eng', 'deu', 'fra', 'spa', 'ita', 'rus']
DEFAULT_OCR_LANGUAGE = os.getenv('DEFAULT_OCR_LANGUAGE', 'tur+eng')
OCR_CONFIGS = [
    '--oem 3 --psm 6',      # Varsayılan
    '--oem 3 --psm 3',      # Otomatik sayfa bölme
    '--oem 3 --psm 4',      # Tek sütun
    '--oem 3 --psm 11',     # Sparse text
    '--oem 3 --psm 12',     # Sparse text + osd
]

# Tesseract yolu (environment'dan alınabilir)
TESSERACT_CMD = os.getenv('TESSERACT_CMD', None)
if os.name == 'nt' and not TESSERACT_CMD:  # Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            TESSERACT_CMD = path
            break

# ========== VERİTABANI AYARLARI ==========
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'database' / 'bot.db'))
DATABASE_BACKUP_PATH = os.getenv('DATABASE_BACKUP_PATH', str(BASE_DIR / 'database' / 'backups'))
DATABASE_BACKUP_INTERVAL_HOURS = int(os.getenv('DATABASE_BACKUP_INTERVAL_HOURS', '24'))
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
DATABASE_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', '30'))

# ========== LOGLAMA AYARLARI ==========
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOG_DIR = BASE_DIR / 'logs'

# Log dosyalarının tam yolları
LOG_FILES = {
    'bot': str(LOG_DIR / 'bot.log'),
    'database': str(LOG_DIR / 'database.log'),
    'payments': str(LOG_DIR / 'payments.log'),
    'converters': str(LOG_DIR / 'converters.log'),
    'analyzer': str(LOG_DIR / 'analyzer.log'),
    'ai_editor': str(LOG_DIR / 'ai_editor.log'),
    'quality': str(LOG_DIR / 'quality.log'),
    'error': str(LOG_DIR / 'error.log'),  # Sadece hatalar için
}

# ========== GEÇİCİ DOSYA AYARLARI ==========
TEMP_DIR = os.getenv('TEMP_DIR', str(BASE_DIR / 'temp'))
TEMP_CLEANUP_INTERVAL_MINUTES = int(os.getenv('TEMP_CLEANUP_INTERVAL_MINUTES', '60'))
TEMP_FILE_PREFIX = os.getenv('TEMP_FILE_PREFIX', 'temp_')

# ========== PAKET FİYATLARI ==========
@dataclass
class Package:
    """Paket bilgileri"""
    id: str
    name: str
    emoji: str
    rights: int
    original_price: int
    price: int
    discount: int
    features: List[str]

PACKAGE_PRICES: Dict[str, Package] = {
    '5': Package(
        id='5',
        name='Başlangıç Paketi',
        emoji='🌟',
        rights=5,
        original_price=300,
        price=200,
        discount=33,
        features=[
            '✅ 5 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Temel analiz',
            '✅ 7/24 destek'
        ]
    ),
    '15': Package(
        id='15',
        name='Gümüş Paket',
        emoji='🚀',
        rights=15,
        original_price=750,
        price=500,
        discount=33,
        features=[
            '✅ 15 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Öncelikli destek'
        ]
    ),
    '30': Package(
        id='30',
        name='Elmas Paket',
        emoji='💎',
        rights=30,
        original_price=1400,
        price=1000,
        discount=29,
        features=[
            '✅ 30 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Belge özetleme',
            '✅ Hata kontrolü',
            '✅ Acil destek hattı'
        ]
    ),
    '50': Package(
        id='50',
        name='Platin Paket',
        emoji='👑',
        rights=50,
        original_price=2000,
        price=1500,
        discount=25,
        features=[
            '✅ 50 dosya dönüştürme hakkı',
            '✅ Tüm formatlar desteklenir',
            '✅ Gelişmiş analiz',
            '✅ Akıllı isimlendirme',
            '✅ Belge özetleme',
            '✅ Hata kontrolü',
            '✅ Kalite optimizasyonu',
            '✅ VIP destek'
        ]
    ),
    '75': Package(
        id='75',
        name='Elit Paket',
        emoji='🏆',
        rights=75,
        original_price=3000,
        price=2250,
        discount=25,
        features=[
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
    )
}

# ========== BANKA BİLGİLERİ ==========
# IBAN ve hesap bilgileri environment'dan alınabilir
BANK_ACCOUNTS = {
    'ziraat': {
        'bank': '🏦 Ziraat Bankası',
        'name': os.getenv('BANK_NAME', 'YUSUF POLAT'),
        'iban': os.getenv('BANK_IBAN', 'TR92 0001 0004 6796 3186 2350 01'),
        'branch': os.getenv('BANK_BRANCH', 'Şube: 1234'),
        'account': os.getenv('BANK_ACCOUNT', 'Hesap No: 12345678')
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

⚡ **7/24 HİZMETİNİZDEYİZ!**

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

━━━━━━━━━━━━━━━━━━━━━
📞 Destek: @{support_username}""",

    'no_rights': """❌ **PAKET HAKKINIZ TÜKENMİŞTİR!**

━━━━━━━━━━━━━━━━━━━━━
📦 Dönüştürme işlemine devam etmek için yeni bir paket satın almanız gerekiyor.

🎁 **SİZE ÖZEL İNDİRİMLİ PAKETLER:**
{packages}

━━━━━━━━━━━━━━━━━━━━━
💡 Hemen paket satın alın!""",

    'file_actions': """📂 **Dosya yüklendi:** `{file_name}`

📁 **Dosya türü:** {file_type}
📊 **Dosya boyutu:** {file_size}
🔄 **Dönüştürülebilir:** {conversion_options}

⚡ Ne yapmak istersiniz?""",

    'conversion_success': """✅ **Dönüştürme tamamlandı!**

📁 Kaynak: {source}
📁 Hedef: {target}
⏱️ Süre: {time:.2f} saniye
📊 Kalite: %{quality}
📌 **{rights} hak tüketildi**

🔁 Kalan hak: {remaining}""",

    'conversion_failed': """❌ **Dönüştürme başarısız!**

📁 Dosya: `{file_name}`
⚠️ Hata: {error}

📂 Yeni dosya yükleyebilir veya @{support_username} ile iletişime geçebilirsiniz."""
}

# ========== DİĞER SABİTLER ==========
# Destek iletişim
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', 'yusozone')
SUPPORT_CHAT = os.getenv('SUPPORT_CHAT', 't.me/yusozone')

# Varsayılan dil
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'tr')

# Maksimum deneme sayısı
MAX_RETRY_COUNT = int(os.getenv('MAX_RETRY_COUNT', '3'))

# Zaman aşımı (saniye)
TIMEOUT_SECONDS = int(os.getenv('TIMEOUT_SECONDS', '300'))  # 5 dakika

# API endpoint'leri
API_BASE_URL = os.getenv('API_BASE_URL', '')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

# ========== ORTAMA ÖZEL AYARLAR ==========
def get_env_specific_config() -> Dict[str, Any]:
    """Çalışma ortamına özel ayarları döndür"""
    configs = {
        Environment.DEVELOPMENT: {
            'debug': True,
            'log_level': 'DEBUG',
            'temp_cleanup_interval': 5,  # 5 dakika
            'database_pool_size': 5,
        },
        Environment.TESTING: {
            'debug': True,
            'log_level': 'DEBUG',
            'temp_cleanup_interval': 1,
            'database_pool_size': 3,
        },
        Environment.STAGING: {
            'debug': False,
            'log_level': 'INFO',
            'temp_cleanup_interval': 30,
            'database_pool_size': 8,
        },
        Environment.PRODUCTION: {
            'debug': False,
            'log_level': 'WARNING',
            'temp_cleanup_interval': 60,
            'database_pool_size': 15,
        }
    }
    return configs.get(ENVIRONMENT, configs[Environment.DEVELOPMENT])

# Ortama özel ayarları uygula
ENV_CONFIG = get_env_specific_config()

# ========== YARDIMCI FONKSİYONLAR ==========
def get_work_hours_string() -> str:
    """Çalışma saatlerini string olarak döndür"""
    if not WORK_HOURS_ACTIVE:
        return "7/24 HİZMET"
    return f"{WORK_HOURS_START:02d}:00 - {WORK_HOURS_END:02d}:00"

def get_package_info(package_id: str) -> Optional[Package]:
    """Paket bilgilerini döndür"""
    return PACKAGE_PRICES.get(package_id)

def get_packages_summary() -> str:
    """Tüm paketlerin özetini döndür"""
    summary = []
    for package in PACKAGE_PRICES.values():
        summary.append(
            f"  {package.emoji} **{package.name}:** "
            f"{package.rights} Hak → ~~{package.original_price} TL~~ "
            f"**{package.price} TL** (%{package.discount} indirim!)"
        )
    return '\n'.join(summary)

def get_rights_cost(operation: str) -> int:
    """İşlem maliyetini döndür"""
    return getattr(RIGHTS_COST, operation, 1)

def get_quality_level(level_id: str) -> QualityLevel:
    """Kalite seviyesi bilgilerini döndür"""
    return QUALITY_LEVELS.get(level_id, QUALITY_LEVELS[DEFAULT_QUALITY])

def is_supported_format(file_ext: str) -> bool:
    """Dosya uzantısının desteklenip desteklenmediğini kontrol et"""
    return file_ext.lower() in SUPPORTED_FORMATS

def get_format_type(file_ext: str) -> FileType:
    """Dosya uzantısına göre format tipini döndür"""
    return SUPPORTED_FORMATS.get(file_ext.lower(), FileType.UNKNOWN)

def get_display_name(format_type: FileType) -> str:
    """Format tipine göre görünen adı döndür"""
    return DISPLAY_NAMES.get(format_type, str(format_type))

def get_extension(format_type: FileType) -> str:
    """Format tipine göre dosya uzantısını döndür"""
    return EXTENSION_MAP.get(format_type, '.bin')

def get_conversion_options(source_type: FileType) -> List[FileType]:
    """Kaynak tipe göre dönüştürülebilecek hedef tipleri döndür"""
    return CONVERSION_MAP.get(source_type, [])

def get_conversion_options_display(source_type: FileType) -> str:
    """Kaynak tipe göre dönüştürülebilecek hedef tiplerin görünen adlarını döndür"""
    options = get_conversion_options(source_type)
    return ', '.join(get_display_name(opt) for opt in options)

def validate_config() -> List[str]:
    """Yapılandırma dosyasını doğrula, hataları listele"""
    errors = []
    
    # Token kontrolü
    if not BOT_TOKEN or len(BOT_TOKEN) < 10:
        errors.append("❌ BOT_TOKEN geçersiz veya çok kısa")
    
    # Admin ID kontrolü
    if not isinstance(ADMIN_ID, int) or ADMIN_ID <= 0:
        errors.append("❌ ADMIN_ID geçersiz")
    
    # Dosya boyutu kontrolü
    if MAX_FILE_SIZE <= 0 or MAX_FILE_SIZE > 100 * 1024 * 1024:
        errors.append("⚠️ MAX_FILE_SIZE çok büyük veya geçersiz (max 100 MB önerilir)")
    
    # Desteklenen formatlar kontrolü
    if not SUPPORTED_FORMATS:
        errors.append("❌ Desteklenen format listesi boş")
    
    # Dönüşüm haritası kontrolü
    for source, targets in CONVERSION_MAP.items():
        if not targets:
            errors.append(f"⚠️ {source} için dönüşüm hedefi yok")
    
    # Paket fiyatları kontrolü
    for package_id, package in PACKAGE_PRICES.items():
        if package.price > package.original_price:
            errors.append(f"⚠️ {package.name} indirimli fiyatı orijinalden yüksek")
    
    return errors

# Yapılandırmayı doğrula (sadece geliştirme ortamında)
if ENVIRONMENT == Environment.DEVELOPMENT:
    errors = validate_config()
    if errors:
        print("⚠️ Config uyarıları:")
        for error in errors:
            print(f"  {error}")
        print()

# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Config dosyası test ediliyor...")
    print("=" * 60)
    print(f"🤖 Bot: {BOT_NAME} v{BOT_VERSION}")
    print(f"👑 Admin: @{ADMIN_USERNAME}")
    print(f"🌍 Ortam: {ENVIRONMENT.value}")
    print(f"⚡ Çalışma: {get_work_hours_string()}")
    print(f"📦 Varsayılan paket: {DEFAULT_PACKAGE_SIZE} hak")
    print(f"📁 Desteklenen format: {len(SUPPORTED_FORMATS)}")
    print(f"✨ Kalite seviyesi: {len(QUALITY_LEVELS)}")
    print(f"🔐 Rate limiting: {'Aktif' if RATE_LIMIT_ENABLED else 'Pasif'}")
    print(f"📊 Veritabanı: {DATABASE_PATH}")
    print("=" * 60)
    
    # Validasyon yap
    errors = validate_config()
    if errors:
        print("\n⚠️ Yapılandırma uyarıları:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n✅ Tüm kontroller başarılı!")
    
    print("\n📋 Desteklenen dönüşümler:")
    for source, targets in CONVERSION_MAP.items():
        target_names = [get_display_name(t) for t in targets]
        print(f"  • {get_display_name(source)} -> {', '.join(target_names)}")
    
    print("\n" + "=" * 60)
    print("✅ Config dosyası hazır! (Profesyonel versiyon)")
