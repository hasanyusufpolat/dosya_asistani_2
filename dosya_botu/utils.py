"""
PROFESYONEL YARDIMCI FONKSİYONLAR MODÜLÜ
Dosya işleme, formatlama, temizlik ve raporlama fonksiyonları
Tüm modüller için ortak yardımcı araçlar
GELİŞMİŞ: OCR metin temizleme, akıllı satır birleştirme, güven skorlaması
"""

import os
import re
import json
import shutil
import hashlib
import datetime
import unicodedata
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

# ========== DOSYA İŞLEMLERİ ==========

def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Güvenli dosya adı oluştur (gelişmiş)
    
    Args:
        filename: Orijinal dosya adı
        max_length: Maksimum uzunluk
    
    Returns:
        Güvenli dosya adı
    """
    # Geçersiz karakterleri temizle
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Kontrol karakterlerini temizle
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Baştaki ve sondaki boşlukları temizle
    filename = filename.strip()
    
    # Nokta ile başlıyorsa düzelt
    if filename.startswith('.'):
        filename = '_' + filename
    
    # Uzunluğu sınırla
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        if len(ext) > 10:  # Çok uzun uzantı
            filename = filename[:max_length]
        else:
            available = max_length - len(ext)
            if available > 10:
                filename = name[:available] + ext
            else:
                filename = filename[:max_length]
    
    return filename

def format_size(size_bytes: int, decimal_places: int = 1) -> str:
    """
    Byte'ı okunabilir formata çevir (gelişmiş)
    
    Args:
        size_bytes: Byte cinsinden boyut
        decimal_places: Ondalık basamak sayısı
    
    Returns:
        Formatlanmış boyut (örn: 1.5 MB)
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.{decimal_places}f} {units[unit_index]}"

def clean_temp_files(user_id: Union[int, str], *file_paths: str) -> int:
    """
    Geçici dosyaları temizle (gelişmiş)
    
    Args:
        user_id: Kullanıcı ID (log için)
        *file_paths: Temizlenecek dosya yolları
    
    Returns:
        Silinen dosya sayısı
    """
    deleted = 0
    errors = 0
    
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                deleted += 1
        except PermissionError:
            errors += 1
        except Exception as e:
            errors += 1
    
    if deleted > 0:
        print(f"🧹 {deleted} geçici dosya temizlendi: {user_id}")
    
    if errors > 0:
        print(f"⚠️ {errors} dosya temizlenirken hata oluştu: {user_id}")
    
    return deleted

def clean_temp_directory(directory: str, max_age_hours: int = 24) -> Tuple[int, int]:
    """
    Geçici klasörü temizle (belirli saatten eski dosyalar)
    
    Args:
        directory: Temizlenecek klasör
        max_age_hours: Maksimum saat (bu saatten eski dosyalar silinir)
    
    Returns:
        (silinen_dosya_sayısı, hata_sayısı)
    """
    if not os.path.exists(directory):
        return 0, 0
    
    now = datetime.datetime.now()
    deleted = 0
    errors = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        try:
            if os.path.isfile(file_path):
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                age_hours = (now - file_mtime).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    os.remove(file_path)
                    deleted += 1
        except Exception:
            errors += 1
    
    if deleted > 0:
        print(f"🧹 {deleted} eski geçici dosya temizlendi: {directory}")
    
    return deleted, errors

def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Dosya hash'i hesapla (değişiklik kontrolü için)
    
    Args:
        file_path: Dosya yolu
        algorithm: Hash algoritması ('md5', 'sha1', 'sha256')
    
    Returns:
        Hash değeri
    """
    if not os.path.exists(file_path):
        return ""
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def get_file_extension(file_path: str) -> str:
    """
    Dosya uzantısını küçük harfle döndür
    
    Args:
        file_path: Dosya yolu
    
    Returns:
        Uzantı (örn: '.pdf')
    """
    return os.path.splitext(file_path)[1].lower()

def get_file_name_without_extension(file_path: str) -> str:
    """
    Dosya adını uzantısız döndür
    
    Args:
        file_path: Dosya yolu
    
    Returns:
        Dosya adı (uzantısız)
    """
    return os.path.splitext(os.path.basename(file_path))[0]

def ensure_directory(directory: str) -> bool:
    """
    Klasörün var olduğundan emin ol (yoksa oluştur)
    
    Args:
        directory: Klasör yolu
    
    Returns:
        Başarılı mı
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception:
        return False


