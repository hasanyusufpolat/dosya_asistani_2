"""
HATA VE EKSİK UYARI SİSTEMİ MODÜLÜ
Belgede eksik veya hatalı alanları tespit eder
Muhasebe standartlarına göre kontrol yapar
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Uyarı seviyeleri"""
    INFO = "bilgi"
    WARNING = "uyarı"
    ERROR = "hata"
    CRITICAL = "kritik"

@dataclass
class ValidationIssue:
    """Tespit edilen sorun"""
    field: str
    message: str
    severity: ValidationSeverity
    suggestion: str

@dataclass
class ValidationResult:
    """Doğrulama sonucu"""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings_count: int
    errors_count: int
    critical_count: int
    score: int  # 0-100 arası kalite puanı

class DocumentValidator:
    """Belge Doğrulayıcı"""
    
    def __init__(self):
        # Zorunlu alanlar (belge türüne göre)
        self.required_fields = {
            'fatura': [
                {'field': 'fatura_no', 'name': 'Fatura Numarası', 'critical': True},
                {'field': 'tarih', 'name': 'Fatura Tarihi', 'critical': True},
                {'field': 'firma', 'name': 'Firma Adı', 'critical': True},
                {'field': 'vergi_no', 'name': 'Vergi Numarası', 'critical': True},
                {'field': 'tutar', 'name': 'Toplam Tutar', 'critical': True},
                {'field': 'kdv', 'name': 'KDV Oranı', 'critical': False},
                {'field': 'urunler', 'name': 'Ürün/Hizmet Listesi', 'critical': False},
                {'field': 'iban', 'name': 'IBAN', 'critical': False}
            ],
            'banka_dekontu': [
                {'field': 'islem_no', 'name': 'İşlem Numarası', 'critical': True},
                {'field': 'tarih', 'name': 'İşlem Tarihi', 'critical': True},
                {'field': 'tutar', 'name': 'İşlem Tutarı', 'critical': True},
                {'field': 'alici', 'name': 'Alıcı Adı', 'critical': True},
                {'field': 'gonderen', 'name': 'Gönderen', 'critical': False},
                {'field': 'iban', 'name': 'IBAN', 'critical': True}
            ],
            'maas_bordrosu': [
                {'field': 'personel', 'name': 'Personel Adı', 'critical': True},
                {'field': 'tc_kimlik', 'name': 'TC Kimlik No', 'critical': True},
                {'field': 'donem', 'name': 'Dönem', 'critical': True},
                {'field': 'net_ucret', 'name': 'Net Ücret', 'critical': True},
                {'field': 'brut_ucret', 'name': 'Brüt Ücret', 'critical': True},
                {'field': 'sgk', 'name': 'SGK Primleri', 'critical': True},
                {'field': 'gelir_vergisi', 'name': 'Gelir Vergisi', 'critical': True},
                {'field': 'imza', 'name': 'İmza/Kaşe', 'critical': True}
            ],
            'kdv_beyannamesi': [
                {'field': 'donem', 'name': 'Dönem', 'critical': True},
                {'field': 'vergi_no', 'name': 'Vergi Numarası', 'critical': True},
                {'field': 'matrah', 'name': 'Matrah', 'critical': True},
                {'field': 'kdv_tutari', 'name': 'KDV Tutarı', 'critical': True},
                {'field': 'teslim_eden', 'name': 'Teslim Eden', 'critical': False},
                {'field': 'onay_tarihi', 'name': 'Onay Tarihi', 'critical': False}
            ],
            'cari_hesap': [
                {'field': 'firma', 'name': 'Firma Adı', 'critical': True},
                {'field': 'donem', 'name': 'Dönem', 'critical': True},
                {'field': 'acilis_bakiyesi', 'name': 'Açılış Bakiyesi', 'critical': True},
                {'field': 'borc', 'name': 'Borç Tutarı', 'critical': True},
                {'field': 'alacak', 'name': 'Alacak Tutarı', 'critical': True},
                {'field': 'kapanis_bakiyesi', 'name': 'Kapanış Bakiyesi', 'critical': True}
            ],
            'genel_tablo': [
                {'field': 'baslik', 'name': 'Tablo Başlığı', 'critical': False},
                {'field': 'tarih', 'name': 'Tarih', 'critical': False},
                {'field': 'veri_sayisi', 'name': 'Veri Sayısı', 'critical': False}
            ]
        }
        
        # Validasyon desenleri
        self.validation_patterns = {
            'fatura_no': r'[A-Z0-9]{5,20}',
            'vergi_no': r'\d{10,11}',
            'tc_kimlik': r'^[1-9]\d{10}$',
            'iban': r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'telefon': r'^(\+90|0)?[0-9]{10}$',
            'tarih': r'^\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4}$',
            'tutar': r'^\d{1,3}(?:\.\d{3})*(?:,\d{2})?$'
        }
        
        # Tutar uyumluluk kontrolleri
        self.amount_checks = [
            {
                'name': 'toplam_kdv',
                'formula': lambda data: data.get('kdv_tutari', 0) == data.get('matrah', 0) * data.get('kdv_orani', 0) / 100,
                'message': 'KDV tutarı matrah ile uyumsuz'
            },
            {
                'name': 'net_brut',
                'formula': lambda data: data.get('net_ucret', 0) < data.get('brut_ucret', 0),
                'message': 'Net ücret brüt ücretten büyük olamaz'
            },
            {
                'name': 'cari_bakiye',
                'formula': lambda data: abs(data.get('kapanis_bakiyesi', 0) - 
                                          (data.get('acilis_bakiyesi', 0) + 
                                           data.get('borc', 0) - 
                                           data.get('alacak', 0))) < 0.01,
                'message': 'Cari hesap bakiyesi uyumsuz'
            }
        ]
    
    def validate(self, text: str, extracted_info: Dict, document_type: str) -> ValidationResult:
        """
        Belgeyi doğrula ve sorunları tespit et
        """
        issues = []
        warnings_count = 0
        errors_count = 0
        critical_count = 0
        
        try:
            # 1. Zorunlu alanları kontrol et
            required = self.required_fields.get(document_type, [])
            for field_info in required:
                field = field_info['field']
                field_name = field_info['name']
                is_critical = field_info['critical']
                
                if field not in extracted_info or not extracted_info[field]:
                    message = f"{field_name} bilgisi bulunamadı."
                    
                    if is_critical:
                        severity = ValidationSeverity.CRITICAL
                        critical_count += 1
                        suggestion = f"{field_name} eklenmeli, aksi halde belge geçersiz sayılabilir."
                    else:
                        severity = ValidationSeverity.WARNING
                        warnings_count += 1
                        suggestion = f"{field_name} eklenmesi önerilir."
                    
                    issues.append(ValidationIssue(
                        field=field,
                        message=message,
                        severity=severity,
                        suggestion=suggestion
                    ))
            
            # 2. Format kontrolleri
            format_issues = self._check_formats(extracted_info)
            for issue in format_issues:
                issues.append(issue)
                if issue.severity == ValidationSeverity.ERROR:
                    errors_count += 1
                elif issue.severity == ValidationSeverity.WARNING:
                    warnings_count += 1
            
            # 3. Tutar uyumluluk kontrolleri
            amount_issues = self._check_amounts(extracted_info)
            for issue in amount_issues:
                issues.append(issue)
                if issue.severity == ValidationSeverity.ERROR:
                    errors_count += 1
                elif issue.severity == ValidationSeverity.WARNING:
                    warnings_count += 1
            
            # 4. İmza/kaşe kontrolü (belge türüne göre)
            if document_type in ['fatura', 'maas_bordrosu']:
                if 'imza' not in text.lower() and 'kaşe' not in text.lower() and 'mühür' not in text.lower():
                    issues.append(ValidationIssue(
                        field='imza',
                        message='Belgede imza veya kaşe bulunamadı.',
                        severity=ValidationSeverity.WARNING,
                        suggestion='Resmî belgelerde imza/kaşe bulunması önerilir.'
                    ))
                    warnings_count += 1
            
            # 5. Genel geçerlilik
            is_valid = (critical_count == 0 and errors_count == 0)
            
            # 6. Kalite puanı hesapla
            score = self._calculate_score(issues, len(required))
            
            logger.info(f"✅ Belge doğrulama tamamlandı - Geçerli: {is_valid}, Puan: {score}")
            
            return ValidationResult(
                is_valid=is_valid,
                issues=issues,
                warnings_count=warnings_count,
                errors_count=errors_count,
                critical_count=critical_count,
                score=score
            )
            
        except Exception as e:
            logger.error(f"❌ Doğrulama hatası: {e}")
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    field='genel',
                    message=f'Doğrulama sırasında hata: {str(e)}',
                    severity=ValidationSeverity.ERROR,
                    suggestion='Belge tekrar kontrol edilmeli.'
                )],
                warnings_count=0,
                errors_count=1,
                critical_count=0,
                score=0
            )
    
    def _check_formats(self, extracted_info: Dict) -> List[ValidationIssue]:
        """Format kontrollerini yap"""
        issues = []
        
        for field, value in extracted_info.items():
            if field in self.validation_patterns:
                pattern = self.validation_patterns[field]
                if not re.match(pattern, str(value), re.IGNORECASE):
                    field_names = {
                        'fatura_no': 'Fatura numarası',
                        'vergi_no': 'Vergi numarası',
                        'tc_kimlik': 'TC Kimlik numarası',
                        'iban': 'IBAN',
                        'email': 'E-posta adresi',
                        'telefon': 'Telefon numarası',
                        'tarih': 'Tarih',
                        'tutar': 'Tutar'
                    }
                    field_name = field_names.get(field, field)
                    
                    issues.append(ValidationIssue(
                        field=field,
                        message=f'{field_name} formatı hatalı.',
                        severity=ValidationSeverity.ERROR,
                        suggestion=f'{field_name} geçerli formatta girilmeli.'
                    ))
        
        return issues
    
    def _check_amounts(self, extracted_info: Dict) -> List[ValidationIssue]:
        """Tutar uyumluluk kontrollerini yap"""
        issues = []
        
        for check in self.amount_checks:
            try:
                if not check['formula'](extracted_info):
                    issues.append(ValidationIssue(
                        field='tutar',
                        message=check['message'],
                        severity=ValidationSeverity.ERROR,
                        suggestion='Tutarları kontrol edin, matematiksel hata olabilir.'
                    ))
            except:
                pass
        
        return issues
    
    def _calculate_score(self, issues: List[ValidationIssue], total_fields: int) -> int:
        """Kalite puanı hesapla"""
        if total_fields == 0:
            return 50
        
        # Başlangıç puanı
        score = 100
        
        # Sorunlara göre puan düş
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                score -= 30
            elif issue.severity == ValidationSeverity.ERROR:
                score -= 20
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 10
            elif issue.severity == ValidationSeverity.INFO:
                score -= 5
        
        return max(0, min(100, score))
    
    def get_validation_report(self, result: ValidationResult) -> str:
        """Doğrulama raporu oluştur"""
        report = []
        
        report.append("📋 **BELGE DOĞRULAMA RAPORU**")
        report.append("━━━━━━━━━━━━━━━━━━━━━")
        
        if result.is_valid:
            report.append("✅ **Belge geçerli** - Tüm kritik alanlar mevcut ve doğru formatta.")
        else:
            report.append("❌ **Belge geçersiz** - Kritik hatalar var, düzeltilmeden kullanılmamalı.")
        
        report.append("")
        
        if result.issues:
            report.append("**🔍 TESPİT EDİLEN SORUNLAR:**")
            
            # Seviyelerine göre grupla
            critical = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
            errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
            warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
            infos = [i for i in result.issues if i.severity == ValidationSeverity.INFO]
            
            if critical:
                report.append("\n🔥 **KRİTİK HATALAR (Çözülmeli):**")
                for issue in critical:
                    report.append(f"  • ❌ {issue.message}")
                    report.append(f"    💡 {issue.suggestion}")
            
            if errors:
                report.append("\n⚠️ **HATALAR (Düzeltilmeli):**")
                for issue in errors:
                    report.append(f"  • ⚠️ {issue.message}")
                    report.append(f"    💡 {issue.suggestion}")
            
            if warnings:
                report.append("\n📌 **UYARILAR (Önerilen):**")
                for issue in warnings:
                    report.append(f"  • 📌 {issue.message}")
                    report.append(f"    💡 {issue.suggestion}")
            
            if infos:
                report.append("\nℹ️ **BİLGİLENDİRMELER:**")
                for issue in infos:
                    report.append(f"  • ℹ️ {issue.message}")
        else:
            report.append("✅ Sorun tespit edilmedi!")
        
        report.append("")
        report.append("━━━━━━━━━━━━━━━━━━━━━")
        report.append(f"📊 **KALİTE PUANI:** {result.score}/100")
        
        if result.score >= 90:
            report.append("🏆 Mükemmel belge")
        elif result.score >= 70:
            report.append("👍 İyi belge, küçük iyileştirmeler yapılabilir")
        elif result.score >= 50:
            report.append("🔧 Orta kalite, düzeltmeler gerekli")
        else:
            report.append("❌ Düşük kalite, büyük düzeltmeler gerekli")
        
        return "\n".join(report)


