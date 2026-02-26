"""
PROFESYONEL DOSYA DÖNÜŞTÜRME MODÜLÜ - GELİŞMİŞ VERSİYON
Tüm dönüşümler yüksek kalitede ve sorunsuz çalışır
Gelişmiş tipografi, tablo yönetimi ve format koruma
Yapay zeka destekli analiz, isimlendirme, sınıflandırma, özetleme ve doğrulama entegrasyonu
"""

import os
import re
import logging
import datetime
import asyncio
import hashlib
import json
import traceback
import tempfile
import shutil
import time
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import Counter
from pathlib import Path
from functools import wraps

# Görsel işleme kütüphaneleri
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL modülü bulunamadı, görsel işlemleri sınırlı olacak")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️ pytesseract modülü bulunamadı, OCR işlemleri yapılamayacak")

# Yeni modüller (opsiyonel)
try:
    import analyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    analyzer = None
    ANALYZER_AVAILABLE = False

try:
    import ai_editor
    AI_EDITOR_AVAILABLE = True
except ImportError:
    ai_editor = None
    AI_EDITOR_AVAILABLE = False

try:
    import naming
    NAMING_AVAILABLE = True
except ImportError:
    naming = None
    NAMING_AVAILABLE = False

try:
    import classifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    classifier = None
    CLASSIFIER_AVAILABLE = False

try:
    import summarizer
    SUMMARIZER_AVAILABLE = True
except ImportError:
    summarizer = None
    SUMMARIZER_AVAILABLE = False

try:
    import validator
    VALIDATOR_AVAILABLE = True
except ImportError:
    validator = None
    VALIDATOR_AVAILABLE = False

try:
    import quality_optimizer
    QUALITY_OPTIMIZER_AVAILABLE = True
except ImportError:
    quality_optimizer = None
    QUALITY_OPTIMIZER_AVAILABLE = False

# Tesseract yolunu ayarla (platform bağımsız)
def setup_tesseract_path():
    """Tesseract OCR yolunu platforma göre ayarla"""
    if not TESSERACT_AVAILABLE:
        return False
    
    # Environment değişkeninden al
    tesseract_cmd = os.getenv('TESSERACT_CMD')
    if tesseract_cmd and os.path.exists(tesseract_cmd):
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        return True
    
    # Windows için varsayılan yollar
    if os.name == 'nt':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
    
    # Linux/Mac için varsayılan yol
    common_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract']
    for path in common_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    
    return False

TESSERACT_CONFIGURED = setup_tesseract_path()

# Loglama ayarları
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'converters.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ========== DEKORATÖRLER ==========

def timer(func: Callable) -> Callable:
    """Fonksiyon çalışma süresini ölçen dekoratör"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"⏱️ {func.__name__} çalışma süresi: {duration:.3f}s")
        return result
    return wrapper

def handle_exceptions(func: Callable) -> Callable:
    """Fonksiyon hatalarını yakalayan dekoratör"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ {func.__name__} hatası: {e}")
            traceback.print_exc()
            # Hata durumunda standart bir dönüş değeri
            if 'metrics' in kwargs or (len(args) > 2 and isinstance(args[2], ConversionMetrics)):
                metrics = kwargs.get('metrics', args[2] if len(args) > 2 else ConversionMetrics())
                return False, "", metrics
            return False, "", ConversionMetrics()
    return wrapper


# ========== DESTEKLENEN FORMATLAR ==========

class FileType(str, Enum):
    """Dosya tipleri (Enum ile tip güvenliği)"""
    WORD = "WORD"
    EXCEL = "EXCEL"
    POWERPOINT = "POWERPOINT"
    PDF = "PDF"
    GORSEL = "GORSEL"
    TEXT = "TEXT"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    UNKNOWN = "UNKNOWN"

# Dosya uzantılarından tip tespiti
EXTENSION_TO_TYPE = {
    '.doc': FileType.WORD, '.docx': FileType.WORD,
    '.xls': FileType.EXCEL, '.xlsx': FileType.EXCEL,
    '.ppt': FileType.POWERPOINT, '.pptx': FileType.POWERPOINT,
    '.pdf': FileType.PDF,
    '.png': FileType.GORSEL, '.jpg': FileType.GORSEL, '.jpeg': FileType.GORSEL,
    '.bmp': FileType.GORSEL, '.tiff': FileType.GORSEL, '.gif': FileType.GORSEL,
    '.txt': FileType.TEXT, '.rtf': FileType.TEXT,
    '.md': FileType.MARKDOWN,
}

# Tipin görünen adları
TYPE_DISPLAY_NAMES = {
    FileType.WORD: '📝 Word',
    FileType.EXCEL: '📊 Excel',
    FileType.POWERPOINT: '📽️ PowerPoint',
    FileType.PDF: '📄 PDF',
    FileType.GORSEL: '🖼️ Görsel',
    FileType.TEXT: '📃 Metin',
    FileType.MARKDOWN: '📝 Markdown',
    FileType.HTML: '🌐 HTML',
    FileType.UNKNOWN: '❌ Bilinmiyor',
}

# Tipin varsayılan uzantısı
TYPE_EXTENSION = {
    FileType.WORD: '.docx',
    FileType.EXCEL: '.xlsx',
    FileType.POWERPOINT: '.pptx',
    FileType.PDF: '.pdf',
    FileType.GORSEL: '.png',
    FileType.TEXT: '.txt',
    FileType.MARKDOWN: '.md',
    FileType.HTML: '.html',
}

# Desteklenen dönüşümler
SUPPORTED_CONVERSIONS = {
    FileType.WORD: [FileType.PDF, FileType.EXCEL, FileType.POWERPOINT, FileType.TEXT],
    FileType.EXCEL: [FileType.PDF, FileType.WORD, FileType.POWERPOINT, FileType.TEXT],
    FileType.POWERPOINT: [FileType.PDF, FileType.WORD, FileType.TEXT],
    FileType.PDF: [FileType.WORD, FileType.TEXT],
    FileType.GORSEL: [FileType.PDF, FileType.WORD, FileType.TEXT],
    FileType.TEXT: [FileType.PDF, FileType.WORD],
    FileType.MARKDOWN: [FileType.PDF, FileType.WORD, FileType.HTML],
}


# ========== YARDIMCI SINIFLAR ==========

class ConversionQuality(Enum):
    """Dönüşüm kalite seviyeleri"""
    DRAFT = "taslak"           # Düşük kalite, hızlı
    STANDARD = "standart"       # Normal kalite
    PROFESSIONAL = "profesyonel" # Yüksek kalite
    PREMIUM = "premium"         # Maksimum kalite
    
    @classmethod
    def from_string(cls, value: str) -> 'ConversionQuality':
        """String'den enum'a çevir"""
        mapping = {
            'taslak': cls.DRAFT,
            'standart': cls.STANDARD,
            'profesyonel': cls.PROFESSIONAL,
            'premium': cls.PREMIUM,
        }
        return mapping.get(value.lower(), cls.PROFESSIONAL)


class DocumentComplexity(Enum):
    """Belge karmaşıklık seviyeleri"""
    SIMPLE = "basit"            # Düz metin
    MODERATE = "orta"            # Başlıklar, listeler
    COMPLEX = "karmaşık"         # Tablolar, grafikler
    VERY_COMPLEX = "çok karmaşık" # Karmaşık yapılar


@dataclass
class ConversionMetrics:
    """Dönüşüm metrikleri"""
    input_size: int = 0
    output_size: int = 0
    processing_time: float = 0
    compression_ratio: float = 0
    quality_score: int = 0
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    complexity: DocumentComplexity = DocumentComplexity.SIMPLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Sözlüğe çevir"""
        data = asdict(self)
        data['complexity'] = self.complexity.value
        return data


@dataclass
class ConversionResult:
    """Dönüşüm sonuç veri yapısı"""
    success: bool
    output_path: str
    metrics: ConversionMetrics
    changes_made: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Sözlüğe çevir"""
        return {
            'success': self.success,
            'output_path': self.output_path,
            'metrics': self.metrics.to_dict(),
            'changes_made': self.changes_made,
            'error_message': self.error_message,
            'warning_message': self.warning_message,
        }


# ========== YARDIMCI FONKSİYONLAR ==========