# ========== OCR VE METİN TEMİZLEME FONKSİYONLARI (YENİ) ==========

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
        r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?',  # Saat: 14:30, 2:30 PM
        r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',  # Tarih: 15.03.2024
        r'Volte?\s*\d{1,2}:\d{2}',  # Volte 14:30
        r'(?:Turkcell|Vodafone|Türk Telekom|Türkcell)\s*\d{1,2}:\d{2}',
        r'Ekran\s*(?:Alıntısı|Görüntüsü|Fotoğrafı)',  # Ekran Alıntısı
        r'Screen\s*(?:Shot|Capture)',  # Screen Shot/Capture
        r'Screenshot',  # Screenshot
        r'Captur(?:e|ed)',  # Capture/Captured
        r'^\s*\d+\s*$',  # Sadece rakam
        r'^\s*[•\-*]\s*$',  # Sadece madde işareti
        r'^\s*[|\\/]\s*$',  # Sadece çizgi
        r'\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}',  # Tarih formatı
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        r'(?:Sayfa|Page)\s+\d+\s*(?:/|of)\s*\d+',  # Sayfa numaraları
        r'^\s*[_\-\=\*]{3,}\s*$',  # Çizgiler
        r'^\s*[▌▐▀▄█▓▒░]\s*$',  # Blok karakterler
        r'^\s*[📱📞📧📅📆📊📈📉📋📝✅❌⚠️🔴🟡🟢🔵]',  # Emoji'ler
        r'^\s*[⏰⏱️⏲️🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛]',  # Saat emojileri
    ]
    
    # Çok kısa satırları filtrele (3 karakterden az)
    for line in lines:
        line = line.strip()
        
        # Boş satırı kontrol et
        if not line:
            cleaned_lines.append('')
            continue
        
        # Çok kısa satırları filtrele
        if len(line) < 3:
            removed_lines.append(line)
            continue
        
        # Gereksiz desenleri kontrol et
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
    
    # Ortalama kelime uzunluğu (normalde 4-8 arası olmalı)
    avg_word_length = total_chars / total_words
    
    # Anormal kısa kelimeler
    very_short_words = sum(1 for w in words if len(w) <= 2)
    short_ratio = very_short_words / total_words
    
    # Anormal uzun kelimeler (OCR hataları genelde uzun kelimeler oluşturur)
    very_long_words = sum(1 for w in words if len(w) > 20)
    long_ratio = very_long_words / total_words
    
    # Özel karakter oranı
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / total_chars if total_chars > 0 else 0
    
    # Rakam oranı (çok fazla rakam OCR hatası olabilir)
    digit_chars = sum(1 for c in text if c.isdigit())
    digit_ratio = digit_chars / total_chars if total_chars > 0 else 0
    
    # Büyük harf oranı (çok fazla büyük harf OCR hatası olabilir)
    uppercase_chars = sum(1 for c in text if c.isupper())
    uppercase_ratio = uppercase_chars / total_chars if total_chars > 0 else 0
    
    # Güven skoru hesapla
    confidence = 100
    
    # Ortalama kelime uzunluğu çok düşükse
    if avg_word_length < 3:
        confidence -= 30
    elif avg_word_length < 4:
        confidence -= 15
    elif avg_word_length > 15:
        confidence -= 20
    
    # Çok fazla kısa kelime varsa
    if short_ratio > 0.3:
        confidence -= 25
    elif short_ratio > 0.2:
        confidence -= 15
    
    # Çok fazla uzun kelime varsa
    if long_ratio > 0.1:
        confidence -= 20
    elif long_ratio > 0.05:
        confidence -= 10
    
    # Çok fazla özel karakter varsa
    if special_ratio > 0.2:
        confidence -= 20
    elif special_ratio > 0.1:
        confidence -= 10
    
    # Çok fazla rakam varsa (sayısal belgeler hariç)
    if digit_ratio > 0.3:
        confidence -= 15
    elif digit_ratio > 0.2:
        confidence -= 5
    
    # Çok fazla büyük harf varsa
    if uppercase_ratio > 0.5:
        confidence -= 15
    elif uppercase_ratio > 0.3:
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
        
        # Boş satır
        if not current_line:
            merged.append('')
            i += 1
            continue
        
        # Sonraki satır var mı?
        if i < len(lines) - 1:
            next_line = lines[i+1].strip()
            
            # Eğer sonraki satır küçük harfle başlıyorsa ve
            # mevcut satır noktalama işareti ile bitmiyorsa
            if next_line and next_line[0].islower() and not current_line[-1] in '.!?:;,':
                # Birleştir
                if current_line.endswith('-'):
                    # Kelime bölünmesi
                    current_line = current_line[:-1] + next_line
                else:
                    current_line += ' ' + next_line
                i += 2  # Bir sonraki satırı atla
                continue
        
        merged.append(current_line)
        i += 1
    
    return '\n'.join(merged)


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
    
    # Yaygın hata düzeltmeleri
    replacements = [
        # Sayısal hatalar
        (r'\b0\b', 'O'),  # Tek başına 0 -> O
        (r'\b1\b', 'l'),  # Tek başına 1 -> l
        (r'\b5\b', 'S'),  # Tek başına 5 -> S
        
        # Karakter karışıklıkları
        ('§', 'S'),  # Paragraf işareti -> S
        ('©', 'C'),  # Copyright -> C
        ('®', 'R'),  # Registered -> R
        ('™', 'TM'),  # Trademark -> TM
        ('•', '-'),  # Madde işareti -> -
        ('·', '.'),  # Orta nokta -> .
        ('…', '...'),  # Üç nokta -> ...
        ('–', '-'),  # Uzun tire -> -
        ('—', '-'),  # Uzun tire -> -
        ('"', '"'),  # Tırnak işareti
        ('"', '"'),  # Tırnak işareti
        ('´', "'"),  # Kesme işareti
        ('`', "'"),  # Kesme işareti
        
        # Türkçe karakter düzeltmeleri
        ('Ý', 'İ'),  # Y. harfi -> İ
        ('Þ', 'Ş'),  # TH -> Ş
        ('ð', 'ğ'),  # Ð -> ğ
        ('ý', 'ı'),  # ý -> ı
        ('Ã', 'Ç'),  # Ã -> Ç
        ('ã', 'ç'),  # ã -> ç
        ('Ä', 'Ö'),  # Ä -> Ö
        ('ä', 'ö'),  # ä -> ö
        ('Ü', 'Ü'),  # Ü zaten doğru
        ('ü', 'ü'),  # ü zaten doğru
        ('Ä', 'Ö'),  # Ä -> Ö
        ('ä', 'ö'),  # ä -> ö
        ('Ë', 'E'),  # Ë -> E
        ('ë', 'e'),  # ë -> e
        
        # İngilizce karakter düzeltmeleri
        ('À', 'A'), ('Á', 'A'), ('Â', 'A'), ('Ã', 'A'),
        ('à', 'a'), ('á', 'a'), ('â', 'a'), ('ã', 'a'),
        ('È', 'E'), ('É', 'E'), ('Ê', 'E'), ('Ë', 'E'),
        ('è', 'e'), ('é', 'e'), ('ê', 'e'), ('ë', 'e'),
        ('Ì', 'I'), ('Í', 'I'), ('Î', 'I'), ('Ï', 'I'),
        ('ì', 'i'), ('í', 'i'), ('î', 'i'), ('ï', 'i'),
        ('Ò', 'O'), ('Ó', 'O'), ('Ô', 'O'), ('Õ', 'O'),
        ('ò', 'o'), ('ó', 'o'), ('ô', 'o'), ('õ', 'o'),
        ('Ù', 'U'), ('Ú', 'U'), ('Û', 'U'), ('Ü', 'U'),
        ('ù', 'u'), ('ú', 'u'), ('û', 'u'), ('ü', 'u'),
        ('Ñ', 'N'), ('ñ', 'n'),
    ]
    
    for old, new in replacements:
        if isinstance(old, tuple) or old.startswith('\\'):
            # Regex pattern
            text = re.sub(old, new, text)
        else:
            # Direkt değiştirme
            text = text.replace(old, new)
    
    return text