# ========== KULLANIM KOLAYLIĞI FONKSİYONLARI ==========
def validate_document(text: str, extracted_info: Dict, document_type: str) -> Dict:
    """
    Belgeyi doğrula
    Returns: doğrulama sonuçları
    """
    validator = DocumentValidator()
    result = validator.validate(text, extracted_info, document_type)
    
    return {
        'is_valid': result.is_valid,
        'issues': [
            {
                'field': i.field,
                'message': i.message,
                'severity': i.severity.value,
                'suggestion': i.suggestion
            } for i in result.issues
        ],
        'warnings_count': result.warnings_count,
        'errors_count': result.errors_count,
        'critical_count': result.critical_count,
        'score': result.score
    }

def get_validation_report(result: Dict) -> str:
    """
    Doğrulama raporu oluştur
    """
    validator = DocumentValidator()
    
    # Dict'ten ValidationResult oluştur
    issues = [
        ValidationIssue(
            field=i['field'],
            message=i['message'],
            severity=ValidationSeverity(i['severity']),
            suggestion=i['suggestion']
        ) for i in result.get('issues', [])
    ]
    
    validation_result = ValidationResult(
        is_valid=result.get('is_valid', False),
        issues=issues,
        warnings_count=result.get('warnings_count', 0),
        errors_count=result.get('errors_count', 0),
        critical_count=result.get('critical_count', 0),
        score=result.get('score', 0)
    )
    
    return validator.get_validation_report(validation_result)


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Belge Doğrulama Modülü Test Ediliyor...")
    
    # Test verileri
    test_text = """
    FATURA
    Fatura No: INV2024001
    Tarih: 15.03.2024
    Firma: ABC Ltd. Şti.
    Vergi No: 1234567890
    Tutar: 1.250,50 TL
    KDV: %20
    IBAN: TR12 0001 0004 6796 3186 2350 01
    """
    
    test_extracted = {
        'fatura_no': 'INV2024001',
        'tarih': '15.03.2024',
        'firma': 'ABC Ltd. Şti.',
        'vergi_no': '1234567890',
        'tutar': '1.250,50 TL',
        'kdv': '%20',
        'iban': 'TR12 0001 0004 6796 3186 2350 01'
    }
    
    validator = DocumentValidator()
    result = validator.validate(test_text, test_extracted, 'fatura')
    
    print(f"\n✅ Belge Geçerli: {result.is_valid}")
    print(f"📊 Kalite Puanı: {result.score}/100")
    print(f"⚠️ Uyarılar: {result.warnings_count}")
    print(f"❌ Hatalar: {result.errors_count}")
    print(f"🔥 Kritik: {result.critical_count}")
    
    print("\n" + validator.get_validation_report(result))
    
    # Eksik alan testi
    print("\n" + "="*50)
    print("🔴 EKSİK ALAN TESTİ")
    
    eksik_extracted = {
        'fatura_no': 'INV2024001',
        'firma': 'ABC Ltd. Şti.'
        # tarih, vergi_no, tutar eksik
    }
    
    result2 = validator.validate(test_text, eksik_extracted, 'fatura')
    print(validator.get_validation_report(result2))