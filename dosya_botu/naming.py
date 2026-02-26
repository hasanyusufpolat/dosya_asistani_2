"""
AKILLI DOSYA İSİMLENDİRME MODÜLÜ
İçeriğe göre anlamlı dosya adı oluşturur
Belge türü, tarih, firma, tutar gibi bilgileri çıkarır
"""

import os
import re
import datetime
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('naming.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NamingResult:
    """İsimlendirme sonucu"""
    new_name: str
    extracted_info: Dict
    confidence: int  # 0-100 arası güven skoru
    file_type: str

class SmartNamer:
    """Akıllı Dosya İsimlendirici"""
    
    def __init__(self):
        # Türkçe karakter dönüşümleri
        self.char_map = {
            'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
            'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'
        }
        
        # Belge türü desenleri
        self.document_patterns = {
            'fatura': [
                r'fatura', r'invoice', r'fatur', r'inv',
                r'irsaliye', r'waybill', r'fat'
            ],
            'banka_dekontu': [
                r'dekont', r'receipt', r'banka', r'bank',
                r'havale', r'eft', r'ödeme', r'payment'
            ],
            'maas_bordrosu': [
                r'maaş', r'bordro', r'salary', r'payroll',
                r'mas', r'bord', r'ücret', r'wage'
            ],
            'kdv_beyannamesi': [
                r'kdv', r'vat', r'tax', r'beyanname',
                r'vergi', r'declaration'
            ],
            'cari_hesap': [
                r'cari', r'hesap', r'account', r'ekstre',
                r'statement', r'bakiye', r'balance'
            ],
            'genel_tablo': [
                r'tablo', r'rapor', r'list', r'liste',
                r'summary', r'özet', r'döküm'
            ]
        }
        
        # Tarih desenleri
        self.date_patterns = [
            # DD.MM.YYYY veya DD/MM/YYYY
            r'(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{4})',
            # YYYY-MM-DD
            r'(\d{4})[-](\d{1,2})[-](\d{1,2})',
            # DD Month YYYY (Türkçe/İngilizce)
            r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
        ]
        
        # Tutar desenleri
        self.amount_patterns = [
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:tl|try|₺|usd|eur|\$|€)',
            r'(?:tl|try|₺|usd|eur|\$|€)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'toplam\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'genel\s*toplam\s*:?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
        ]
        
        # Firma/Kişi desenleri
        self.company_patterns = [
            r'(?:firma|şirket|company|firm)\s*:?\s*([A-Za-zğüşıöç\s]+)',
            r'(?:adı|name)\s*:?\s*([A-Za-zğüşıöç\s]+)',
            r'(?:alıcı|satıcı|customer|supplier)\s*:?\s*([A-Za-zğüşıöç\s]+)',
        ]
    
    def normalize_text(self, text: str) -> str:
        """Metni normalize et (Türkçe karakterleri dönüştür)"""
        for tr_char, en_char in self.char_map.items():
            text = text.replace(tr_char, en_char)
        return text
    
    def extract_date(self, text: str) -> Optional[str]:
        """Metinden tarih bilgisi çıkar"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                            year, month, day = match.groups()
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        elif '.' in pattern or '/' in pattern:  # DD.MM.YYYY
                            day, month, year = match.groups()
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:  # DD Month YYYY
                            day, month_text, year = match.groups()
                            month_map = {
                                'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04',
                                'mayıs': '05', 'haziran': '06', 'temmuz': '07', 'ağustos': '08',
                                'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12',
                                'january': '01', 'february': '02', 'march': '03', 'april': '04',
                                'may': '05', 'june': '06', 'july': '07', 'august': '08',
                                'september': '09', 'october': '10', 'november': '11', 'december': '12'
                            }
                            month = month_map.get(month_text.lower(), '01')
                            return f"{year}-{month}-{day.zfill(2)}"
                except:
                    continue
        return None
    
    def extract_amount(self, text: str) -> Optional[Tuple[float, str]]:
        """Metinden tutar ve para birimi çıkar"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Tutarı sayıya çevir
                amount_str = amount_str.replace('.', '').replace(',', '.')
                try:
                    amount = float(amount_str)
                    
                    # Para birimini belirle
                    currency = 'TL'
                    if 'usd' in text.lower() or '$' in text:
                        currency = 'USD'
                    elif 'eur' in text.lower() or '€' in text:
                        currency = 'EUR'
                    
                    return (amount, currency)
                except:
                    continue
        return None
    
    def extract_company(self, text: str) -> Optional[str]:
        """Metinden firma/kişi adı çıkar"""
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Temizle
                company = re.sub(r'\s+', '_', company)
                company = self.normalize_text(company)
                return company[:30]  # Çok uzunsa kes
        return None
    
    def detect_document_type(self, text: str) -> Tuple[str, int]:
        """Belge türünü tespit et"""
        text_lower = text.lower()
        max_score = 0
        detected_type = 'genel_belge'
        
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 10
                if re.search(pattern, text_lower):
                    score += 5
            
            if score > max_score:
                max_score = score
                detected_type = doc_type
        
        # Güven skoru hesapla (0-100)
        confidence = min(100, max_score * 5)
        return detected_type, confidence
    
    def generate_filename(self, text: str, original_ext: str) -> NamingResult:
        """
        Metin içeriğine göre anlamlı dosya adı oluştur
        """
        try:
            extracted = {}
            
            # 1. Belge türünü tespit et
            doc_type, type_confidence = self.detect_document_type(text)
            extracted['document_type'] = doc_type
            
            # 2. Tarih bilgisini çıkar
            date = self.extract_date(text)
            if date:
                extracted['date'] = date
            else:
                # Bugünün tarihini kullan
                extracted['date'] = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # 3. Tutar bilgisini çıkar
            amount_info = self.extract_amount(text)
            if amount_info:
                amount, currency = amount_info
                extracted['amount'] = amount
                extracted['currency'] = currency
            
            # 4. Firma bilgisini çıkar
            company = self.extract_company(text)
            if company:
                extracted['company'] = company
            
            # 5. Dosya adını oluştur
            name_parts = []
            
            # Önce tarih
            if extracted.get('date'):
                name_parts.append(extracted['date'])
            
            # Sonra belge türü (Türkçe)
            doc_type_names = {
                'fatura': 'Fatura',
                'banka_dekontu': 'Dekont',
                'maas_bordrosu': 'Bordro',
                'kdv_beyannamesi': 'KDV_Beyannamesi',
                'cari_hesap': 'Cari_Hesap',
                'genel_tablo': 'Rapor',
                'genel_belge': 'Belge'
            }
            name_parts.append(doc_type_names.get(doc_type, 'Belge'))
            
            # Varsa firma adı
            if extracted.get('company'):
                name_parts.append(extracted['company'])
            
            # Varsa tutar
            if extracted.get('amount'):
                amount_str = f"{extracted['amount']:.2f}".replace('.', ',')
                name_parts.append(f"{amount_str}_{extracted.get('currency', 'TL')}")
            
            # Son olarak benzersiz ID (çakışmayı önlemek için)
            import hashlib
            unique_id = hashlib.md5(text[:100].encode()).hexdigest()[:4]
            name_parts.append(unique_id)
            
            # Dosya adını birleştir
            base_name = '_'.join(name_parts)
            
            # Geçersiz karakterleri temizle
            base_name = re.sub(r'[<>:"/\\|?*]', '', base_name)
            base_name = re.sub(r'\s+', '_', base_name)
            
            # Uzantıyı ekle
            new_name = f"{base_name}{original_ext}"
            
            # Güven skoru hesapla
            confidence = type_confidence
            if extracted.get('date'):
                confidence += 10
            if extracted.get('company'):
                confidence += 15
            if extracted.get('amount'):
                confidence += 15
            
            confidence = min(100, confidence)
            
            logger.info(f"✅ Dosya adı oluşturuldu: {new_name} (Güven: %{confidence})")
            
            return NamingResult(
                new_name=new_name,
                extracted_info=extracted,
                confidence=confidence,
                file_type=original_ext
            )
            
        except Exception as e:
            logger.error(f"❌ İsimlendirme hatası: {e}")
            # Hata durumunda varsayılan isim
            default_name = f"belge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{original_ext}"
            return NamingResult(
                new_name=default_name,
                extracted_info={},
                confidence=0,
                file_type=original_ext
            )
    
    def rename_file(self, file_path: str, text_content: str) -> Tuple[bool, str, NamingResult]:
        """
        Dosyayı yeniden adlandır
        Returns: (başarılı_mı, yeni_dosya_yolu, isimlendirme_sonucu)
        """
        try:
            directory = os.path.dirname(file_path)
            original_name = os.path.basename(file_path)
            original_ext = os.path.splitext(original_name)[1]
            
            # Yeni isim oluştur
            result = self.generate_filename(text_content, original_ext)
            
            # Yeni dosya yolu
            new_path = os.path.join(directory, result.new_name)
            
            # Aynı isimde dosya varsa
            if os.path.exists(new_path):
                base, ext = os.path.splitext(result.new_name)
                counter = 1
                while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
                    counter += 1
                result.new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(directory, result.new_name)
            
            # Dosyayı yeniden adlandır
            os.rename(file_path, new_path)
            
            logger.info(f"✅ Dosya yeniden adlandırıldı: {original_name} -> {result.new_name}")
            return True, new_path, result
            
        except Exception as e:
            logger.error(f"❌ Dosya yeniden adlandırma hatası: {e}")
            return False, file_path, None


# ========== KULLANIM KOLAYLIĞI FONKSİYONU ==========
def smart_rename(file_path: str, text_content: str) -> Tuple[bool, str, Dict]:
    """
    Akıllı dosya isimlendirme yap
    Returns: (başarılı_mı, yeni_dosya_yolu, çıkarılan_bilgiler)
    """
    namer = SmartNamer()
    success, new_path, result = namer.rename_file(file_path, text_content)
    
    if success and result:
        return True, new_path, {
            'new_name': result.new_name,
            'extracted_info': result.extracted_info,
            'confidence': result.confidence
        }
    else:
        return False, file_path, {}


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Akıllı İsimlendirme Modülü Test Ediliyor...")
    
    test_text = """
    FATURA
    Tarih: 15.03.2024
    Firma: ABC Ltd. Şti.
    Tutar: 1.250,50 TL
    KDV: %20
    """
    
    namer = SmartNamer()
    result = namer.generate_filename(test_text, '.pdf')
    
    print(f"\n📄 Oluşturulan İsim: {result.new_name}")
    print(f"📊 Çıkarılan Bilgiler: {result.extracted_info}")
    print(f"📈 Güven Skoru: %{result.confidence}")