def normalize_whitespace_advanced(text: str) -> str:
    """
    Gelişmiş boşluk normalizasyonu
    
    Args:
        text: Ham metin
    
    Returns:
        Düzenlenmiş metin
    """
    if not text:
        return ""
    
    # Fazla boşlukları temizle
    text = re.sub(r' +', ' ', text)
    
    # Satır sonlarındaki boşlukları temizle
    text = re.sub(r' +\n', '\n', text)
    
    # Fazla satır sonlarını temizle (3'ten fazla satır sonu -> 2 satır sonu)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    # Paragraf başlarındaki boşlukları temizle
    text = re.sub(r'\n +', '\n', text)
    
    # Cümle sonlarındaki fazla boşlukları temizle
    text = re.sub(r'\. +', '. ', text)
    text = re.sub(r'\! +', '! ', text)
    text = re.sub(r'\? +', '? ', text)
    
    return text.strip()


def is_meaningful_text(text: str, min_words: int = 3) -> bool:
    """
    Metnin anlamlı olup olmadığını kontrol et
    
    Args:
        text: Kontrol edilecek metin
        min_words: Minimum anlamlı kelime sayısı
    
    Returns:
        Anlamlı mı?
    """
    if not text or len(text) < 10:
        return False
    
    words = text.split()
    
    # Çok az kelime varsa
    if len(words) < min_words:
        return False
    
    # Sadece rakam ve sembollerden oluşuyorsa
    alpha_ratio = sum(1 for c in text if c.isalpha()) / len(text) if len(text) > 0 else 0
    if alpha_ratio < 0.3:  # %30'dan az harf varsa
        return False
    
    return True


