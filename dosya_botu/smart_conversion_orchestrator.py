"""
AKILLI DÖNÜŞÜM ORKESTRATÖRÜ
Tüm dönüşümleri yönetir, en uygun yöntemi seçer ve kalite kontrolü yapar
"""

import os
import logging
import datetime
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

# Ana dönüşüm modülü
import converters

# Akıllı modüller
import analyzer
import ai_editor
import quality_optimizer

# Loglama
logger = logging.getLogger(__name__)


class ConversionStrategy(Enum):
    """Dönüşüm stratejileri"""
    DIRECT = "direct"           # Doğrudan dönüşüm
    SMART_EDIT = "smart_edit"   # Akıllı düzenleme + dönüşüm
    QUALITY_FIRST = "quality"    # Kalite öncelikli
    OCR_OPTIMIZED = "ocr"        # OCR optimize


class SmartConversionOrchestrator:
    """
    Akıllı Dönüşüm Orkestratörü
    Tüm dönüşümleri yönetir ve en iyi sonucu verir
    """
    
    def __init__(self):
        self.conversion_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'by_strategy': {}
        }
    
    async def convert_with_strategy(
        self,
        input_path: str,
        output_path: str,
        source_type: str,
        target_type: str,
        user_id: int = None,
        db_instance: Any = None,
        quality: str = "profesyonel",
        strategy: ConversionStrategy = None
    ) -> Tuple[bool, str, Dict]:
        """
        Belirtilen strateji ile dönüşüm yap
        """
        start_time = datetime.datetime.now()
        
        # Strateji belirlenmemişse otomatik seç
        if not strategy:
            strategy = self._select_best_strategy(input_path, source_type, target_type)
        
        logger.info(f"🎯 Seçilen strateji: {strategy.value}")
        
        result = {
            'success': False,
            'output_path': output_path,
            'strategy': strategy.value,
            'processing_time': 0,
            'quality_score': 0,
            'warnings': [],
            'steps': []
        }
        
        try:
            # 1. Dosya analizi
            analysis = None
            if strategy != ConversionStrategy.DIRECT:
                try:
                    analysis = analyzer.analyze_file(input_path)
                    result['steps'].append(f"Analiz tamamlandı: {analysis[0]}")
                except Exception as e:
                    result['warnings'].append(f"Analiz hatası: {e}")
            
            # 2. Kalite optimizasyonu (gerekirse)
            optimized_path = input_path
            if strategy == ConversionStrategy.QUALITY_FIRST:
                try:
                    optimizer = quality_optimizer.QualityOptimizer()
                    success, opt_path, opt_result = optimizer.optimize_document(
                        input_path, source_type, ""
                    )
                    if success:
                        optimized_path = opt_path
                        result['steps'].append(f"Kalite optimizasyonu yapıldı: %{opt_result.metrics.quality_score}")
                except Exception as e:
                    result['warnings'].append(f"Kalite optimizasyonu hatası: {e}")
            
            # 3. Akıllı düzenleme (gerekirse)
            edited_path = optimized_path
            if strategy == ConversionStrategy.SMART_EDIT:
                try:
                    editor = ai_editor.AIEditor()
                    edit_result = editor.edit(optimized_path, target_type, analysis)
                    if edit_result.success:
                        edited_path = edit_result.edited_content
                        result['steps'].append(f"Akıllı düzenleme yapıldı: {len(edit_result.changes_made)} değişiklik")
                except Exception as e:
                    result['warnings'].append(f"Akıllı düzenleme hatası: {e}")
            
            # 4. Dönüşüm
            success, out_path, conv_type, edit_summary, metrics = await converters.smart_convert_file(
                input_path=edited_path,
                output_path=output_path,
                source_type=source_type,
                target_type=target_type,
                user_id=user_id,
                db_instance=db_instance,
                quality=quality
            )
            
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            
            result['success'] = success
            result['output_path'] = out_path if success else output_path
            result['processing_time'] = processing_time
            result['quality_score'] = metrics.quality_score if metrics else 0
            
            # İstatistikleri güncelle
            self._update_stats(success, strategy)
            
            if success:
                logger.info(f"✅ Akıllı dönüşüm başarılı: {source_type} -> {target_type} ({processing_time:.2f}s)")
            else:
                logger.error(f"❌ Akıllı dönüşüm başarısız: {source_type} -> {target_type}")
            
            return success, out_path if success else output_path, result
            
        except Exception as e:
            logger.error(f"❌ Orkestratör hatası: {e}")
            import traceback
            traceback.print_exc()
            result['warnings'].append(str(e))
            return False, output_path, result
    
    def _select_best_strategy(self, input_path: str, source_type: str, target_type: str) -> ConversionStrategy:
        """
        En iyi dönüşüm stratejisini seç
        """
        # Dosya uzantısına bak
        ext = os.path.splitext(input_path)[1].lower()
        
        # Görsel dosyaları için OCR optimize
        if source_type == 'GORSEL':
            return ConversionStrategy.OCR_OPTIMIZED
        
        # PDF'ler için akıllı düzenleme
        if source_type == 'PDF' and target_type == 'WORD':
            return ConversionStrategy.SMART_EDIT
        
        # Kalite öncelikli dönüşümler
        if target_type in ['PDF', 'POWERPOINT']:
            return ConversionStrategy.QUALITY_FIRST
        
        # Varsayılan direkt dönüşüm
        return ConversionStrategy.DIRECT
    
    def _update_stats(self, success: bool, strategy: ConversionStrategy):
        """İstatistikleri güncelle"""
        self.conversion_stats['total'] += 1
        if success:
            self.conversion_stats['success'] += 1
        else:
            self.conversion_stats['failed'] += 1
        
        strategy_name = strategy.value
        if strategy_name not in self.conversion_stats['by_strategy']:
            self.conversion_stats['by_strategy'][strategy_name] = {'total': 0, 'success': 0}
        
        self.conversion_stats['by_strategy'][strategy_name]['total'] += 1
        if success:
            self.conversion_stats['by_strategy'][strategy_name]['success'] += 1
    
    def get_stats_report(self) -> str:
        """İstatistik raporu oluştur"""
        total = self.conversion_stats['total']
        if total == 0:
            return "Henüz dönüşüm yapılmamış."
        
        success_rate = (self.conversion_stats['success'] / total) * 100
        
        report = f"""📊 **AKILLI DÖNÜŞÜM İSTATİSTİKLERİ**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Toplam Dönüşüm: {total}
✅ Başarılı: {self.conversion_stats['success']} (%{success_rate:.1f})
❌ Başarısız: {self.conversion_stats['failed']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **STRATEJİ BAZLI İSTATİSTİKLER**
"""
        for strategy, stats in self.conversion_stats['by_strategy'].items():
            strategy_success = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report += f"  • {strategy}: {stats['total']} dönüşüm, %{strategy_success:.1f} başarı\n"
        
        return report


