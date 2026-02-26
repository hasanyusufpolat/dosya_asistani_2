"""
PROFESYONEL BELGE TÜRÜ TANIMA VE FORMAT KISITLAMA MODÜLÜ
Belge türüne göre izin verilen dönüşüm formatlarını belirler
Gelişmiş desen eşleştirme, çoklu dil desteği ve akıllı sınıflandırma
"""

import re
import logging
import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('classifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Belge türleri (genişletilmiş)"""
    # Muhasebe belgeleri
    FATURA = "fatura"
    PROFORMA_FATURA = "proforma_fatura"
    IRSALIYE = "irsaliye"
    BANKA_DEKONTU = "banka_dekontu"
    BANKA_EKSTRESI = "banka_ekstresi"
    MAAS_BORDROSU = "maas_bordrosu"
    KDV_BEYANNAMESI = "kdv_beyannamesi"
    CARI_HESAP = "cari_hesap"
    CARI_EKSTRE = "cari_ekstre"
    ODEME_EMRI = "odeme_emri"
    GIDER_PUSULASI = "gider_pusulasi"
    AVANS_BORDROSU = "avans_bordrosu"
    
    # Hukuki belgeler
    SOZLESME = "sozlesme"
    TEKLIF = "teklif"
    DILEKCE = "dilekce"
    TAAHHUTNAME = "taahhutname"
    VEKALETNAME = "vekaletname"
    MAHKEME_KARARI = "mahkeme_karari"
    RESMI_YAZI = "resmi_yazi"
    TEBLIGAT = "tebligat"
    
    # İK belgeleri
    OZGECMIS = "ozgecmis"
    DILEKCE_IK = "dilekce_ik"
    IZIN_TALEBI = "izin_talebi"
    ISTIFA_DILEKCESI = "istifa_dilekcesi"
    SAVUNMA = "savunma"
    PERFORMANS_DEGERLENDIRME = "performans_degerlendirme"
    
    # Teknik belgeler
    TEKNIK_RAPOR = "teknik_rapor"
    PROJE_DOKUMANI = "proje_dokumani"
    ANALIZ_RAPORU = "analiz_raporu"
    TEST_RAPORU = "test_raporu"
    KULLANIM_KILAVUZU = "kullanim_kilavuzu"
    API_DOKUMANTASYONU = "api_dokumantasyonu"
    
    # Akademik belgeler
    TEZ = "tez"
    MAKALE = "makale"
    BILDIRI = "bildiri"
    ARASTIRMA_RAPORU = "arastirma_raporu"
    LAB_RAPORU = "lab_raporu"
    
    # Finansal belgeler
    YATIRIM_RAPORU = "yatirim_raporu"
    FİYAT_TEKLIFI = "fiyat_teklifi"
    PROFORMA = "proforma"
    STOK_LISTESI = "stok_listesi"
    FIYAT_LISTESI = "fiyat_listesi"
    
    # Sağlık belgeleri
    HASTA_RAPORU = "hasta_raporu"
    RECETE = "recete"
    EPIKRIZ = "epikriz"
    LAB_SONUCU = "lab_sonucu"
    RONTGEN_RAPORU = "rontgen_raporu"
    
    # Genel belgeler
    GENEL_RAPOR = "genel_rapor"
    GENEL_TABLO = "genel_tablo"
    GENEL_BELGE = "genel_belge"
    LISTE = "liste"
    OZET = "ozet"
    NOT = "not"

class DocumentCategory(Enum):
    """Belge kategorileri (genişletilmiş)"""
    RESMI_MUHASEBE = "resmi_muhasebe"
    HUKUKI = "hukuki"
    IK = "ik"
    TEKNIK = "teknik"
    AKADEMIK = "akademik"
    FINANSAL = "finansal"
    SAGLIK = "sağlık"
    GENEL_BELGE = "genel_belge"

class ConfidenceLevel(Enum):
    """Güven seviyeleri"""
    CERTAIN = "kesin"          # 90-100
    HIGH = "yüksek"             # 70-89
    MEDIUM = "orta"              # 50-69
    LOW = "düşük"                # 30-49
    VERY_LOW = "çok_düşük"       # 0-29

@dataclass
class ClassificationMetrics:
    """Sınıflandırma metrikleri"""
    total_matches: int = 0
    unique_matches: int = 0
    keyword_density: float = 0.0
    primary_score: int = 0
    secondary_score: int = 0
    alternative_types: List[DocumentType] = field(default_factory=list)
    alternative_scores: List[int] = field(default_factory=list)
    language: str = "unknown"
    word_count: int = 0

@dataclass
class ClassificationResult:
    """Sınıflandırma sonucu (gelişmiş)"""
    document_type: DocumentType
    category: DocumentCategory
    confidence: int  # 0-100
    confidence_level: ConfidenceLevel
    allowed_formats: List[str]
    extracted_fields: Dict
    metrics: ClassificationMetrics
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class DocumentClassifier:
    """Profesyonel Belge Sınıflandırıcı - Gelişmiş Versiyon"""
    
    def __init__(self):
        # Kategori bazlı belge türleri
        self.category_types = {
            DocumentCategory.RESMI_MUHASEBE: [
                DocumentType.FATURA, DocumentType.PROFORMA_FATURA,
                DocumentType.IRSALIYE, DocumentType.BANKA_DEKONTU,
                DocumentType.BANKA_EKSTRESI, DocumentType.MAAS_BORDROSU,
                DocumentType.KDV_BEYANNAMESI, DocumentType.CARI_HESAP,
                DocumentType.CARI_EKSTRE, DocumentType.ODEME_EMRI,
                DocumentType.GIDER_PUSULASI, DocumentType.AVANS_BORDROSU
            ],
            DocumentCategory.HUKUKI: [
                DocumentType.SOZLESME, DocumentType.TEKLIF,
                DocumentType.DILEKCE, DocumentType.TAAHHUTNAME,
                DocumentType.VEKALETNAME, DocumentType.MAHKEME_KARARI,
                DocumentType.RESMI_YAZI, DocumentType.TEBLIGAT
            ],
            DocumentCategory.IK: [
                DocumentType.OZGECMIS, DocumentType.DILEKCE_IK,
                DocumentType.IZIN_TALEBI, DocumentType.ISTIFA_DILEKCESI,
                DocumentType.SAVUNMA, DocumentType.PERFORMANS_DEGERLENDIRME
            ],
            DocumentCategory.TEKNIK: [
                DocumentType.TEKNIK_RAPOR, DocumentType.PROJE_DOKUMANI,
                DocumentType.ANALIZ_RAPORU, DocumentType.TEST_RAPORU,
                DocumentType.KULLANIM_KILAVUZU, DocumentType.API_DOKUMANTASYONU
            ],
            DocumentCategory.AKADEMIK: [
                DocumentType.TEZ, DocumentType.MAKALE,
                DocumentType.BILDIRI, DocumentType.ARASTIRMA_RAPORU,
                DocumentType.LAB_RAPORU
            ],
            DocumentCategory.FINANSAL: [
                DocumentType.YATIRIM_RAPORU, DocumentType.FİYAT_TEKLIFI,
                DocumentType.PROFORMA, DocumentType.STOK_LISTESI,
                DocumentType.FIYAT_LISTESI
            ],
            DocumentCategory.SAGLIK: [
                DocumentType.HASTA_RAPORU, DocumentType.RECETE,
                DocumentType.EPIKRIZ, DocumentType.LAB_SONUCU,
                DocumentType.RONTGEN_RAPORU
            ],
            DocumentCategory.GENEL_BELGE: [
                DocumentType.GENEL_RAPOR, DocumentType.GENEL_TABLO,
                DocumentType.LISTE, DocumentType.OZET,
                DocumentType.NOT, DocumentType.GENEL_BELGE
            ]
        }
        
        # Format kısıtları (kategori bazlı)
        self.format_restrictions = {
            DocumentCategory.RESMI_MUHASEBE: ['PDF', 'WORD', 'EXCEL'],
            DocumentCategory.HUKUKI: ['PDF', 'WORD'],
            DocumentCategory.IK: ['PDF', 'WORD'],
            DocumentCategory.TEKNIK: ['PDF', 'WORD', 'EXCEL', 'POWERPOINT'],
            DocumentCategory.AKADEMIK: ['PDF', 'WORD'],
            DocumentCategory.FINANSAL: ['PDF', 'WORD', 'EXCEL'],
            DocumentCategory.SAGLIK: ['PDF', 'WORD'],
            DocumentCategory.GENEL_BELGE: ['PDF', 'WORD', 'EXCEL', 'POWERPOINT', 'GORSEL']
        }
        
        # Belge türü desenleri (genişletilmiş - çoklu dil)
        self.patterns = {
            # Fatura ve türevleri
            DocumentType.FATURA: {
                'tr': [r'fatura', r'fatur', r'irsaliye', r'inv', r'mal[ -]?hizmet', r'vergi[ -]?dairesi'],
                'en': [r'invoice', r'inv', r'bill', r'tax[ -]?invoice', r'vat[ -]?invoice'],
                'general': [r'kdv\s*%\s*\d+', r'toplam\s*[\d.,]+\s*(?:tl|try|₺|usd|eur|\$|€)']
            },
            DocumentType.PROFORMA_FATURA: {
                'tr': [r'proforma', r'pro[ -]?forma', r'ön[ -]?fatura'],
                'en': [r'proforma', r'pro[ -]?forma', r'pre[ -]?invoice'],
                'general': []
            },
            DocumentType.IRSALIYE: {
                'tr': [r'irsaliye', r'sevk[ -]?irsaliyesi', r'teslim[ -]?irsaliyesi'],
                'en': [r'waybill', r'delivery[ -]?note', r'shipping[ -]?note'],
                'general': []
            },
            
            # Banka belgeleri
            DocumentType.BANKA_DEKONTU: {
                'tr': [r'dekont', r'banka[ -]?dekontu', r'havale[ -]?dekontu', r'eft[ -]?dekontu'],
                'en': [r'receipt', r'bank[ -]?receipt', r'transaction[ -]?receipt'],
                'general': [r'iban', r'işlem[ -]?no', r'transaction[ -]?id', r'alıcı[ -]?adı', r'gönderen']
            },
            DocumentType.BANKA_EKSTRESI: {
                'tr': [r'ekstre', r'banka[ -]?ekstresi', r'hesap[ -]?ekstresi'],
                'en': [r'statement', r'bank[ -]?statement', r'account[ -]?statement'],
                'general': [r'açılış[ -]?bakiyesi', r'kapanış[ -]?bakiyesi']
            },
            
            # İK belgeleri
            DocumentType.OZGECMIS: {
                'tr': [r'özgeçmiş', r'cv', r'öz[ -]?geçmiş', r'ögeçmiş'],
                'en': [r'resume', r'cv', r'curriculum[ -]?vitae'],
                'general': [r'deneyim', r'education', r'eğitim', r'beceri', r'skill']
            },
            DocumentType.IZIN_TALEBI: {
                'tr': [r'izin[ -]?talebi', r'izin[ -]?dilekçesi', r'yıllık[ -]?izin'],
                'en': [r'leave[ -]?request', r'vacation[ -]?request'],
                'general': []
            },
            DocumentType.ISTIFA_DILEKCESI: {
                'tr': [r'istifa', r'istifa[ -]?dilekçesi', r'ayrılma[ -]?talebi'],
                'en': [r'resignation', r'resignation[ -]?letter'],
                'general': []
            },
            
            # Hukuki belgeler
            DocumentType.SOZLESME: {
                'tr': [r'sözleşme', r'kontrat', r'mukavele'],
                'en': [r'contract', r'agreement'],
                'general': [r'madde\s+\d+', r'fıkra', r'taraflar']
            },
            DocumentType.TEKLIF: {
                'tr': [r'teklif', r'teklif[ -]?mektubu', r'fiyat[ -]?teklifi'],
                'en': [r'proposal', r'offer', r'quotation'],
                'general': [r'fiyat', r'price', r'toplam']
            },
            DocumentType.DILEKCE: {
                'tr': [r'dilekçe', r'başvuru[ -]?dilekçesi', r'arz[ -]?talep'],
                'en': [r'petition', r'application'],
                'general': [r'sayın[ -]?yetkili', r'to[ -]?whom[ -]?it[ -]?may[ -]?concern']
            },
            
            # Teknik belgeler
            DocumentType.TEKNIK_RAPOR: {
                'tr': [r'teknik[ -]?rapor', r'teknik[ -]?doküman'],
                'en': [r'technical[ -]?report', r'technical[ -]?document'],
                'general': [r'spesifikasyon', r'specification', r'parametre']
            },
            DocumentType.KULLANIM_KILAVUZU: {
                'tr': [r'kullanım[ -]?kılavuzu', r'kullanma[ -]?kılavuzu'],
                'en': [r'user[ -]?manual', r'instruction[ -]?manual'],
                'general': [r'adım\s+\d+', r'step\s+\d+']
            },
            DocumentType.API_DOKUMANTASYONU: {
                'tr': [r'api[ -]?dokümantasyonu', r'api[ -]?dökümanı'],
                'en': [r'api[ -]?documentation', r'api[ -]?reference'],
                'general': [r'endpoint', r'parameter', r'response', r'request']
            },
            
            # Akademik belgeler
            DocumentType.TEZ: {
                'tr': [r'tez', r'yüksek[ -]?lisans[ -]?tezi', r'doktora[ -]?tezi'],
                'en': [r'thesis', r'dissertation'],
                'general': [r'abstract', r'özet', r'kaynakça', r'references']
            },
            DocumentType.MAKALE: {
                'tr': [r'makale', r'bilimsel[ -]?makale'],
                'en': [r'article', r'paper', r'journal'],
                'general': [r'doi', r'issn', r'volume', r'issue']
            },
            
            # Finansal belgeler
            DocumentType.FİYAT_TEKLIFI: {
                'tr': [r'fiyat[ -]?teklifi', r'fiyat[ -]?listesi'],
                'en': [r'price[ -]?quotation', r'price[ -]?list'],
                'general': [r'fiyat', r'price', r'adet', r'unit']
            },
            DocumentType.STOK_LISTESI: {
                'tr': [r'stok[ -]?listesi', r'stok[ -]?durumu'],
                'en': [r'stock[ -]?list', r'inventory[ -]?list'],
                'general': [r'ürün', r'product', r'miktar', r'quantity']
            },
            
            # Sağlık belgeleri
            DocumentType.HASTA_RAPORU: {
                'tr': [r'hasta[ -]?raporu', r'hasta[ -]?dosyası'],
                'en': [r'patient[ -]?report', r'medical[ -]?report'],
                'general': [r'tanı', r'diagnosis', r'tedavi', r'treatment']
            },
            DocumentType.RECETE: {
                'tr': [r'reçete', r'ilaç[ -]?listesi'],
                'en': [r'prescription'],
                'general': [r'ilaç', r'medicine', r'doktor', r'doctor']
            },
            
            # Genel belgeler
            DocumentType.GENEL_RAPOR: {
                'tr': [r'rapor', r'analiz[ -]?raporu'],
                'en': [r'report', r'analysis'],
                'general': [r'sonuç', r'result', r'değerlendirme']
            },
            DocumentType.LISTE: {
                'tr': [r'liste', r'listeleme'],
                'en': [r'list'],
                'general': [r'no\s*\.', r'#' , r'sıra']
            },
            DocumentType.OZET: {
                'tr': [r'özet', r'özet[ -]?tablo'],
                'en': [r'summary', r'overview'],
                'general': [r'toplam', r'total']
            }
        }
        
        # Alan desenleri (genişletilmiş)
        self.field_patterns = {
            'tarih': [
                r'tarih\s*:?\s*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})',
                r'date\s*:?\s*(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})',
                r'(\d{1,2})[\.\/](\d{1,2})[\.\/](\d{2,4})',
                r'(\d{4})[-](\d{1,2})[-](\d{1,2})'
            ],
            'firma': [
                r'(?:firma|şirket|company|firm)\s*:?\s*([A-Za-zğüşıöçĞÜŞİÖÇ\s\.]+)',
                r'(?:alıcı|satıcı|customer|supplier)\s*:?\s*([A-Za-zğüşıöçĞÜŞİÖÇ\s\.]+)',
                r'(?:adı|name|ünvan|unvan|title)\s*:?\s*([A-Za-zğüşıöçĞÜŞİÖÇ\s\.]+)'
            ],
            'tutar': [
                r'toplam\s*:?\s*([\d.,]+\s*(?:tl|try|₺|usd|eur|\$|€))',
                r'genel\s*toplam\s*:?\s*([\d.,]+\s*(?:tl|try|₺|usd|eur|\$|€))',
                r'([\d.,]+)\s*(?:tl|try|₺|usd|eur|\$|€)',
                r'(?:tutar|price|amount)\s*:?\s*([\d.,]+)'
            ],
            'kdv': [
                r'kdv\s*:?\s*([\d.,]+\s*%)',
                r'vat\s*:?\s*([\d.,]+\s*%)',
                r'kdv\s*orani\s*:?\s*([\d.,]+)',
                r'vat\s*rate\s*:?\s*([\d.,]+)'
            ],
            'vergi_no': [
                r'vergi\s+no\s*:?\s*(\d+)',
                r'tax\s+id\s*:?\s*(\d+)',
                r'vkn\s*:?\s*(\d+)',
                r'tckn\s*:?\s*(\d{11})'
            ],
            'iban': [
                r'iban\s*:?\s*([A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7})',
                r'iban[:\s]*([A-Z]{2}\d{2}[A-Z0-9]{1,30})'
            ],
            'telefon': [
                r'tel\s*:?\s*([0-9\s\(\)\+\-]{7,})',
                r'phone\s*:?\s*([0-9\s\(\)\+\-]{7,})',
                r'(?:\+?90|0)[0-9]{10}'
            ],
            'email': [
                r'email\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'e[ -]?posta\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'fatura_no': [
                r'fatura\s*no\s*:?\s*([A-Z0-9\-]+)',
                r'invoice\s*no\s*:?\s*([A-Z0-9\-]+)',
                r'inv[.:\s]*([A-Z0-9\-]+)'
            ],
            'siparis_no': [
                r'sipariş\s*no\s*:?\s*([A-Z0-9\-]+)',
                r'order\s*no\s*:?\s*([A-Z0-9\-]+)',
                r'po\s*no\s*:?\s*([A-Z0-9\-]+)'
            ],
            'adres': [
                r'adres\s*:?\s*([^\n]+)',
                r'address\s*:?\s*([^\n]+)',
                r'(?:mahalle|mah\.|sokak|sk\.|cadde|cad\.|bulvar)[\s:]*([^\n]+)'
            ],
            'tc_kimlik': [
                r'tc\s*kimlik\s*no\s*:?\s*(\d{11})',
                r'tckn\s*:?\s*(\d{11})',
                r'kimlik\s*no\s*:?\s*(\d{11})'
            ],
            'musteri_no': [
                r'müşteri\s*no\s*:?\s*([A-Z0-9\-]+)',
                r'customer\s*no\s*:?\s*([A-Z0-9\-]+)'
            ]
        }
        
        # Dil desenleri
        self.language_patterns = {
            'tr': set('ğüşıöçĞÜŞİÖÇ'),
            'de': set('äöüßÄÖÜ'),
            'fr': set('éèêëàâçôùûÿœæ'),
            'es': set('ñáéíóúüÑÁÉÍÓÚÜ'),
            'it': set('àèéìíîòóùú'),
            'ru': set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'),
            'ar': set('ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
        }
    
    def classify(self, text: str, source_format: str) -> ClassificationResult:
        """
        Belgeyi sınıflandır ve izin verilen formatları döndür (gelişmiş)
        """
        try:
            metrics = ClassificationMetrics()
            text_lower = text.lower()
            
            # Kelime sayısı
            words = text.split()
            metrics.word_count = len(words)
            
            # Dil tespiti
            metrics.language = self._detect_language(text)
            
            # 1. Belge türünü tespit et (gelişmiş)
            doc_type, scores, alternatives = self._detect_document_type_advanced(text_lower, metrics.language)
            
            metrics.primary_score = scores.get(doc_type, 0)
            metrics.alternative_types = [alt for alt, _ in alternatives[:3]]
            metrics.alternative_scores = [score for _, score in alternatives[:3]]
            
            # 2. Kategoriyi belirle
            category = self._get_category(doc_type)
            
            # 3. İzin verilen formatları al
            allowed_formats = self._get_allowed_formats(category, source_format)
            
            # 4. Alanları çıkar (gelişmiş)
            extracted_fields = self._extract_fields_advanced(text)
            
            # 5. Güven skoru hesapla (gelişmiş)
            confidence, confidence_level, warnings = self._calculate_confidence_advanced(
                text_lower, doc_type, scores, metrics
            )
            
            # 6. Öneriler oluştur
            suggestions = self._generate_suggestions(doc_type, extracted_fields, metrics)
            
            logger.info(f"✅ Belge sınıflandırıldı: {doc_type.value} (Güven: %{confidence} - {confidence_level.value})")
            logger.info(f"📋 İzin verilen formatlar: {allowed_formats}")
            
            return ClassificationResult(
                document_type=doc_type,
                category=category,
                confidence=confidence,
                confidence_level=confidence_level,
                allowed_formats=allowed_formats,
                extracted_fields=extracted_fields,
                metrics=metrics,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"❌ Sınıflandırma hatası: {e}")
            import traceback
            traceback.print_exc()
            
            return ClassificationResult(
                document_type=DocumentType.GENEL_BELGE,
                category=DocumentCategory.GENEL_BELGE,
                confidence=50,
                confidence_level=ConfidenceLevel.MEDIUM,
                allowed_formats=['PDF', 'WORD', 'EXCEL', 'POWERPOINT'],
                extracted_fields={},
                metrics=ClassificationMetrics(),
                warnings=[str(e)],
                suggestions=["Varsayılan sınıflandırma kullanıldı"]
            )
    
    def _detect_language(self, text: str) -> str:
        """Metnin dilini tespit et"""
        if not text:
            return 'unknown'
        
        scores = {}
        for lang, chars in self.language_patterns.items():
            count = sum(1 for c in text if c in chars)
            if count > 0:
                scores[lang] = count
        
        if scores:
            return max(scores, key=scores.get)
        return 'en'
    
    def _detect_document_type_advanced(self, text: str, language: str) -> Tuple[DocumentType, Dict, List]:
        """
        Gelişmiş belge türü tespiti
        Returns: (ana_tip, skorlar, alternatifler)
        """
        scores = {}
        
        for doc_type, lang_patterns in self.patterns.items():
            score = 0
            
            # Dile özel patternler
            if language in lang_patterns:
                for pattern in lang_patterns[language]:
                    if pattern in text:
                        score += 5
                    if re.search(pattern, text):
                        score += 3
            
            # Genel patternler
            if 'general' in lang_patterns:
                for pattern in lang_patterns['general']:
                    if pattern in text:
                        score += 4
                    if re.search(pattern, text):
                        score += 2
            
            if score > 0:
                scores[doc_type] = score
        
        if not scores:
            return DocumentType.GENEL_BELGE, {DocumentType.GENEL_BELGE: 1}, []
        
        # Alternatifleri sırala
        alternatives = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Ana tipi seç
        main_type = alternatives[0][0]
        
        return main_type, scores, alternatives
    
    def _get_category(self, doc_type: DocumentType) -> DocumentCategory:
        """Belge kategorisini belirle"""
        for category, types in self.category_types.items():
            if doc_type in types:
                return category
        return DocumentCategory.GENEL_BELGE
    
    def _get_allowed_formats(self, category: DocumentCategory, source_format: str) -> List[str]:
        """İzin verilen formatları döndür"""
        base_formats = self.format_restrictions.get(category, ['PDF', 'WORD', 'EXCEL'])
        
        # Kaynak formatı da ekle
        if source_format not in base_formats:
            base_formats.append(source_format)
        
        # Benzersiz yap
        return list(dict.fromkeys(base_formats))
    
    def _extract_fields_advanced(self, text: str) -> Dict:
        """Gelişmiş alan çıkarımı"""
        extracted = {}
        
        for field, patterns in self.field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Grup varsa onu al, yoksa tüm eşleşmeyi al
                    if match.groups():
                        value = match.group(1).strip()
                    else:
                        value = match.group(0).strip()
                    
                    # Değeri temizle
                    value = re.sub(r'\s+', ' ', value)
                    
                    extracted[field] = value
                    break
        
        return extracted
    
    def _calculate_confidence_advanced(self, text: str, doc_type: DocumentType, 
                                      scores: Dict, metrics: ClassificationMetrics) -> Tuple[int, ConfidenceLevel, List[str]]:
        """
        Gelişmiş güven skoru hesaplama
        Returns: (confidence, level, warnings)
        """
        warnings = []
        
        # Ana tip skoru
        main_score = scores.get(doc_type, 0)
        
        # Toplam skor
        total_score = sum(scores.values())
        
        # Alternatif skorlar
        if len(scores) > 1:
            second_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
            score_ratio = second_score / main_score if main_score > 0 else 0
            
            if score_ratio > 0.8:
                warnings.append("Birden fazla belge türüne benzerlik var")
                metrics.keyword_density = score_ratio
        
        # Kelime sayısı bazlı düzeltme
        word_factor = 1.0
        if metrics.word_count < 50:
            word_factor = 0.7
            warnings.append("Çok kısa metin, güven düşük")
        elif metrics.word_count > 1000:
            word_factor = 1.2
            warnings.append("Uzun metin, analiz daha güvenli")
        
        # Ana skoru hesapla
        if total_score > 0:
            base_confidence = (main_score * 100) // total_score
        else:
            base_confidence = 50
        
        # Kelime faktörünü uygula
        confidence = int(min(100, base_confidence * word_factor))
        
        # Güven seviyesi
        if confidence >= 90:
            level = ConfidenceLevel.CERTAIN
        elif confidence >= 70:
            level = ConfidenceLevel.HIGH
        elif confidence >= 50:
            level = ConfidenceLevel.MEDIUM
        elif confidence >= 30:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW
        
        return confidence, level, warnings
    
    def _generate_suggestions(self, doc_type: DocumentType, extracted_fields: Dict, 
                              metrics: ClassificationMetrics) -> List[str]:
        """Öneriler oluştur"""
        suggestions = []
        
        # Eksik alan kontrolü
        expected_fields = {
            DocumentType.FATURA: ['fatura_no', 'tarih', 'firma', 'tutar', 'vergi_no'],
            DocumentType.BANKA_DEKONTU: ['iban', 'tarih', 'tutar'],
            DocumentType.SOZLESME: ['tarih', 'firma'],
            DocumentType.OZGECMIS: ['email', 'telefon']
        }
        
        if doc_type in expected_fields:
            for field in expected_fields[doc_type]:
                if field not in extracted_fields:
                    suggestions.append(f"{field} alanı eklenebilir")
        
        # Dil önerisi
        if metrics.language != 'tr' and metrics.language != 'en':
            suggestions.append(f"Belge dili tespit edilemedi: {metrics.language}")
        
        return suggestions[:3]  # En fazla 3 öneri
    
    def validate_conversion(self, source_type: str, target_type: str, doc_type: DocumentType) -> Tuple[bool, str]:
        """
        Dönüşümün geçerli olup olmadığını kontrol et
        Returns: (geçerli_mi, mesaj)
        """
        category = self._get_category(doc_type)
        allowed = self._get_allowed_formats(category, source_type)
        
        if target_type in allowed:
            return True, "✅ Geçerli dönüşüm"
        else:
            allowed_str = ', '.join(allowed)
            return False, f"❌ Bu belge türü için izin verilmeyen dönüşüm. (İzin verilen: {allowed_str})"


# ========== KULLANIM KOLAYLIĞI FONKSİYONLARI ==========

def classify_document(text: str, source_format: str) -> Dict:
    """
    Belgeyi sınıflandır
    Returns: sınıflandırma bilgileri
    """
    classifier = DocumentClassifier()
    result = classifier.classify(text, source_format)
    
    return {
        'document_type': result.document_type.value,
        'category': result.category.value,
        'confidence': result.confidence,
        'confidence_level': result.confidence_level.value,
        'allowed_formats': result.allowed_formats,
        'extracted_fields': result.extracted_fields,
        'warnings': result.warnings,
        'suggestions': result.suggestions,
        'metrics': {
            'word_count': result.metrics.word_count,
            'language': result.metrics.language,
            'alternatives': [
                {'type': t.value, 'score': s} 
                for t, s in zip(result.metrics.alternative_types, result.metrics.alternative_scores)
            ]
        }
    }

def check_conversion_allowed(source_type: str, target_type: str, doc_type: str) -> Tuple[bool, str]:
    """
    Dönüşümün izin verilip verilmediğini kontrol et
    """
    classifier = DocumentClassifier()
    
    # String'den Enum'a çevir
    type_map = {t.value: t for t in DocumentType}
    doc_type_enum = type_map.get(doc_type, DocumentType.GENEL_BELGE)
    
    return classifier.validate_conversion(source_type, target_type, doc_type_enum)

def get_document_type_list() -> List[Dict]:
    """
    Tüm belge türlerini listele
    """
    result = []
    for doc_type in DocumentType:
        result.append({
            'type': doc_type.value,
            'name': doc_type.name.replace('_', ' ').title()
        })
    return result


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Belge Sınıflandırma Modülü Test Ediliyor...")
    print("=" * 60)
    
    # Test metni
    test_text = """
    FATURA
    Fatura No: INV2024001
    Tarih: 15.03.2024
    Firma: ABC Ltd. Şti.
    Vergi No: 1234567890
    Tutar: 1.250,50 TL
    KDV: %20
    Toplam: 1.500,60 TL
    IBAN: TR12 0001 0004 6796 3186 2350 01
    """
    
    classifier = DocumentClassifier()
    result = classifier.classify(test_text, 'PDF')
    
    print(f"\n📄 Belge Türü: {result.document_type.value}")
    print(f"📂 Kategori: {result.category.value}")
    print(f"📈 Güven Skoru: %{result.confidence} ({result.confidence_level.value})")
    print(f"📋 İzin Verilen Formatlar: {result.allowed_formats}")
    
    print(f"\n📊 Çıkarılan Alanlar:")
    for key, value in result.extracted_fields.items():
        print(f"  • {key}: {value}")
    
    if result.warnings:
        print(f"\n⚠️ Uyarılar:")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    if result.suggestions:
        print(f"\n💡 Öneriler:")
        for suggestion in result.suggestions:
            print(f"  • {suggestion}")
    
    if result.metrics.alternative_types:
        print(f"\n🔄 Alternatif Türler:")
        for alt_type, alt_score in zip(result.metrics.alternative_types, result.metrics.alternative_scores):
            print(f"  • {alt_type.value}: %{alt_score}")
    
    # Dönüşüm kontrolü testi
    valid, msg = classifier.validate_conversion('PDF', 'EXCEL', result.document_type)
    print(f"\n🔄 PDF -> EXCEL dönüşümü: {msg}")
    
    valid, msg = classifier.validate_conversion('PDF', 'WORD', result.document_type)
    print(f"🔄 PDF -> WORD dönüşümü: {msg}")
    
    print("=" * 60)
    print("✅ Belge Sınıflandırma Modülü hazır!")