def extract_clean_text(text: str) -> str:
    """
    OCR metnini tamamen temizle ve düzenle (tüm adımlar)
    
    Args:
        text: Ham OCR metni
    
    Returns:
        Temizlenmiş metin
    """
    if not text:
        return ""
    
    # 1. Yaygın OCR hatalarını düzelt
    text = fix_common_ocr_errors(text)
    
    # 2. Gereksiz satırları filtrele
    text, removed = clean_ocr_text(text)
    
    # 3. Boşlukları normalize et
    text = normalize_whitespace_advanced(text)
    
    # 4. Akıllı satır birleştirme
    text = merge_intelligent_lines(text)
    
    return text


# ========== TARİH/SAAT İŞLEMLERİ ==========

def get_time_string(format: str = "%d.%m.%Y %H:%M:%S") -> str:
    """
    Şu anki zamanı string olarak döndür
    
    Args:
        format: Tarih formatı
    
    Returns:
        Formatlanmış tarih
    """
    return datetime.datetime.now().strftime(format)

def get_date_string(format: str = "%d.%m.%Y") -> str:
    """
    Şu anki tarihi string olarak döndür
    
    Args:
        format: Tarih formatı
    
    Returns:
        Formatlanmış tarih
    """
    return datetime.datetime.now().strftime(format)