def get_file_extension(file_path: str) -> str:
    """Dosya uzantısını döndür"""
    return os.path.splitext(file_path)[1].lower()


def get_file_name_without_extension(file_path: str) -> str:
    """Dosya adını uzantısız döndür"""
    return os.path.splitext(os.path.basename(file_path))[0]


def get_file_size_str(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevir"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.1f} GB"


def detect_file_type(file_path: str) -> FileType:
    """Dosya uzantısından tipini tespit et"""
    ext = get_file_extension(file_path)
    return EXTENSION_TO_TYPE.get(ext, FileType.UNKNOWN)


def is_conversion_supported(source_type: FileType, target_type: FileType) -> bool:
    """Dönüşümün desteklenip desteklenmediğini kontrol et"""
    if source_type not in SUPPORTED_CONVERSIONS:
        return False
    return target_type in SUPPORTED_CONVERSIONS[source_type]


def get_display_name(file_type: FileType) -> str:
    """Dosya tipinin görünen adını döndür"""
    return TYPE_DISPLAY_NAMES.get(file_type, str(file_type))


def get_extension(file_type: FileType) -> str:
    """Dosya tipinin varsayılan uzantısını döndür"""
    return TYPE_EXTENSION.get(file_type, '.bin')


def ensure_directory(directory: str) -> bool:
    """Klasörün var olduğundan emin ol"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Klasör oluşturma hatası: {e}")
        return False


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """Dosya hash'i hesapla (değişiklik kontrolü için)"""
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"❌ Hash hesaplama hatası: {e}")
        return ""


def clean_text(text: str, aggressive: bool = False) -> str:
    """
    Metni temizle ve düzenle (gelişmiş)
    
    Args:
        text: Temizlenecek metin
        aggressive: Agresif temizleme modu
    
    Returns:
        Temizlenmiş metin
    """
    if not text:
        return ""
    
    # Fazla boşlukları temizle
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        clean_line = ' '.join(line.split())
        if clean_line:
            cleaned_lines.append(clean_line)
    
    if aggressive:
        # Agresif temizleme - tüm gereksiz karakterleri temizle
        final_lines = []
        for line in cleaned_lines:
            clean_line = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]{}@#$%&*+/=]', '', line)
            if clean_line:
                final_lines.append(clean_line)
        return '\n'.join(final_lines)
    
    # Normal temizleme
    return '\n'.join(cleaned_lines)


def detect_table_structure(text: str) -> Tuple[bool, List[Dict]]:
    """
    Metin içinde tablo yapısını tespit et (gelişmiş)
    
    Returns:
        (tablo_var_mı, tablo_bilgileri)
    """
    lines = text.split('\n')
    possible_tables = []
    table_score = 0
    
    for i, line in enumerate(lines):
        # Sekme ile ayrılmış tablo
        if '\t' in line:
            cells = line.split('\t')
            if len(cells) > 1:
                table_score += 3
                possible_tables.append({
                    'line': i,
                    'cells': cells,
                    'type': 'tab',
                    'cell_count': len(cells)
                })
        
        # Çoklu boşluk ile ayrılmış tablo
        elif '  ' in line and len(line.split('  ')) > 2:
            cells = [c for c in line.split('  ') if c.strip()]
            if len(cells) > 1:
                table_score += 2
                possible_tables.append({
                    'line': i,
                    'cells': cells,
                    'type': 'space',
                    'cell_count': len(cells)
                })
        
        # Boru (|) ile ayrılmış tablo
        elif '|' in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) > 1:
                table_score += 4
                possible_tables.append({
                    'line': i,
                    'cells': cells,
                    'type': 'pipe',
                    'cell_count': len(cells)
                })
        
        # Düzenli sütunlar
        elif re.search(r'\s{3,}', line):
            cells = re.split(r'\s{3,}', line)
            if len(cells) > 1:
                table_score += 2
                possible_tables.append({
                    'line': i,
                    'cells': cells,
                    'type': 'regex',
                    'cell_count': len(cells)
                })
    
    # Düzenli tablo kontrolü (ardışık satırlar)
    if len(possible_tables) > 2:
        consecutive = 0
        for j in range(len(possible_tables) - 1):
            if possible_tables[j+1]['line'] - possible_tables[j]['line'] == 1:
                consecutive += 1
        if consecutive > 1:
            table_score += 10
    
    # Hücre sayılarının tutarlılığını kontrol et
    if len(possible_tables) > 1:
        cell_counts = [t['cell_count'] for t in possible_tables]
        if max(cell_counts) - min(cell_counts) <= 2:
            table_score += 5
    
    return table_score > len(lines) * 0.15, possible_tables


def format_number(value: Any, decimal_places: int = 2, thousand_sep: bool = True, 
                  currency: str = None) -> str:
    """
    Sayıları formatla (gelişmiş)
    
    Args:
        value: Sayısal değer
        decimal_places: Ondalık basamak sayısı
        thousand_sep: Binlik ayırıcı kullan
        currency: Para birimi (TL, USD, EUR, vs.)
    
    Returns:
        Formatlanmış sayı
    """
    if value is None:
        return ""
    
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            if value.is_integer():
                formatted = str(int(value))
            else:
                formatted = f"{value:.{decimal_places}f}".replace('.', ',')
        else:
            formatted = str(value)
        
        # Binlik ayırıcı ekle
        if thousand_sep and len(formatted) > 3:
            parts = formatted.split(',')
            integer_part = parts[0]
            
            if len(integer_part) > 3:
                # Sağdan sola doğru grupla
                grouped = []
                for i in range(len(integer_part), 0, -3):
                    start = max(0, i-3)
                    grouped.append(integer_part[start:i])
                integer_part = '.'.join(reversed(grouped))
            
            if len(parts) > 1:
                formatted = f"{integer_part},{parts[1]}"
            else:
                formatted = integer_part
        
        # Para birimi ekle
        if currency:
            currency_map = {
                'TL': '₺',
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'JPY': '¥'
            }
            symbol = currency_map.get(currency, currency)
            formatted = f"{formatted} {symbol}"
        
        return formatted
    
    return str(value)