# Global orkestratör
_orchestrator = None


def get_orchestrator() -> SmartConversionOrchestrator:
    """Singleton orkestratör instance'ı döndür"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartConversionOrchestrator()
    return _orchestrator


async def smart_convert_with_strategy(
    input_path: str,
    output_path: str,
    source_type: str,
    target_type: str,
    user_id: int = None,
    db_instance: Any = None,
    quality: str = "profesyonel",
    strategy: str = None
) -> Tuple[bool, str, Dict]:
    """
    Stratejik akıllı dönüşüm yap
    
    Args:
        input_path: Kaynak dosya yolu
        output_path: Hedef dosya yolu
        source_type: Kaynak tip
        target_type: Hedef tip
        user_id: Kullanıcı ID
        db_instance: Veritabanı instance
        quality: Kalite seviyesi
        strategy: Strateji (direct, smart_edit, quality, ocr)
    
    Returns:
        (başarılı_mı, çıktı_dosyası, sonuç_dict)
    """
    orchestrator = get_orchestrator()
    
    strategy_map = {
        'direct': ConversionStrategy.DIRECT,
        'smart_edit': ConversionStrategy.SMART_EDIT,
        'quality': ConversionStrategy.QUALITY_FIRST,
        'ocr': ConversionStrategy.OCR_OPTIMIZED
    }
    
    selected_strategy = strategy_map.get(strategy) if strategy else None
    
    return await orchestrator.convert_with_strategy(
        input_path=input_path,
        output_path=output_path,
        source_type=source_type,
        target_type=target_type,
        user_id=user_id,
        db_instance=db_instance,
        quality=quality,
        strategy=selected_strategy
    )