def format_datetime(dt: datetime.datetime, format: str = "%d.%m.%Y %H:%M:%S") -> str:
    """
    Datetime nesnesini formatla
    
    Args:
        dt: Datetime nesnesi
        format: Tarih formatı
    
    Returns:
        Formatlanmış tarih
    """
    if dt is None:
        return ""
    return dt.strftime(format)

def parse_date(date_str: str) -> Optional[datetime.datetime]:
    """
    Tarih string'ini parse et
    
    Args:
        date_str: Tarih string'i (örn: "15.03.2024")
    
    Returns:
        Datetime nesnesi veya None
    """
    formats = [
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def get_time_difference(start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None) -> str:
    """
    İki zaman arasındaki farkı okunabilir formatta döndür
    
    Args:
        start_time: Başlangıç zamanı
        end_time: Bitiş zamanı (None ise şimdi)
    
    Returns:
        Okunabilir zaman farkı (örn: "2 dakika 15 saniye")
    """
    if end_time is None:
        end_time = datetime.datetime.now()
    
    diff = end_time - start_time
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return f"{seconds} saniye"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes} dakika {seconds} saniye"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} saat {minutes} dakika"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} gün {hours} saat"


# ========== METİN İŞLEMLERİ (GELİŞTİRİLMİŞ) ==========

def slugify(text: str) -> str:
    """
    Metni URL dostu formata çevir
    
    Args:
        text: Orijinal metin
    
    Returns:
        Slug formatında metin
    """
    # Türkçe karakterleri dönüştür
    text = text.replace('ı', 'i').replace('İ', 'I')
    text = text.replace('ğ', 'g').replace('Ğ', 'G')
    text = text.replace('ü', 'u').replace('Ü', 'U')
    text = text.replace('ş', 's').replace('Ş', 'S')
    text = text.replace('ö', 'o').replace('Ö', 'O')
    text = text.replace('ç', 'c').replace('Ç', 'C')
    
    # Normalize et
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # Sadece harf, rakam ve boşluk bırak
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Boşlukları tire ile değiştir
    text = re.sub(r'[-\s]+', '-', text)
    
    return text.lower().strip('-')

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Metni belirli uzunlukta kes
    
    Args:
        text: Orijinal metin
        max_length: Maksimum uzunluk
        suffix: Eklenecek son ek
    
    Returns:
        Kısaltılmış metin
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def clean_text(text: str, remove_extra_spaces: bool = True, aggressive: bool = False) -> str:
    """
    Metni temizle (gelişmiş)
    
    Args:
        text: Orijinal metin
        remove_extra_spaces: Fazla boşlukları temizle
        aggressive: Agresif temizleme modu (OCR için)
    
    Returns:
        Temizlenmiş metin
    """
    if not text:
        return ""
    
    if aggressive:
        # OCR için agresif temizleme
        return extract_clean_text(text)
    
    if remove_extra_spaces:
        # Normal temizleme
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Satırdaki fazla boşlukları temizle
            clean_line = ' '.join(line.split())
            if clean_line:
                cleaned_lines.append(clean_line)
        
        return '\n'.join(cleaned_lines)
    
    return text

def extract_numbers(text: str) -> List[str]:
    """
    Metinden sayıları çıkar
    
    Args:
        text: Orijinal metin
    
    Returns:
        Sayı listesi
    """
    return re.findall(r'\d+', text)