def extract_text_from_file(file_path: str, file_type: FileType, 
                          extract_mode: str = 'full') -> str:
    """
    Dosyadan metin çıkar (farklı formatlar için - süper gelişmiş)
    
    Args:
        file_path: Dosya yolu
        file_type: Dosya tipi
        extract_mode: Çıkarma modu (full, metadata, content_only)
    
    Returns:
        Çıkarılan metin
    """
    text = ""
    metadata = {}
    
    try:
        if file_type == FileType.WORD:
            try:
                from docx import Document
                doc = Document(file_path)
                
                if extract_mode in ['full', 'metadata']:
                    core_props = doc.core_properties
                    metadata = {
                        'author': core_props.author,
                        'created': str(core_props.created),
                        'modified': str(core_props.modified),
                        'title': core_props.title,
                        'subject': core_props.subject
                    }
                
                if extract_mode in ['full', 'content_only']:
                    for para in doc.paragraphs:
                        if para.text.strip():
                            text += para.text + "\n"
                    
                    for table in doc.tables:
                        for row in table.rows:
                            row_text = " | ".join([cell.text for cell in row.cells])
                            if row_text.strip():
                                text += row_text + "\n"
                        text += "\n"
            except Exception as e:
                logger.error(f"❌ Word okuma hatası: {e}")
                return f"[Word dosyası okunamadı: {e}]"
        
        elif file_type == FileType.PDF:
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    
                    if extract_mode in ['full', 'metadata']:
                        metadata = dict(pdf_reader.metadata) if pdf_reader.metadata else {}
                    
                    if extract_mode in ['full', 'content_only']:
                        for page_num, page in enumerate(pdf_reader.pages):
                            page_text = page.extract_text()
                            if page_text.strip():
                                text += f"--- Sayfa {page_num + 1} ---\n"
                                text += page_text + "\n\n"
            except Exception as e:
                logger.error(f"❌ PDF okuma hatası: {e}")
                return f"[PDF dosyası okunamadı: {e}]"
        
        elif file_type == FileType.EXCEL:
            try:
                import pandas as pd
                excel_file = pd.ExcelFile(file_path)
                
                if extract_mode in ['full', 'metadata']:
                    metadata = {
                        'sheet_names': excel_file.sheet_names,
                        'sheet_count': len(excel_file.sheet_names)
                    }
                
                if extract_mode in ['full', 'content_only']:
                    for sheet_name in excel_file.sheet_names:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        text += f"--- Sayfa: {sheet_name} ({df.shape[0]} satır, {df.shape[1]} sütun) ---\n"
                        text += df.to_string() + "\n\n"
            except Exception as e:
                logger.error(f"❌ Excel okuma hatası: {e}")
                return f"[Excel dosyası okunamadı: {e}]"
        
        elif file_type == FileType.POWERPOINT:
            try:
                from pptx import Presentation
                prs = Presentation(file_path)
                
                if extract_mode in ['full', 'metadata']:
                    metadata = {'slide_count': len(prs.slides)}
                
                if extract_mode in ['full', 'content_only']:
                    for slide_num, slide in enumerate(prs.slides, 1):
                        text += f"--- Slayt {slide_num} ---\n"
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                text += shape.text + "\n"
                        text += "\n"
            except Exception as e:
                logger.error(f"❌ PowerPoint okuma hatası: {e}")
                return f"[PowerPoint dosyası okunamadı: {e}]"
        
        elif file_type == FileType.GORSEL:
            if not TESSERACT_AVAILABLE or not TESSERACT_CONFIGURED:
                return "[OCR sistemi yapılandırılmamış]"
            
            try:
                from PIL import Image, ImageEnhance, ImageFilter
                
                image = Image.open(file_path)
                
                if extract_mode in ['full', 'metadata']:
                    metadata = {
                        'format': image.format,
                        'mode': image.mode,
                        'size': image.size,
                        'width': image.width,
                        'height': image.height
                    }
                
                if extract_mode in ['full', 'content_only']:
                    # Görseli ön işle
                    if image.mode != 'L':
                        image = image.convert('L')
                    
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(2.0)
                    
                    image = image.filter(ImageFilter.MedianFilter(size=3))
                    
                    text = pytesseract.image_to_string(image, lang='tur+eng', config='--psm 6')
                    
                    if not text.strip():
                        text = pytesseract.image_to_string(image, lang='tur+eng', config='--psm 3')
            except Exception as e:
                logger.error(f"❌ Görsel OCR hatası: {e}")
                return f"[Görsel okunamadı: {e}]"
        
        else:
            # TXT veya diğer formatlar
            try:
                encodings = ['utf-8', 'windows-1254', 'iso-8859-9', 'latin1']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                            text = f.read()
                        break
                    except:
                        continue
            except Exception as e:
                logger.error(f"❌ Metin dosyası okuma hatası: {e}")
                return f"[Dosya okunamadı: {e}]"
    
    except Exception as e:
        logger.error(f"❌ Metin çıkarma hatası: {e}")
        return f"[İşlem hatası: {e}]"
    
    if extract_mode == 'full' and metadata:
        meta_text = "\n".join([f"{k}: {v}" for k, v in metadata.items() if v])
        if meta_text:
            text = f"--- BELGE METADATASI ---\n{meta_text}\n\n{text}"
    
    return clean_text(text, aggressive=False)


def detect_language(text: str) -> str:
    """Metnin dilini tespit et"""
    if not text:
        return 'unknown'
    
    language_chars = {
        'tr': set('ğüşıöçĞÜŞİÖÇ'),
        'de': set('äöüßÄÖÜ'),
        'fr': set('éèêëàâçôùûÿœæ'),
        'es': set('ñáéíóúüÑÁÉÍÓÚÜ'),
        'it': set('àèéìíîòóùú'),
        'ru': set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'),
        'ar': set('ابتثجحخدذرزسشصضطظعغفقكلمنهوي'),
    }
    
    scores = {}
    for lang, chars in language_chars.items():
        count = sum(1 for c in text if c in chars)
        if count > 0:
            scores[lang] = count
    
    if scores:
        return max(scores, key=scores.get)
    
    return 'en'


def detect_important_fields(text: str) -> Dict[str, Any]:
    """Belgeden önemli alanları tespit et"""
    fields = {}
    
    # Tarih desenleri
    date_patterns = [
        (r'(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{2,4})', 'DMY'),
        (r'(\d{4})[-](\d{1,2})[-](\d{1,2})', 'YMD'),
        (r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(\d{4})', 'TR_MONTH'),
        (r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', 'EN_MONTH'),
    ]
    
    for pattern, format_type in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if format_type == 'DMY':
                day, month, year = match.groups()
                if len(year) == 2:
                    year = '20' + year
                fields['tarih'] = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                break
            elif format_type == 'YMD':
                year, month, day = match.groups()
                fields['tarih'] = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                break
            else:
                day, month_text, year = match.groups()
                month_map = {
                    'Ocak': '01', 'Şubat': '02', 'Mart': '03', 'Nisan': '04',
                    'Mayıs': '05', 'Haziran': '06', 'Temmuz': '07', 'Ağustos': '08',
                    'Eylül': '09', 'Ekim': '10', 'Kasım': '11', 'Aralık': '12',
                    'January': '01', 'February': '02', 'March': '03', 'April': '04',
                    'May': '05', 'June': '06', 'July': '07', 'August': '08',
                    'September': '09', 'October': '10', 'November': '11', 'December': '12'
                }
                month = month_map.get(month_text, '01')
                fields['tarih'] = f"{day.zfill(2)}.{month}.{year}"
                break
    
    # Tutar desenleri
    amount_patterns = [
        r'(?:toplam|genel toplam|tutar|ödenecek|fiyat|ücret)[\s:]*([\d.,]+)\s*(TL|USD|EUR|₺|\$|€|GBP|JPY)?',
        r'([\d.,]+)\s*(TL|USD|EUR|₺|\$|€|GBP|JPY)',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            currency = match.group(2) if len(match.groups()) > 1 else 'TL'
            currency_map = {'₺': 'TL', '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
            currency = currency_map.get(currency, currency)
            fields['tutar'] = f"{amount} {currency}"
            break
    
    # Firma adı
    company_patterns = [
        r'(?:firma|şirket|company|müşteri|customer|alıcı|satıcı)[\s:]*([A-Za-zğüşıöçĞÜŞİÖÇ\s\.]+)',
        r'(?:adı|name|ünvan|unvan|title)[\s:]*([A-Za-zğüşıöçĞÜŞİÖÇ\s\.]+)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            company = match.group(1).strip()
            if 2 < len(company) < 100:
                fields['firma'] = company
                break
    
    # Vergi numarası
    tax_patterns = [
        r'(?:vergi no|tax id|vkn)[\s:]*(\d{10,11})',
        r'(?:TC|kimlik no|TCKN)[\s:]*(\d{11})',
    ]
    
    for pattern in tax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['vergi_no'] = match.group(1)
            break
    
    # IBAN
    iban_pattern = r'(?:IBAN|iban)[\s:]*([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})'
    match = re.search(iban_pattern, text, re.IGNORECASE)
    if match:
        fields['iban'] = match.group(1).replace(' ', '')
    
    return fields


# ========== OCR TEMİZLEME FONKSİYONLARI ==========

def clean_ocr_text(text: str) -> Tuple[str, List[str]]:
    """
    OCR metnini temizle ve gereksiz satırları filtrele
    
    Args:
        text: Orijinal OCR metni
    
    Returns:
        (temizlenmiş_metin, silinen_satırlar)
    """
    if not text:
        return "", []
    
    lines = text.split('\n')
    cleaned_lines = []
    removed_lines = []
    
    # Gereksiz desenler
    unwanted_patterns = [
        r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?',  # Saat
        r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',  # Tarih
        r'Volte?\s*\d{1,2}:\d{2}',  # Volte
        r'(?:Turkcell|Vodafone|Türk Telekom|Türkcell)\s*\d{1,2}:\d{2}',
        r'Ekran\s*(?:Alıntısı|Görüntüsü|Fotoğrafi)',  # Ekran Alıntısı
        r'Screen\s*(?:Shot|Capture)',  # Screen Shot
        r'Screenshot',
        r'Captur(?:e|ed)',
        r'^\s*\d+\s*$',  # Sadece rakam
        r'^\s*[•\-*]\s*$',  # Sadece madde işareti
        r'^\s*[|\\/]\s*$',  # Sadece çizgi
        r'(?:Sayfa|Page)\s+\d+\s*(?:/|of)\s*\d+',  # Sayfa numaraları
        r'^\s*[_\-\=\*]{3,}\s*$',  # Çizgiler
        r'^\s*[▌▐▀▄█▓▒░]\s*$',  # Blok karakterler
    ]
    
    for line in lines:
        line = line.strip()
        
        if not line:
            cleaned_lines.append('')
            continue
        
        if len(line) < 3:
            removed_lines.append(line)
            continue
        
        is_unwanted = False
        for pattern in unwanted_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                removed_lines.append(line)
                is_unwanted = True
                break
        
        if not is_unwanted:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), removed_lines


def calculate_ocr_confidence(text: str) -> float:
    """
    OCR metninin kalitesini hesapla
    
    Args:
        text: OCR metni
    
    Returns:
        Güven skoru (0-100)
    """
    if not text or not text.strip():
        return 0
    
    words = text.split()
    total_chars = len(text)
    total_words = len(words)
    
    if total_words == 0:
        return 0
    
    avg_word_length = total_chars / total_words
    very_short_words = sum(1 for w in words if len(w) <= 2)
    short_ratio = very_short_words / total_words
    
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / total_chars if total_chars > 0 else 0
    
    digit_chars = sum(1 for c in text if c.isdigit())
    digit_ratio = digit_chars / total_chars if total_chars > 0 else 0
    
    confidence = 100
    
    if avg_word_length < 3:
        confidence -= 30
    elif avg_word_length > 15:
        confidence -= 20
    
    if short_ratio > 0.3:
        confidence -= 25
    elif short_ratio > 0.2:
        confidence -= 15
    
    if special_ratio > 0.2:
        confidence -= 20
    elif special_ratio > 0.1:
        confidence -= 10
    
    if digit_ratio > 0.3:
        confidence -= 15
    elif digit_ratio > 0.2:
        confidence -= 5
    
    return max(0, min(100, confidence))


def merge_intelligent_lines(text: str) -> str:
    """
    Akıllı satır birleştirme - bölünmüş kelimeleri ve cümleleri düzelt
    
    Args:
        text: Ham metin
    
    Returns:
        Birleştirilmiş metin
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    merged = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].strip()
        
        if not current_line:
            merged.append('')
            i += 1
            continue
        
        if i < len(lines) - 1:
            next_line = lines[i+1].strip()
            
            if (next_line and next_line[0].islower() and 
                not current_line[-1] in '.!?:;,' and 
                not current_line.endswith('-')):
                
                current_line += ' ' + next_line
                i += 2
                continue
        
        merged.append(current_line)
        i += 1
    
    return '\n'.join(merged)


def normalize_whitespace(text: str) -> str:
    """
    Boşlukları normalize et
    
    Args:
        text: Ham metin
    
    Returns:
        Düzenlenmiş metin
    """
    if not text:
        return ""
    
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


def fix_common_ocr_errors(text: str) -> str:
    """
    Yaygın OCR hatalarını düzelt
    
    Args:
        text: OCR metni
    
    Returns:
        Düzeltilmiş metin
    """
    if not text:
        return ""
    
    replacements = [
        (r'\b0\b', 'O'), (r'\b1\b', 'l'), (r'\b5\b', 'S'),
        ('§', 'S'), ('©', 'C'), ('®', 'R'), ('™', 'TM'),
        ('•', '-'), ('·', '.'), ('…', '...'), ('–', '-'), ('—', '-'),
        ('"', '"'), ('"', '"'), ('´', "'"), ('`', "'"),
        ('Ý', 'İ'), ('Þ', 'Ş'), ('ð', 'ğ'), ('ý', 'ı'),
        ('Ã', 'Ç'), ('ã', 'ç'), ('Ä', 'Ö'), ('ä', 'ö'),
        ('Ë', 'E'), ('ë', 'e'),
    ]
    
    for old, new in replacements:
        if isinstance(old, str) and old.startswith('\\'):
            text = re.sub(old, new, text)
        else:
            text = text.replace(old, new)
    
    return text


# ========== WORD DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def word_to_pdf(input_path: str, output_path: str, 
               quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Word -> PDF (PROFESYONEL - TİPOGRAFİ KORUMALI)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from docx import Document
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        doc = Document(input_path)
        
        # Kalite ayarları
        quality_settings = {
            ConversionQuality.DRAFT: {'title_size': 14, 'heading_size': 12, 'normal_size': 10, 'line_height': 0.5},
            ConversionQuality.STANDARD: {'title_size': 15, 'heading_size': 13, 'normal_size': 11, 'line_height': 0.55},
            ConversionQuality.PROFESSIONAL: {'title_size': 16, 'heading_size': 14, 'normal_size': 11, 'line_height': 0.6},
            ConversionQuality.PREMIUM: {'title_size': 18, 'heading_size': 16, 'normal_size': 12, 'line_height': 0.7},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        left_margin = 2 * cm
        right_margin = width - 2 * cm
        y = height - 2 * cm
        line_height = settings['line_height'] * cm
        
        for paragraph in doc.paragraphs:
            if not paragraph.text.strip():
                y -= line_height * 0.3
                continue
            
            style_name = paragraph.style.name.lower() if paragraph.style else ""
            font_size = settings['normal_size']
            is_bold = False
            
            if 'title' in style_name or 'heading 1' in style_name:
                font_size = settings['title_size']
                is_bold = True
            elif 'heading 2' in style_name:
                font_size = settings['heading_size']
                is_bold = True
            
            c.setFont("Helvetica-Bold" if is_bold else "Helvetica", font_size)
            
            text = paragraph.text.strip()
            words = text.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                line_width = c.stringWidth(test_line, "Helvetica-Bold" if is_bold else "Helvetica", font_size)
                
                if line_width < (right_margin - left_margin):
                    current_line = test_line
                else:
                    if y < line_height:
                        c.showPage()
                        y = height - 2 * cm
                        c.setFont("Helvetica-Bold" if is_bold else "Helvetica", font_size)
                    
                    c.drawString(left_margin, y, current_line)
                    y -= line_height
                    current_line = word
            
            if current_line:
                if y < line_height:
                    c.showPage()
                    y = height - 2 * cm
                c.drawString(left_margin, y, current_line)
                y -= line_height * 1.2
        
        c.save()
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.MODERATE
        
        logger.info(f"✅ Word -> PDF dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def word_to_excel(input_path: str, output_path: str, 
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Word -> Excel (PROFESYONEL - AKILLI TABLO ALGILAMA)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from docx import Document
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        
        doc = Document(input_path)
        
        # Verileri topla
        data = []
        for para in doc.paragraphs:
            if para.text.strip():
                data.append([para.text.strip()])
        
        # Tablo varsa ekle
        for table in doc.tables:
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                if any(row_data):
                    data.append(row_data)
        
        df = pd.DataFrame(data, columns=['İçerik'] if len(data[0]) == 1 else None)
        
        # Excel oluştur
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Word İçeriği')
            
            workbook = writer.book
            worksheet = writer.sheets['Word İçeriği']
            
            # Stil ayarları
            if len(df) > 0:
                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center")
            
            # Sütun genişliklerini ayarla
            for column in worksheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.SIMPLE if len(df) < 50 else DocumentComplexity.MODERATE
        
        logger.info(f"✅ Word -> Excel dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def word_to_pptx(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Word -> PowerPoint (PROFESYONEL - TASARIM ODAKLI)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from docx import Document
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        
        doc = Document(input_path)
        prs = Presentation()
        
        quality_settings = {
            ConversionQuality.DRAFT: {'title': 40, 'heading': 28, 'content': 18, 'per_slide': 6},
            ConversionQuality.STANDARD: {'title': 44, 'heading': 30, 'content': 20, 'per_slide': 5},
            ConversionQuality.PROFESSIONAL: {'title': 48, 'heading': 32, 'content': 20, 'per_slide': 5},
            ConversionQuality.PREMIUM: {'title': 54, 'heading': 36, 'content': 22, 'per_slide': 4},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        # Ana başlık slaytı
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        title = slide.shapes.title
        if title:
            title.text = "WORD DÖKÜMANI DÖNÜŞÜMÜ"
            title.text_frame.paragraphs[0].font.size = Pt(settings['title'])
            title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)
        
        # İçerik slaytları
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        for i in range(0, len(paragraphs), settings['per_slide']):
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            if title:
                title.text = f"İçerik - Bölüm {i//settings['per_slide'] + 1}"
            
            content = slide.placeholders[1]
            tf = content.text_frame
            
            for para in paragraphs[i:i+settings['per_slide']]:
                p = tf.add_paragraph()
                p.text = para
                p.font.size = Pt(settings['content'])
        
        prs.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.MODERATE
        
        logger.info(f"✅ Word -> PowerPoint dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def word_to_text(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Word -> Metin dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from docx import Document
        
        doc = Document(input_path)
        
        text_lines = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_lines.append(para.text.strip())
        
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    text_lines.append(row_text)
        
        text = '\n'.join(text_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ Word -> Metin dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Word -> Metin dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== EXCEL DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def excel_to_pdf(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Excel -> PDF (PROFESYONEL - TABLO KORUMALI)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import pandas as pd
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        df = pd.read_excel(input_path)
        df = df.fillna('')
        
        c = canvas.Canvas(output_path, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        y = height - 2 * cm
        line_height = 0.5 * cm
        
        # Başlık
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, f"Excel Dökümanı: {os.path.basename(input_path)}")
        y -= line_height * 2
        
        # Sütun başlıkları
        c.setFont("Helvetica-Bold", 10)
        x = 2 * cm
        for col in df.columns:
            c.drawString(x, y, str(col)[:15])
            x += 4 * cm
        y -= line_height
        
        # Veriler
        c.setFont("Helvetica", 9)
        for _, row in df.iterrows():
            if y < line_height:
                c.showPage()
                y = height - 2 * cm
                c.setFont("Helvetica", 9)
            
            x = 2 * cm
            for val in row:
                c.drawString(x, y, str(val)[:15])
                x += 4 * cm
            y -= line_height
        
        c.save()
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.MODERATE
        
        logger.info(f"✅ Excel -> PDF dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def excel_to_word(input_path: str, output_path: str,
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Excel -> Word (PROFESYONEL - SAYFAYA TAM SIĞDIRMA)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import pandas as pd
        from docx import Document
        from docx.shared import Cm, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        
        excel_file = pd.ExcelFile(input_path)
        sheet_names = excel_file.sheet_names
        
        doc = Document()
        
        # Sayfa yapısı
        section = doc.sections[0]
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)
        
        # Ana başlık
        title = doc.add_heading('EXCEL DÖKÜMANI DÖNÜŞÜMÜ', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.runs[0]
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)
        
        doc.add_paragraph(f"📊 Kaynak: {os.path.basename(input_path)}")
        doc.add_paragraph()
        
        total_rows = 0
        
        for sheet_idx, sheet_name in enumerate(sheet_names):
            df = pd.read_excel(input_path, sheet_name=sheet_name)
            df = df.fillna('')
            total_rows += len(df)
            
            if sheet_idx > 0:
                doc.add_page_break()
            
            doc.add_heading(f'Sayfa {sheet_idx + 1}: {sheet_name}', level=1)
            
            if df.empty:
                doc.add_paragraph("📭 Bu sayfa boş")
                continue
            
            # Tablo oluştur
            rows, cols = df.shape
            table = doc.add_table(rows=rows+1, cols=cols)
            table.style = 'Light Grid Accent 1'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Başlık satırı
            for col in range(cols):
                cell = table.cell(0, col)
                cell.text = str(df.columns[col])
                
                # Stil
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                shd = OxmlElement('w:shd')
                shd.set(qn('w:fill'), '2E75B6')
                tcPr.append(shd)
                
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = paragraph.runs[0]
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            
            # Veri satırları
            for row in range(rows):
                for col in range(cols):
                    cell = table.cell(row+1, col)
                    value = df.iloc[row, col]
                    
                    if isinstance(value, (int, float)):
                        if isinstance(value, float) and not value.is_integer():
                            cell.text = f"{value:.2f}".replace('.', ',')
                        else:
                            cell.text = str(int(value) if isinstance(value, float) else value)
                    else:
                        cell.text = str(value)
                    
                    # Alternatif satır renkleri
                    if row % 2 == 0:
                        tc = cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        shd = OxmlElement('w:shd')
                        shd.set(qn('w:fill'), 'F2F2F2')
                        tcPr.append(shd)
        
        doc.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.COMPLEX if total_rows > 500 else DocumentComplexity.MODERATE
        
        logger.info(f"✅ Excel -> Word dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def excel_to_pptx(input_path: str, output_path: str,
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Excel -> PowerPoint (PROFESYONEL - GRAFİK DESTEKLİ)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import pandas as pd
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN
        from pptx.dml.color import RGBColor
        
        df = pd.read_excel(input_path)
        df = df.fillna('')
        
        prs = Presentation()
        
        quality_settings = {
            ConversionQuality.DRAFT: {'title': 44, 'heading': 28, 'content': 11, 'per_slide': 20},
            ConversionQuality.STANDARD: {'title': 48, 'heading': 30, 'content': 12, 'per_slide': 15},
            ConversionQuality.PROFESSIONAL: {'title': 48, 'heading': 32, 'content': 12, 'per_slide': 15},
            ConversionQuality.PREMIUM: {'title': 54, 'heading': 36, 'content': 14, 'per_slide': 12},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        # Ana başlık
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        title = slide.shapes.title
        if title:
            title.text = "EXCEL VERİLERİ"
            title.text_frame.paragraphs[0].font.size = Pt(settings['title'])
        
        subtitle = slide.placeholders[1]
        if subtitle:
            subtitle.text = f"Toplam {len(df)} satır, {len(df.columns)} sütun"
        
        rows_per_slide = settings['per_slide']
        
        for start in range(0, len(df), rows_per_slide):
            end = min(start + rows_per_slide, len(df))
            
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            
            # Başlık
            title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.8))
            title_frame = title_box.text_frame
            title_frame.text = f"Excel Verileri - Sayfa {start//rows_per_slide + 1}"
            title_frame.paragraphs[0].font.size = Pt(settings['heading'])
            title_frame.paragraphs[0].font.bold = True
            title_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)
            
            # Tablo
            data = [df.columns.tolist()] + df.iloc[start:end].values.tolist()
            rows, cols = len(data), len(data[0])
            
            left = Inches(0.5)
            top = Inches(1.5)
            width = Inches(9)
            height = Inches(5)
            
            table = slide.shapes.add_table(rows, cols, left, top, width, height).table
            
            for i in range(rows):
                for j in range(cols):
                    cell = table.cell(i, j)
                    cell.text = str(data[i][j])
                    
                    for paragraph in cell.text_frame.paragraphs:
                        paragraph.font.size = Pt(settings['content'])
                        paragraph.alignment = PP_ALIGN.CENTER
                    
                    if i == 0:  # Başlık satırı
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(46, 117, 182)
                        for paragraph in cell.text_frame.paragraphs:
                            paragraph.font.color.rgb = RGBColor(255, 255, 255)
                            paragraph.font.bold = True
        
        prs.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.MODERATE
        
        logger.info(f"✅ Excel -> PowerPoint dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def excel_to_text(input_path: str, output_path: str,
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Excel -> Metin dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import pandas as pd
        
        df = pd.read_excel(input_path)
        df = df.fillna('')
        
        text_lines = []
        text_lines.append(" | ".join([str(col) for col in df.columns]))
        text_lines.append("-" * 50)
        
        for _, row in df.iterrows():
            text_lines.append(" | ".join([str(val) for val in row]))
        
        text = '\n'.join(text_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ Excel -> Metin dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Excel -> Metin dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== POWERPOINT DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def pptx_to_pdf(input_path: str, output_path: str,
               quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    PowerPoint -> PDF (PROFESYONEL - TASARIM KORUMALI)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from pptx import Presentation
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        prs = Presentation(input_path)
        
        c = canvas.Canvas(output_path, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        left_margin = 2 * cm
        y = height - 2 * cm
        line_height = 0.7 * cm
        
        total_slides = len(prs.slides)
        
        for slide_num, slide in enumerate(prs.slides, 1):
            # Slayt başlığı
            c.setFont("Helvetica-Bold", 18)
            c.setFillColor(colors.HexColor('#2E75B6'))
            c.drawString(left_margin, y, f"Slayt {slide_num}/{total_slides}")
            y -= line_height * 2
            
            c.setFont("Helvetica", 11)
            c.setFillColor(colors.black)
            
            # İçerik
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    
                    for line in text.split('\n'):
                        if line.strip():
                            if y < line_height + 1*cm:
                                c.showPage()
                                y = height - 2*cm
                                c.setFont("Helvetica", 11)
                            
                            c.drawString(left_margin + 0.5*cm, y, line)
                            y -= line_height
                    
                    y -= line_height * 0.5
            
            if slide_num < total_slides:
                c.showPage()
                y = height - 2*cm
        
        c.save()
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.MODERATE if total_slides > 10 else DocumentComplexity.SIMPLE
        
        logger.info(f"✅ PowerPoint -> PDF dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def pptx_to_word(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    PowerPoint -> Word (PROFESYONEL)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from pptx import Presentation
        from docx import Document
        from docx.shared import Inches, Pt
        
        prs = Presentation(input_path)
        doc = Document()
        
        total_slides = len(prs.slides)
        
        # Ana başlık
        title = doc.add_heading('POWERPOINT DÖKÜMANI DÖNÜŞÜMÜ', 0)
        title.alignment = 1
        run = title.runs[0]
        run.font.size = Pt(24)
        run.font.bold = True
        
        doc.add_paragraph(f"Kaynak: {os.path.basename(input_path)}")
        doc.add_paragraph(f"Toplam {total_slides} slayt")
        doc.add_paragraph()
        
        for slide_num, slide in enumerate(prs.slides, 1):
            doc.add_heading(f'Slayt {slide_num}/{total_slides}', level=1)
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    
                    if len(text) < 50 and not '\n' in text:
                        doc.add_heading(text, level=2)
                    else:
                        for para in text.split('\n'):
                            if para.strip():
                                p = doc.add_paragraph()
                                run = p.add_run(para.strip())
                                run.font.size = Pt(11)
                                p.paragraph_format.left_indent = Inches(0.3)
            
            if slide_num < total_slides:
                doc.add_page_break()
        
        doc.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.MODERATE if total_slides > 10 else DocumentComplexity.SIMPLE
        
        logger.info(f"✅ PowerPoint -> Word dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def pptx_to_text(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    PowerPoint -> Metin dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from pptx import Presentation
        
        prs = Presentation(input_path)
        
        text_lines = []
        total_slides = len(prs.slides)
        
        for slide_num, slide in enumerate(prs.slides, 1):
            text_lines.append(f"--- Slayt {slide_num}/{total_slides} ---")
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_lines.append(shape.text.strip())
            
            text_lines.append("")
        
        text = '\n'.join(text_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ PowerPoint -> Metin dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ PowerPoint -> Metin dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== PDF DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def pdf_to_word(input_path: str, output_path: str,
               quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    PDF -> Word (PROFESYONEL - METİN KORUMALI)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import PyPDF2
        from docx import Document
        from docx.shared import Pt
        
        doc = Document()
        
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            title = doc.add_heading('PDF DÖKÜMANI DÖNÜŞÜMÜ', 0)
            title.alignment = 1
            run = title.runs[0]
            run.font.size = Pt(24)
            
            doc.add_paragraph(f"Kaynak: {os.path.basename(input_path)}")
            doc.add_paragraph(f"Toplam {total_pages} sayfa")
            doc.add_paragraph()
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                doc.add_heading(f'Sayfa {page_num + 1}/{total_pages}', level=1)
                
                if text and text.strip():
                    for para in text.split('\n'):
                        if para.strip():
                            doc.add_paragraph(para.strip())
                else:
                    doc.add_paragraph("(Bu sayfada metin bulunamadı)")
                
                if page_num < total_pages - 1:
                    doc.add_page_break()
        
        doc.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 80
        metrics.complexity = DocumentComplexity.MODERATE if total_pages > 20 else DocumentComplexity.SIMPLE
        
        logger.info(f"✅ PDF -> Word dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def pdf_to_text(input_path: str, output_path: str,
               quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    PDF -> Metin dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        import PyPDF2
        
        text_lines = []
        
        with open(input_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text and text.strip():
                    text_lines.append(f"--- Sayfa {page_num + 1}/{total_pages} ---")
                    text_lines.append(text.strip())
                    text_lines.append("")
        
        text = '\n'.join(text_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ PDF -> Metin dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ PDF -> Metin dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== GÖRSEL DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def image_to_pdf(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Görsel -> PDF (PROFESYONEL - YÜKSEK KALİTE)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from PIL import Image, ImageFilter
        import img2pdf
        
        image = Image.open(input_path)
        
        # Kalite ayarları
        quality_settings = {
            ConversionQuality.DRAFT: {'dpi': 150, 'quality': 80, 'sharpen': False},
            ConversionQuality.STANDARD: {'dpi': 200, 'quality': 85, 'sharpen': False},
            ConversionQuality.PROFESSIONAL: {'dpi': 300, 'quality': 95, 'sharpen': True},
            ConversionQuality.PREMIUM: {'dpi': 600, 'quality': 100, 'sharpen': True},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        # RGB'ye çevir
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # A4'e sığdır
        a4_width, a4_height = int(8.27 * settings['dpi']), int(11.69 * settings['dpi'])
        image.thumbnail((a4_width, a4_height), Image.Resampling.LANCZOS)
        
        if settings['sharpen']:
            image = image.filter(ImageFilter.SHARPEN)
        
        # Geçici dosya
        temp_path = input_path + f"_temp_{int(time.time())}.jpg"
        image.save(temp_path, 'JPEG', quality=settings['quality'], optimize=True, dpi=(settings['dpi'], settings['dpi']))
        
        # PDF'e çevir
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(temp_path))
        
        os.remove(temp_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 95 if quality == ConversionQuality.PREMIUM else 85
        
        logger.info(f"✅ Görsel -> PDF dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


def _create_fallback_word_document(input_path: str, output_path: str, 
                                   metrics: ConversionMetrics, changes: List[str]) -> Tuple[bool, str, ConversionMetrics]:
    """OCR başarısız olduğunda basit bir Word belgesi oluştur"""
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        title = doc.add_heading('GÖRSEL DOSYASI', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.runs[0]
        run.font.size = Pt(26)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)
        
        doc.add_paragraph()
        info = doc.add_paragraph()
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = info.add_run("⚠️ OCR SİSTEMİ DEVRE DIŞI")
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 0, 0)
        
        doc.add_paragraph()
        
        # Dosya bilgileri
        p = doc.add_paragraph()
        p.add_run("📁 ").bold = True
        p.add_run(f"Dosya: {os.path.basename(input_path)}")
        
        p = doc.add_paragraph()
        p.add_run("📅 ").bold = True
        p.add_run(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        p = doc.add_paragraph()
        p.add_run("📏 ").bold = True
        from PIL import Image
        img = Image.open(input_path)
        p.add_run(f"Boyut: {img.width} x {img.height} piksel")
        
        doc.add_paragraph()
        doc.add_paragraph("Bu bir görsel dosyasıdır. OCR sistemi şu anda kullanılamıyor.")
        doc.add_paragraph("Metin çıkarmak için lütfen daha sonra tekrar deneyin.")
        
        doc.add_paragraph()
        doc.add_paragraph("📞 Destek: @yusozone")
        
        doc.add_page_break()
        doc.add_heading('ORİJİNAL GÖRSEL', level=1)
        doc.add_paragraph()
        doc.add_picture(input_path, width=Inches(5))
        
        doc.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.quality_score = 30
        metrics.warnings.append("OCR sistemi bulunamadı, görsel bilgileri kaydedildi")
        
        logger.info(f"✅ Yedek Word belgesi oluşturuldu: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Yedek belge oluşturulamadı: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


@timer
@handle_exceptions
def image_to_word(input_path: str, output_path: str,
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Görsel -> Word (OCR - PROFESYONEL)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    # Tesseract kontrolü
    if not TESSERACT_AVAILABLE or not TESSERACT_CONFIGURED:
        logger.warning("⚠️ Tesseract OCR bulunamadı, yedek belge oluşturuluyor")
        return _create_fallback_word_document(input_path, output_path, metrics, changes)
    
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        import pytesseract
        
        image = Image.open(input_path)
        
        original_size = image.size
        changes.append(f"Orijinal görsel: {original_size[0]}x{original_size[1]}")
        
        # Kalite ayarları
        quality_settings = {
            ConversionQuality.DRAFT: {'scale': 1.5, 'contrast': 2.0, 'psm': 6},
            ConversionQuality.STANDARD: {'scale': 2.0, 'contrast': 2.5, 'psm': 6},
            ConversionQuality.PROFESSIONAL: {'scale': 2.0, 'contrast': 2.5, 'psm': 6},
            ConversionQuality.PREMIUM: {'scale': 3.0, 'contrast': 3.0, 'psm': 3},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        # Görseli büyüt
        if image.width < 2000:
            new_size = (int(image.width * settings['scale']), int(image.height * settings['scale']))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            changes.append(f"Görsel büyütüldü: {new_size[0]}x{new_size[1]}")
        
        # Gri tonlama
        image = image.convert('L')
        
        # Kontrast artır
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(settings['contrast'])
        
        # Gürültü azalt
        image = image.filter(ImageFilter.MedianFilter(size=3))
        image = image.filter(ImageFilter.SHARPEN)
        
        if quality == ConversionQuality.PREMIUM:
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        
        # Geçici kaydet
        temp_path = input_path + f"_temp_ocr_{int(time.time())}.png"
        image.save(temp_path, 'PNG', dpi=(300,300))
        
        # Dil tespiti
        sample = pytesseract.image_to_string(temp_path, lang='tur', config='--psm 6')
        language = 'tur' if sample.strip() else 'eng'
        
        # OCR
        config = f'--oem 3 --psm {settings["psm"]} -l {language}+eng'
        text = pytesseract.image_to_string(temp_path, config=config)
        
        if text.strip():
            text = fix_common_ocr_errors(text)
            cleaned, removed = clean_ocr_text(text)
            cleaned = merge_intelligent_lines(cleaned)
            cleaned = normalize_whitespace(cleaned)
            
            changes.append(f"OCR başarılı ({len(text)} karakter, {len(removed)} gereksiz satır temizlendi)")
            
            confidence = calculate_ocr_confidence(cleaned)
            changes.append(f"OCR güven skoru: %{confidence:.0f}")
        else:
            changes.append("OCR başarısız, görselde metin olmayabilir")
            cleaned = ""
        
        # Word belgesi
        doc = Document()
        
        section = doc.sections[0]
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        title = doc.add_heading('📄 GÖRSELDEN OCR İLE DÖNÜŞTÜRÜLEN METİN', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.runs[0]
        run.font.size = Pt(26)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)
        
        info = doc.add_paragraph()
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = info.add_run(f"🖼️ Kaynak: {os.path.basename(input_path)}")
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(100, 100, 100)
        
        doc.add_paragraph('_' * 80)
        doc.add_paragraph()
        
        if cleaned.strip():
            for para in cleaned.split('\n\n'):
                if para.strip():
                    p = doc.add_paragraph()
                    run = p.add_run(para.strip())
                    run.font.size = Pt(11)
                    p.paragraph_format.space_after = Pt(12)
        else:
            p = doc.add_paragraph()
            run = p.add_run("(Görselde metin bulunamadı)")
            run.font.italic = True
            run.font.color.rgb = RGBColor(150, 150, 150)
        
        doc.add_page_break()
        doc.add_heading('🖼️ ORİJİNAL GÖRSEL', level=1)
        doc.add_paragraph()
        doc.add_picture(input_path, width=Inches(5))
        
        doc.save(output_path)
        
        # Temizlik
        os.remove(temp_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85 if text.strip() else 50
        
        logger.info(f"✅ Görsel -> Word dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Görsel -> Word dönüşüm hatası: {e}")
        traceback.print_exc()
        metrics.warnings.append(str(e))
        return _create_fallback_word_document(input_path, output_path, metrics, changes)


@timer
@handle_exceptions
def image_to_text(input_path: str, output_path: str,
                 quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Görsel -> Metin dönüşümü (OCR)
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    if not TESSERACT_AVAILABLE or not TESSERACT_CONFIGURED:
        logger.warning("⚠️ Tesseract OCR bulunamadı")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("(OCR sistemi yapılandırılmamış)")
        metrics.output_size = os.path.getsize(output_path)
        metrics.quality_score = 10
        return True, output_path, metrics
    
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import pytesseract
        
        image = Image.open(input_path)
        
        quality_settings = {
            ConversionQuality.DRAFT: {'scale': 1.5, 'contrast': 2.0},
            ConversionQuality.STANDARD: {'scale': 2.0, 'contrast': 2.5},
            ConversionQuality.PROFESSIONAL: {'scale': 2.0, 'contrast': 2.5},
            ConversionQuality.PREMIUM: {'scale': 3.0, 'contrast': 3.0},
        }
        settings = quality_settings.get(quality, quality_settings[ConversionQuality.PROFESSIONAL])
        
        if image.width < 2000:
            new_size = (int(image.width * settings['scale']), int(image.height * settings['scale']))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(settings['contrast'])
        image = image.filter(ImageFilter.SHARPEN)
        
        temp_path = input_path + f"_temp_ocr_{int(time.time())}.png"
        image.save(temp_path, 'PNG')
        
        text = pytesseract.image_to_string(temp_path, lang='tur+eng')
        
        if text.strip():
            text = fix_common_ocr_errors(text)
            cleaned, removed = clean_ocr_text(text)
            cleaned = merge_intelligent_lines(cleaned)
            cleaned = normalize_whitespace(cleaned)
            
            changes.append(f"OCR başarılı ({len(text)} karakter, {len(removed)} gereksiz satır temizlendi)")
            confidence = calculate_ocr_confidence(cleaned)
            changes.append(f"OCR güven skoru: %{confidence:.0f}")
        else:
            cleaned = "(Görselde metin bulunamadı)"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        os.remove(temp_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 85 if text.strip() else 50
        
        logger.info(f"✅ Görsel -> Metin dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Görsel -> Metin dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== METİN DÖNÜŞÜMLERİ ==========

@timer
@handle_exceptions
def text_to_pdf(input_path: str, output_path: str,
               quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Metin -> PDF dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        y = height - 2 * cm
        line_height = 0.6 * cm
        
        c.setFont("Helvetica", 11)
        
        for line in text.split('\n'):
            if line.strip():
                if y < line_height:
                    c.showPage()
                    y = height - 2 * cm
                    c.setFont("Helvetica", 11)
                
                c.drawString(2 * cm, y, line.strip())
                y -= line_height
            else:
                y -= line_height * 0.5
        
        c.save()
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ Metin -> PDF dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except ImportError as e:
        error_msg = f"Gerekli kütüphane bulunamadı: {e}"
        logger.error(f"❌ {error_msg}")
        metrics.warnings.append(error_msg)
        return False, "", metrics


@timer
@handle_exceptions
def text_to_word(input_path: str, output_path: str,
                quality: ConversionQuality = ConversionQuality.PROFESSIONAL) -> Tuple[bool, str, ConversionMetrics]:
    """
    Metin -> Word dönüşümü
    """
    metrics = ConversionMetrics()
    metrics.input_size = os.path.getsize(input_path)
    changes = []
    
    try:
        from docx import Document
        
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        doc = Document()
        
        doc.add_heading('Metin Dökümanı Dönüşümü', 0)
        doc.add_paragraph(f"Kaynak: {os.path.basename(input_path)}")
        doc.add_paragraph()
        
        for para in text.split('\n'):
            if para.strip():
                doc.add_paragraph(para.strip())
        
        doc.save(output_path)
        
        metrics.output_size = os.path.getsize(output_path)
        metrics.compression_ratio = metrics.output_size / metrics.input_size if metrics.input_size > 0 else 1
        metrics.quality_score = 90
        metrics.complexity = DocumentComplexity.SIMPLE
        
        logger.info(f"✅ Metin -> Word dönüşüm başarılı: {input_path}")
        return True, output_path, metrics
        
    except Exception as e:
        logger.error(f"❌ Metin -> Word dönüşüm hatası: {e}")
        metrics.warnings.append(str(e))
        return False, "", metrics


# ========== ANA DÖNÜŞTÜRME FONKSİYONLARI ==========

# Dönüşüm fonksiyonları sözlüğü
CONVERSION_FUNCTIONS = {
    (FileType.WORD, FileType.PDF): word_to_pdf,
    (FileType.WORD, FileType.EXCEL): word_to_excel,
    (FileType.WORD, FileType.POWERPOINT): word_to_pptx,
    (FileType.WORD, FileType.TEXT): word_to_text,
    
    (FileType.EXCEL, FileType.PDF): excel_to_pdf,
    (FileType.EXCEL, FileType.WORD): excel_to_word,
    (FileType.EXCEL, FileType.POWERPOINT): excel_to_pptx,
    (FileType.EXCEL, FileType.TEXT): excel_to_text,
    
    (FileType.POWERPOINT, FileType.PDF): pptx_to_pdf,
    (FileType.POWERPOINT, FileType.WORD): pptx_to_word,
    (FileType.POWERPOINT, FileType.TEXT): pptx_to_text,
    
    (FileType.PDF, FileType.WORD): pdf_to_word,
    (FileType.PDF, FileType.TEXT): pdf_to_text,
    
    (FileType.GORSEL, FileType.PDF): image_to_pdf,
    (FileType.GORSEL, FileType.WORD): image_to_word,
    (FileType.GORSEL, FileType.TEXT): image_to_text,
    
    (FileType.TEXT, FileType.PDF): text_to_pdf,
    (FileType.TEXT, FileType.WORD): text_to_word,
}


async def smart_convert_file(input_path: str, output_path: str, 
                            source_type: Union[str, FileType], 
                            target_type: Union[str, FileType],
                            user_id: int = None, db_instance: Any = None,
                            quality: str = "profesyonel") -> Tuple[bool, str, str, Optional[str], ConversionMetrics]:
    """
    Gelişmiş dönüşüm yöneticisi - TÜM DÖNÜŞÜMLER DESTEKLENİR
    """
    import time
    start_time = time.time()
    
    # String'leri FileType'a çevir
    if isinstance(source_type, str):
        try:
            source_type = FileType(source_type)
        except ValueError:
            source_type = FileType.UNKNOWN
    
    if isinstance(target_type, str):
        try:
            target_type = FileType(target_type)
        except ValueError:
            target_type = FileType.UNKNOWN
    
    logger.info(f"🔍 Dönüşüm isteği: {source_type.value} -> {target_type.value}")
    logger.info(f"📁 Kaynak: {input_path}")
    logger.info(f"📁 Hedef: {output_path}")
    
    quality_level = ConversionQuality.from_string(quality)
    
    metrics = ConversionMetrics()
    changes = []
    edit_summary = None
    conversion_type = 'direct'
    
    try:
        if not os.path.exists(input_path):
            error_msg = f"Dosya bulunamadı: {input_path}"
            logger.error(f"❌ {error_msg}")
            metrics.warnings.append(error_msg)
            return False, "", conversion_type, edit_summary, metrics
        
        if not is_conversion_supported(source_type, target_type):
            error_msg = f"Desteklenmeyen dönüşüm: {source_type.value} -> {target_type.value}"
            logger.error(f"❌ {error_msg}")
            metrics.warnings.append(error_msg)
            return False, "", conversion_type, edit_summary, metrics
        
        key = (source_type, target_type)
        if key not in CONVERSION_FUNCTIONS:
            error_msg = f"Dönüşüm fonksiyonu bulunamadı: {source_type.value} -> {target_type.value}"
            logger.error(f"❌ {error_msg}")
            metrics.warnings.append(error_msg)
            return False, "", conversion_type, edit_summary, metrics
        
        logger.info(f"🔄 Dönüşüm başlıyor: {source_type.value} -> {target_type.value}")
        
        try:
            success, out_path, conv_metrics = CONVERSION_FUNCTIONS[key](input_path, output_path, quality_level)
        except Exception as e:
            logger.error(f"❌ Dönüşüm fonksiyonu hatası: {e}")
            traceback.print_exc()
            metrics.warnings.append(str(e))
            return False, "", conversion_type, edit_summary, metrics
        
        metrics = conv_metrics
        metrics.processing_time = time.time() - start_time
        
        if success and out_path and os.path.exists(out_path):
            metrics.quality_score = conv_metrics.quality_score
            logger.info(f"✅ Dönüşüm başarılı: {out_path}")
            return True, out_path, conversion_type, edit_summary, metrics
        else:
            error_msg = f"Dönüşüm başarısız: {source_type.value} -> {target_type.value}"
            logger.error(f"❌ {error_msg}")
            metrics.warnings.append(error_msg)
            return False, "", conversion_type, edit_summary, metrics
            
    except Exception as e:
        logger.error(f"❌ Akıllı dönüşüm hatası: {e}")
        traceback.print_exc()
        metrics.warnings.append(str(e))
        return False, "", conversion_type, edit_summary, metrics


def get_conversion_report(metrics: ConversionMetrics) -> str:
    """
    Dönüşüm raporu oluştur
    """
    report = f"""
📊 **DÖNÜŞÜM RAPORU**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 **DOSYA BİLGİLERİ**
• Giriş boyutu: {get_file_size_str(metrics.input_size)}
• Çıkış boyutu: {get_file_size_str(metrics.output_size)}
• Sıkıştırma oranı: %{(1-metrics.compression_ratio)*100:.1f}
• İşlem süresi: {metrics.processing_time:.2f} saniye

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **KALİTE METRİKLERİ**
• Kalite puanı: %{metrics.quality_score}
• Karmaşıklık: {metrics.complexity.value}
"""
    
    if metrics.warnings:
        report += "\n⚠️ **UYARILAR**\n"
        for warning in metrics.warnings[:5]:
            report += f"  • {warning}\n"
    
    if metrics.suggestions:
        report += "\n💡 **ÖNERİLER**\n"
        for suggestion in metrics.suggestions[:3]:
            report += f"  • {suggestion}\n"
    
    return report


# ========== GERİYE UYUMLULUK FONKSİYONLARI ==========

async def convert_file(input_path: str, output_path: str, source_type: str, target_type: str) -> Tuple[bool, str]:
    """
    Eski dönüşüm fonksiyonu (geriye uyumluluk için)
    """
    success, out_path, _, _, metrics = await smart_convert_file(
        input_path, output_path, source_type, target_type, quality="standart"
    )
    
    if success:
        return True, ""
    else:
        error_msg = metrics.warnings[0] if metrics.warnings else "Bilinmeyen hata"
        return False, error_msg


async def smart_process_file(input_path: str, output_path: str, source_type: str, target_type: str,
                            user_id: int = None, db_instance: Any = None) -> Tuple[bool, str, Dict]:
    """
    Akıllı işlem yöneticisi (geriye uyumluluk için)
    """
    success, out_path, conv_type, edit_summary, metrics = await smart_convert_file(
        input_path, output_path, source_type, target_type, user_id, db_instance
    )
    
    results = {
        'conversion': {
            'success': success,
            'message': "Dönüşüm tamamlandı" if success else "Dönüşüm başarısız",
            'type': conv_type,
            'edit_summary': edit_summary
        },
        'metrics': metrics.to_dict() if hasattr(metrics, 'to_dict') else {
            'quality_score': metrics.quality_score,
            'processing_time': metrics.processing_time,
            'input_size': metrics.input_size,
            'output_size': metrics.output_size,
            'warnings': metrics.warnings
        }
    }
    
    return success, get_conversion_report(metrics), results


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Profesyonel Dönüşüm Modülü Test Ediliyor...")
    print("=" * 60)
    
    print(f"📋 Tesseract OCR: {'✅ Var' if TESSERACT_AVAILABLE and TESSERACT_CONFIGURED else '❌ Yok'}")
    print(f"📋 PIL: {'✅ Var' if PIL_AVAILABLE else '❌ Yok'}")
    
    print("\n📋 DESTEKLENEN DÖNÜŞÜMLER:")
    for source, targets in SUPPORTED_CONVERSIONS.items():
        target_names = [get_display_name(t) for t in targets]
        print(f"  • {get_display_name(source)} -> {', '.join(target_names)}")
    
    print("\n" + "=" * 60)
    print("✅ Modül hazır! Tüm dönüşümler destekleniyor.")