def extract_emails(text: str) -> List[str]:
    """
    Metinden email adreslerini çıkar
    
    Args:
        text: Orijinal metin
    
    Returns:
        Email listesi
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)

def extract_urls(text: str) -> List[str]:
    """
    Metinden URL'leri çıkar
    
    Args:
        text: Orijinal metin
    
    Returns:
        URL listesi
    """
    pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[^\s]*)?'
    return re.findall(pattern, text)

def normalize_phone(phone: str) -> str:
    """
    Telefon numarasını normalize et
    
    Args:
        phone: Orijinal telefon numarası
    
    Returns:
        Normalize edilmiş telefon (örn: 05321234567)
    """
    # Sadece rakamları al
    digits = re.sub(r'\D', '', phone)
    
    # 10 haneli ise başına 0 ekle
    if len(digits) == 10:
        digits = '0' + digits
    
    return digits

def normalize_tckn(tckn: str) -> str:
    """
    TC Kimlik numarasını normalize et
    
    Args:
        tckn: Orijinal TCKN
    
    Returns:
        Normalize edilmiş TCKN
    """
    return re.sub(r'\D', '', tckn)[:11]


# ========== JSON İŞLEMLERİ ==========

def save_json(data: Any, file_path: str, ensure_ascii: bool = False) -> bool:
    """
    JSON dosyasına veri kaydet
    
    Args:
        data: Kaydedilecek veri
        file_path: Dosya yolu
        ensure_ascii: ASCII garantisi
    
    Returns:
        Başarılı mı
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=2, default=str)
        return True
    except Exception:
        return False

def load_json(file_path: str, default: Any = None) -> Any:
    """
    JSON dosyasından veri yükle
    
    Args:
        file_path: Dosya yolu
        default: Dosya yoksa dönecek varsayılan değer
    
    Returns:
        Yüklenen veri veya default
    """
    if not os.path.exists(file_path):
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


# ========== İSTATİSTİK RAPORLAMA ==========

def create_detailed_stats(user_data: Dict, conversion_stats: Dict, processing_time: float) -> str:
    """
    Detaylı istatistik mesajı oluştur (gelişmiş)
    
    Args:
        user_data: Kullanıcı verisi (used, remaining)
        conversion_stats: Dönüşüm istatistikleri
        processing_time: İşlem süresi (saniye)
    
    Returns:
        Formatlanmış istatistik mesajı
    """
    # Yüzdeleri hesapla
    total_used = user_data.get('used', 0)
    total_remaining = user_data.get('remaining', 0)
    total_package = total_used + total_remaining
    
    success_rate = 0
    if conversion_stats.get('total', 0) > 0:
        success_rate = (conversion_stats.get('success', 0) / conversion_stats.get('total', 1)) * 100
    
    stats = f"""📊 **KULLANIM ÖZETİ**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 **PAKET DURUMU**
• Paket: `{total_package} Dosya Paketi`
• Kullanılan: `{total_used}` dosya (%{(total_used/total_package*100) if total_package > 0 else 0:.0f})
• Kalan Hak: `{total_remaining}` dosya
• Doluluk: {'🟩' * (total_used) + '⬜' * (total_remaining)} 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 **İSTATİSTİKLERİNİZ**
• Toplam Dönüşüm: `{conversion_stats.get('total', 0)}`
  ├─ Başarılı: `{conversion_stats.get('success', 0)}` ✅ (%{success_rate:.1f})
  └─ Başarısız: `{conversion_stats.get('failed', 0)}` ❌
• Bugünkü İşlem: `{conversion_stats.get('today', 0)}`
• Haftalık İşlem: `{conversion_stats.get('weekly', 0)}`
• Aylık İşlem: `{conversion_stats.get('monthly', 0)}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **AKILLI İŞLEMLER**
• Analiz: `{conversion_stats.get('total_analysis', 0)}`
• İsimlendirme: `{conversion_stats.get('total_naming', 0)}`
• Sınıflandırma: `{conversion_stats.get('total_classification', 0)}`
• Özetleme: `{conversion_stats.get('total_summaries', 0)}`
• Doğrulama: `{conversion_stats.get('total_validations', 0)}`
• Kalite: `{conversion_stats.get('total_quality', 0)}`

⏱️ **İŞLEM DETAYI**
• İşlem Süresi: `{processing_time:.2f}` saniye
• İşlem Tarihi: `{get_time_string()}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 **Yeni dosyanızı bekliyorum...** 
"""
    return stats

def create_admin_report(stats: Dict) -> str:
    """
    Admin raporu oluştur
    
    Args:
        stats: Admin istatistikleri
    
    Returns:
        Formatlanmış admin raporu
    """
    report = f"""👑 **ADMIN SİSTEM RAPORU**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **SİSTEM DURUMU**
• Toplam Kullanıcı: `{stats.get('total_users', 0)}`
• Aktif Kullanıcı: `{stats.get('active_users', 0)}`
• Toplam Gelir: `{stats.get('total_revenue', 0):.2f} TL`
• Premium Dönüşüm: `{stats.get('total_premium', 0)}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 **BUGÜNKÜ İŞLEMLER**
• Dönüşüm: `{stats.get('today_conversions', 0)}`
• Analiz: `{stats.get('today_analysis', 0)}`
• İsimlendirme: `{stats.get('today_naming', 0)}`
• Sınıflandırma: `{stats.get('today_classification', 0)}`
• Özetleme: `{stats.get('today_summaries', 0)}`
• Doğrulama: `{stats.get('today_validations', 0)}`
• Kalite: `{stats.get('today_quality', 0)}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ **TOPLAM BAŞARILI**
• Dönüşüm: `{stats.get('success_total', 0)}`
• Analiz: `{stats.get('total_analysis', 0)}`
• İsimlendirme: `{stats.get('total_naming', 0)}`
• Sınıflandırma: `{stats.get('total_classification', 0)}`
• Özetleme: `{stats.get('total_summaries', 0)}`
• Doğrulama: `{stats.get('total_validations', 0)}`
• Kalite: `{stats.get('total_quality', 0)}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **POPÜLER FORMATLAR**
{stats.get('top_formats', '  • Veri yok')}

⭐ **KALİTE SEVİYELERİ**
{stats.get('top_quality', '  • Veri yok')}

📅 **HAFTALIK İSTATİSTİKLER**
{stats.get('weekly_stats', '  • Veri yok')}

💰 **SON GELİRLER**
{stats.get('revenue_stats', '  • Veri yok')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return report

def create_package_summary(package: Dict) -> str:
    """
    Paket özeti oluştur
    
    Args:
        package: Paket bilgileri
    
    Returns:
        Formatlanmış paket özeti
    """
    discount = ((package['original_price'] - package['price']) / package['original_price']) * 100
    
    summary = f"""📦 **{package['emoji']} {package['name']}**

━━━━━━━━━━━━━━━━━━━━━
📊 **PAKET İÇERİĞİ**
• 📁 `{package['rights']}` Dosya Dönüştürme Hakkı
• 💰 ~~{package['original_price']:,} TL~~ → **{package['price']:,} TL**
• 💸 **%{discount:.0f} İndirim!**
• 💎 Dosya başı `{package['price']/package['rights']:.2f}` TL

✨ **ÖZELLİKLER**
"""
    for feature in package.get('features', []):
        summary += f"  {feature}\n"
    
    return summary

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """
    İlerleme çubuğu oluştur
    
    Args:
        current: Mevcut değer
        total: Toplam değer
        length: Çubuk uzunluğu
    
    Returns:
        İlerleme çubuğu (örn: '██████▒▒▒▒▒▒')
    """
    if total == 0:
        return '▒' * length
    
    filled = int((current / total) * length)
    empty = length - filled
    
    return '█' * filled + '▒' * empty

def create_table(data: List[List[str]], headers: List[str] = None) -> str:
    """
    Tablo oluştur
    
    Args:
        data: Tablo verileri
        headers: Sütun başlıkları
    
    Returns:
        Formatlanmış tablo
    """
    if not data:
        return ""
    
    # Sütun genişliklerini hesapla
    col_widths = []
    for col in range(len(data[0])):
        max_width = max(len(str(row[col])) for row in data)
        if headers and col < len(headers):
            max_width = max(max_width, len(headers[col]))
        col_widths.append(max_width)
    
    # Tabloyu oluştur
    lines = []
    
    if headers:
        header_line = ' | '.join(h.ljust(w) for h, w in zip(headers, col_widths))
        lines.append(header_line)
        lines.append('-+-'.join('-' * w for w in col_widths))
    
    for row in data:
        line = ' | '.join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(line)
    
    return '\n'.join(lines)


# ========== SYSTEM İŞLEMLERİ ==========

def get_system_info() -> Dict:
    """
    Sistem bilgilerini getir
    
    Returns:
        Sistem bilgileri sözlüğü
    """
    import platform
    import psutil
    
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'hostname': platform.node(),
        'cpu_count': psutil.cpu_count(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%d.%m.%Y %H:%M:%S')
    }
    
    return info

def format_system_info(info: Dict) -> str:
    """
    Sistem bilgilerini formatla
    
    Args:
        info: Sistem bilgileri sözlüğü
    
    Returns:
        Formatlanmış sistem bilgileri
    """
    text = f"""🖥️ **SİSTEM BİLGİLERİ**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 **İşletim Sistemi:** {info['platform']}
🐍 **Python:** {info['python_version']}
🏠 **Hostname:** {info['hostname']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ **DONANIM**
• CPU: {info['cpu_count']} çekirdek (%{info['cpu_percent']} kullanım)
• RAM: {format_size(info['memory_available'])} / {format_size(info['memory_total'])} (%{info['memory_percent']})
• Disk: %{info['disk_usage']} kullanım
• Açılış: {info['boot_time']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return text


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Utils modülü test ediliyor...")
    print("=" * 60)
    
    # Dosya işlemleri test
    test_filename = "test<file>:name?.txt"
    safe = safe_filename(test_filename)
    print(f"📛 Güvenli dosya adı: {test_filename} -> {safe}")
    
    # Boyut formatlama test
    print(f"📊 Boyut formatlama: 1.5 MB -> {format_size(1.5 * 1024 * 1024)}")
    
    # Tarih işlemleri test
    print(f"📅 Bugün: {get_date_string()}")
    print(f"⏰ Şimdi: {get_time_string()}")
    
    # Metin işlemleri test
    test_text = "  Bu   bir   test   metnidir.  "
    print(f"📝 Temizlenmiş metin: '{clean_text(test_text)}'")
    
    # OCR test
    ocr_test = """
    14:30 15.03.2024
    Screen Shot
    Ekran Alıntısı
    BU BİR TEST BAŞLIĞIDIR
    
    Bu bir test paragrafıdır. İçinde birden fazla cümle bulunur. 
    Bu cümleler otomatik olarak düzenlenecek ve optimize edilecektir.
    
    • Madde 1
    • Madde 2
    • Madde 3
    """
    
    cleaned, removed = clean_ocr_text(ocr_test)
    confidence = calculate_ocr_confidence(cleaned)
    
    print(f"\n🔍 OCR Temizleme Testi:")
    print(f"  • Silinen satır: {len(removed)}")
    print(f"  • Güven skoru: %{confidence:.1f}")
    print(f"  • Temizlenmiş metin:\n{cleaned}")
    
    # Slug test
    test_slug = "Türkçe Karakterli Metin"
    print(f"\n🔗 Slug: {test_slug} -> {slugify(test_slug)}")
    
    # İstatistik test
    test_user = {'used': 15, 'remaining': 15}
    test_stats = {
        'total': 50,
        'success': 45,
        'failed': 5,
        'today': 3,
        'weekly': 12,
        'monthly': 30,
        'total_analysis': 10,
        'total_naming': 8,
        'total_classification': 7,
        'total_summaries': 6,
        'total_validations': 5,
        'total_quality': 4
    }
    
    print(create_detailed_stats(test_user, test_stats, 2.5))
    print("=" * 60)
    print("✅ Utils modülü hazır!")