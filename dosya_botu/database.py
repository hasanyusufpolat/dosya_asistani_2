"""
GELİŞMİŞ VERİTABANI YÖNETİM SİSTEMİ
Tüm veritabanı işlemleri bu dosyada profesyonelce yönetilir
Hak yönetimi, istatistikler ve aktivite takibi
YENİ: Akıllı isimlendirme, sınıflandırma, özetleme, doğrulama, kalite optimizasyonu
"""

import sqlite3
import os
import datetime
import logging
import json
from contextlib import contextmanager
from typing import Optional, Dict, List, Any, Tuple
from config import DEFAULT_PACKAGE_SIZE, QUALITY_LEVELS

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Profesyonel Veritabanı Yöneticisi"""
    
    def __init__(self, db_path: str = 'database/bot.db'):
        self.db_path = db_path
        self._ensure_database_dir()
        
    def _ensure_database_dir(self):
        """Veritabanı klasörünün varlığını kontrol et"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"📁 Veritabanı klasörü oluşturuldu: {db_dir}")
    
    @contextmanager
    def get_connection(self):
        """Veritabanı bağlantısını yönet (context manager)"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Sözlük benzeri erişim
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ Veritabanı hatası: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("🔌 Veritabanı bağlantısı kapatıldı")
    
    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[Dict]]:
        """SQL sorgusunu çalıştır ve sonuçları sözlük listesi olarak döndür"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return None
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """INSERT sorgusu çalıştır ve son eklenen ID'yi döndür"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid
    
    # ========== TABLO OLUŞTURMA VE GÜNCELLEME ==========
    
    def create_tables(self):
        """Tüm veritabanı tablolarını oluştur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # KULLANICILAR ANA TABLOSU - YENİ SÜTUNLAR EKLENDİ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'tr',
                    is_premium BOOLEAN DEFAULT 0,
                    package_type TEXT DEFAULT '30',
                    remaining_rights INTEGER DEFAULT 30,
                    total_conversions INTEGER DEFAULT 0,
                    successful_conversions INTEGER DEFAULT 0,
                    failed_conversions INTEGER DEFAULT 0,
                    total_analysis INTEGER DEFAULT 0,
                    total_smart_edits INTEGER DEFAULT 0,
                    total_naming INTEGER DEFAULT 0,
                    total_classification INTEGER DEFAULT 0,
                    total_summaries INTEGER DEFAULT 0,
                    total_validations INTEGER DEFAULT 0,
                    total_quality_optimizations INTEGER DEFAULT 0,  -- YENİ: Kalite optimizasyonu
                    total_premium_conversions INTEGER DEFAULT 0,    -- YENİ: Premium dönüşümler
                    last_activity TEXT,
                    registered_at TEXT,
                    updated_at TEXT,
                    notes TEXT
                )
            ''')
            logger.info("✅ Users tablosu oluşturuldu/kontrol edildi (yeni sütunlar eklendi)")
            
            # KULLANICI AKTİVİTE LOGLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ User activity tablosu oluşturuldu")
            
            # DÖNÜŞÜM KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    source_format TEXT NOT NULL,
                    target_format TEXT NOT NULL,
                    conversion_type TEXT DEFAULT 'direct',
                    quality_level TEXT DEFAULT 'standard',
                    status TEXT NOT NULL,
                    processing_time REAL,
                    quality_score INTEGER DEFAULT 0,
                    error_message TEXT,
                    converted_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Conversions tablosu oluşturuldu (quality_level eklendi)")
            
            # ANALİZ KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    confidence INTEGER,
                    structure_score INTEGER,
                    readability_score INTEGER,
                    complexity_level TEXT,
                    issues TEXT,
                    analyzed_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Analysis records tablosu oluşturuldu")
            
            # İSİMLENDİRME KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS naming_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    original_name TEXT NOT NULL,
                    new_name TEXT NOT NULL,
                    extracted_info TEXT,
                    confidence INTEGER,
                    named_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Naming records tablosu oluşturuldu")
            
            # SINIFLANDIRMA KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classification_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence INTEGER,
                    allowed_formats TEXT,
                    extracted_fields TEXT,
                    classified_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Classification records tablosu oluşturuldu")
            
            # ÖZETLEME KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summary_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    key_points TEXT,
                    word_count INTEGER,
                    confidence INTEGER,
                    summarized_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Summary records tablosu oluşturuldu")
            
            # DOĞRULAMA KAYITLARI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    issues TEXT,
                    warnings_count INTEGER,
                    errors_count INTEGER,
                    critical_count INTEGER,
                    score INTEGER,
                    validated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Validation records tablosu oluşturuldu")
            
            # KALİTE OPTİMİZASYONU KAYITLARI (YENİ)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    original_quality_score INTEGER,
                    optimized_quality_score INTEGER,
                    quality_level TEXT NOT NULL,
                    optimizations TEXT,
                    processing_time REAL,
                    optimized_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Quality records tablosu oluşturuldu")
            
            # PAKET GEÇMİŞİ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS package_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    package_type TEXT NOT NULL,
                    rights_added INTEGER NOT NULL,
                    amount_paid REAL,
                    payment_method TEXT,
                    purchased_at TEXT NOT NULL,
                    expires_at TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ Package history tablosu oluşturuldu")
            
            # GÜNLÜK İSTATİSTİKLER (YENİ)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    total_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    total_conversions INTEGER DEFAULT 0,
                    successful_conversions INTEGER DEFAULT 0,
                    failed_conversions INTEGER DEFAULT 0,
                    total_analysis INTEGER DEFAULT 0,
                    total_quality INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    created_at TEXT
                )
            ''')
            logger.info("✅ Daily stats tablosu oluşturuldu")
            
            # İNDİCE'LER (Performans için)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversions_user_id ON conversions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversions_date ON conversions(converted_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis_records(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_naming_user_id ON naming_records(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification_user_id ON classification_records(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_summary_user_id ON summary_records(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_validation_user_id ON validation_records(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_user_id ON quality_records(user_id)')  # YENİ
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_package_user_id ON package_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)')  # YENİ
            
            logger.info("✅ Veritabanı indeksleri oluşturuldu")
            conn.commit()
    
    def upgrade_database(self):
        """Veritabanını güncelle (eski sürümlerden yeni sürüme)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # users tablosundaki sütunları kontrol et
                cursor.execute("PRAGMA table_info(users)")
                columns = [col['name'] for col in cursor.fetchall()]
                
                # YENİ SÜTUNLAR - Kalite optimizasyonu için
                new_columns = [
                    ('total_quality_optimizations', 'INTEGER DEFAULT 0'),
                    ('total_premium_conversions', 'INTEGER DEFAULT 0')
                ]
                
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        logger.info(f"🔄 '{col_name}' sütunu ekleniyor...")
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                        logger.info(f"✅ '{col_name}' sütunu eklendi")
                
                # Mevcut sütunlar
                existing_columns = [
                    ('total_naming', 'INTEGER DEFAULT 0'),
                    ('total_classification', 'INTEGER DEFAULT 0'),
                    ('total_summaries', 'INTEGER DEFAULT 0'),
                    ('total_validations', 'INTEGER DEFAULT 0')
                ]
                
                for col_name, col_type in existing_columns:
                    if col_name not in columns:
                        logger.info(f"🔄 '{col_name}' sütunu ekleniyor...")
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                        logger.info(f"✅ '{col_name}' sütunu eklendi")
                
                if 'total_conversions' not in columns:
                    logger.info("🔄 'total_conversions' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN total_conversions INTEGER DEFAULT 0")
                    cursor.execute("UPDATE users SET total_conversions = 0 WHERE total_conversions IS NULL")
                    logger.info("✅ 'total_conversions' sütunu eklendi")
                
                if 'successful_conversions' not in columns:
                    logger.info("🔄 'successful_conversions' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN successful_conversions INTEGER DEFAULT 0")
                    cursor.execute("UPDATE users SET successful_conversions = 0 WHERE successful_conversions IS NULL")
                    logger.info("✅ 'successful_conversions' sütunu eklendi")
                
                if 'failed_conversions' not in columns:
                    logger.info("🔄 'failed_conversions' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN failed_conversions INTEGER DEFAULT 0")
                    cursor.execute("UPDATE users SET failed_conversions = 0 WHERE failed_conversions IS NULL")
                    logger.info("✅ 'failed_conversions' sütunu eklendi")
                
                if 'total_analysis' not in columns:
                    logger.info("🔄 'total_analysis' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN total_analysis INTEGER DEFAULT 0")
                    logger.info("✅ 'total_analysis' sütunu eklendi")
                
                if 'total_smart_edits' not in columns:
                    logger.info("🔄 'total_smart_edits' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN total_smart_edits INTEGER DEFAULT 0")
                    logger.info("✅ 'total_smart_edits' sütunu eklendi")
                
                if 'last_name' not in columns:
                    logger.info("🔄 'last_name' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
                    logger.info("✅ 'last_name' sütunu eklendi")
                
                if 'language_code' not in columns:
                    logger.info("🔄 'language_code' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT 'tr'")
                    logger.info("✅ 'language_code' sütunu eklendi")
                
                if 'is_premium' not in columns:
                    logger.info("🔄 'is_premium' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0")
                    logger.info("✅ 'is_premium' sütunu eklendi")
                
                if 'updated_at' not in columns:
                    logger.info("🔄 'updated_at' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
                    cursor.execute("UPDATE users SET updated_at = last_activity WHERE updated_at IS NULL")
                    logger.info("✅ 'updated_at' sütunu eklendi")
                
                if 'notes' not in columns:
                    logger.info("🔄 'notes' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE users ADD COLUMN notes TEXT")
                    logger.info("✅ 'notes' sütunu eklendi")
                
                # conversions tablosunu kontrol et
                cursor.execute("PRAGMA table_info(conversions)")
                conv_columns = [col['name'] for col in cursor.fetchall()]
                
                if 'conversion_type' not in conv_columns:
                    logger.info("🔄 'conversion_type' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE conversions ADD COLUMN conversion_type TEXT DEFAULT 'direct'")
                    logger.info("✅ 'conversion_type' sütunu eklendi")
                
                if 'quality_level' not in conv_columns:
                    logger.info("🔄 'quality_level' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE conversions ADD COLUMN quality_level TEXT DEFAULT 'standard'")
                    logger.info("✅ 'quality_level' sütunu eklendi")
                
                if 'quality_score' not in conv_columns:
                    logger.info("🔄 'quality_score' sütunu ekleniyor...")
                    cursor.execute("ALTER TABLE conversions ADD COLUMN quality_score INTEGER DEFAULT 0")
                    logger.info("✅ 'quality_score' sütunu eklendi")
                
                conn.commit()
                logger.info("✅ Veritabanı güncellemesi tamamlandı (yeni işlem tipleri eklendi)")
                
        except Exception as e:
            logger.error(f"❌ Veritabanı güncellenirken hata: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== KULLANICI İŞLEMLERİ ==========
    
    def register_user(self, user) -> bool:
        """
        Kullanıcıyı veritabanına kaydet veya güncelle
        Returns: Başarılı ise True, değilse False
        """
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = user.username or ""
            first_name = user.first_name or ""
            last_name = getattr(user, 'last_name', "") or ""
            language_code = getattr(user, 'language_code', "tr") or "tr"
            is_premium = 1 if getattr(user, 'is_premium', False) else 0
            
            # Kullanıcı var mı kontrol et
            existing = self.execute_query(
                "SELECT * FROM users WHERE user_id = ?", 
                (user.id,)
            )
            
            if not existing:
                # YENİ KULLANICI - Tüm yeni sütunlarla
                query = '''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, language_code, is_premium,
                     remaining_rights, total_conversions, successful_conversions, 
                     failed_conversions, total_analysis, total_smart_edits,
                     total_naming, total_classification, total_summaries, total_validations,
                     total_quality_optimizations, total_premium_conversions,
                     last_activity, registered_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?, ?)
                '''
                self.execute_query(query, (
                    user.id, username, first_name, last_name, language_code, is_premium,
                    DEFAULT_PACKAGE_SIZE, now, now, now
                ))
                
                # Aktivite kaydı
                self.log_user_activity(user.id, 'registration', 'Yeni kullanıcı kaydı')
                
                # Günlük istatistikleri güncelle
                self.update_daily_stats(new_users=1)
                
                logger.info(f"✅ YENİ KULLANICI KAYDEDİLDİ: {user.id} - @{username}")
                return True
            else:
                # MEVCUT KULLANICI - Bilgileri güncelle
                query = '''
                    UPDATE users SET 
                        username = ?,
                        first_name = ?,
                        last_name = ?,
                        language_code = ?,
                        is_premium = ?,
                        last_activity = ?,
                        updated_at = ?
                    WHERE user_id = ?
                '''
                self.execute_query(query, (
                    username, first_name, last_name, language_code, is_premium, 
                    now, now, user.id
                ))
                
                # Aktivite kaydı
                self.log_user_activity(user.id, 'login', 'Kullanıcı girişi')
                
                logger.info(f"✅ KULLANICI GÜNCELLENDİ: {user.id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Kullanıcı kaydedilirken hata: {e}")
            return False
    
    def log_user_activity(self, user_id: int, activity_type: str, details: str = ""):
        """Kullanıcı aktivitelerini kaydet"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = '''
                INSERT INTO user_activity (user_id, activity_type, details, created_at)
                VALUES (?, ?, ?, ?)
            '''
            self.execute_query(query, (user_id, activity_type, details, now))
            logger.debug(f"📝 Aktivite kaydedildi: {user_id} - {activity_type}")
        except Exception as e:
            logger.error(f"❌ Aktivite kaydedilirken hata: {e}")
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Kullanıcı bilgilerini detaylı getir"""
        try:
            result = self.execute_query(
                "SELECT * FROM users WHERE user_id = ?", 
                (user_id,)
            )
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Kullanıcı bilgisi alınırken hata: {e}")
            return None
    
    def get_remaining_rights(self, user_id: int) -> int:
        """Kullanıcının kalan hakkını getir"""
        try:
            result = self.execute_query(
                "SELECT remaining_rights FROM users WHERE user_id = ?", 
                (user_id,)
            )
            return result[0]['remaining_rights'] if result else 0
        except Exception as e:
            logger.error(f"❌ Hak sorgulanırken hata: {e}")
            return 0
    
    def decrease_rights(self, user_id: int, conversion_type: str = 'direct', quality_level: str = 'standard') -> bool:
        """
        Kullanıcının hakkını 1 azalt (BAŞARILI işlem)
        conversion_type: 'direct', 'smart_edit', 'quality'
        quality_level: 'draft', 'standard', 'professional', 'premium'
        """
        try:
            # Önce mevcut hakları kontrol et
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    successful_conversions = successful_conversions + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            # Premium dönüşüm sayacı
            if quality_level == 'premium':
                self.execute_query("""
                    UPDATE users SET total_premium_conversions = total_premium_conversions + 1
                    WHERE user_id = ?
                """, (user_id,))
            
            activity_detail = f"Başarılı dönüşüm ({conversion_type}, {quality_level})"
            self.log_user_activity(user_id, 'conversion_success', activity_detail)
            
            # Günlük istatistikleri güncelle
            self.update_daily_stats(successful_conversions=1)
            
            logger.info(f"✅ Kullanıcı {user_id} hakkı azaltıldı. Kalan: {current-1} ({conversion_type}, {quality_level})")
            return True
        except Exception as e:
            logger.error(f"❌ Hak azaltılırken hata: {e}")
            return False
    
    # ========== YENİ İŞLEM FONKSİYONLARI ==========
    
    def increase_naming_count(self, user_id: int) -> bool:
        """Akıllı isimlendirme sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin isimlendirme için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_naming = total_naming + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'naming', 'Akıllı dosya isimlendirme yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} isimlendirme hakkı tüketildi. Kalan: {current-1}")
            return True
        except Exception as e:
            logger.error(f"❌ İsimlendirme sayısı artırılırken hata: {e}")
            return False
    
    def increase_classification_count(self, user_id: int) -> bool:
        """Belge sınıflandırma sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin sınıflandırma için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_classification = total_classification + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'classification', 'Belge sınıflandırma yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} sınıflandırma hakkı tüketildi. Kalan: {current-1}")
            return True
        except Exception as e:
            logger.error(f"❌ Sınıflandırma sayısı artırılırken hata: {e}")
            return False
    
    def increase_summary_count(self, user_id: int) -> bool:
        """Belge özetleme sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin özetleme için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_summaries = total_summaries + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'summary', 'Belge özetleme yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} özetleme hakkı tüketildi. Kalan: {current-1}")
            return True
        except Exception as e:
            logger.error(f"❌ Özetleme sayısı artırılırken hata: {e}")
            return False
    
    def increase_validation_count(self, user_id: int) -> bool:
        """Belge doğrulama sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin doğrulama için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_validations = total_validations + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'validation', 'Belge doğrulama yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} doğrulama hakkı tüketildi. Kalan: {current-1}")
            return True
        except Exception as e:
            logger.error(f"❌ Doğrulama sayısı artırılırken hata: {e}")
            return False
    
    def increase_analysis_count(self, user_id: int) -> bool:
        """Analiz sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin analiz için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_analysis = total_analysis + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'analysis', 'Dosya analizi yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} analiz hakkı tüketildi. Kalan: {current-1}")
            
            # Günlük istatistikleri güncelle
            self.update_daily_stats(total_analysis=1)
            
            return True
        except Exception as e:
            logger.error(f"❌ Analiz sayısı artırılırken hata: {e}")
            return False
    
    def increase_quality_count(self, user_id: int) -> bool:
        """Kalite optimizasyonu sayısını artır (1 HAK TÜKETİR)"""
        try:
            current = self.get_remaining_rights(user_id)
            if current <= 0:
                logger.warning(f"⚠️ Kullanıcı {user_id}'nin kalite optimizasyonu için hakkı kalmamış!")
                return False
            
            query = """
                UPDATE users SET 
                    remaining_rights = remaining_rights - 1,
                    total_quality_optimizations = total_quality_optimizations + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ? AND remaining_rights > 0
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'quality', 'Kalite optimizasyonu yapıldı')
            logger.info(f"✅ Kullanıcı {user_id} kalite optimizasyonu hakkı tüketildi. Kalan: {current-1}")
            
            # Günlük istatistikleri güncelle
            self.update_daily_stats(total_quality=1)
            
            return True
        except Exception as e:
            logger.error(f"❌ Kalite optimizasyonu sayısı artırılırken hata: {e}")
            return False
    
    def increase_failed_count(self, user_id: int) -> bool:
        """Başarısız işlem sayısını artır (HAK GİTMEZ)"""
        try:
            query = """
                UPDATE users SET 
                    failed_conversions = failed_conversions + 1,
                    total_conversions = total_conversions + 1,
                    last_activity = ?,
                    updated_at = ?
                WHERE user_id = ?
            """
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(query, (now, now, user_id))
            
            self.log_user_activity(user_id, 'conversion_failed', 'Başarısız işlem')
            logger.info(f"✅ Kullanıcı {user_id} başarısız işlem kaydedildi.")
            
            # Günlük istatistikleri güncelle
            self.update_daily_stats(failed_conversions=1)
            
            return True
        except Exception as e:
            logger.error(f"❌ Başarısız sayısı artırılırken hata: {e}")
            return False
    
    def add_rights(self, user_id: int, rights_to_add: int, package_id: str = None, amount: float = 0) -> bool:
        """Kullanıcıya hak ekle (paket satın alımında)"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Mevcut hakları kontrol et
            current = self.get_remaining_rights(user_id)
            
            if package_id:
                query = """
                    UPDATE users SET 
                        remaining_rights = remaining_rights + ?,
                        package_type = ?,
                        last_activity = ?,
                        updated_at = ?
                    WHERE user_id = ?
                """
                self.execute_query(query, (rights_to_add, package_id, now, now, user_id))
                
                # Paket geçmişine ekle
                self.add_package_history(user_id, package_id, rights_to_add, amount)
            else:
                query = """
                    UPDATE users SET 
                        remaining_rights = remaining_rights + ?,
                        last_activity = ?,
                        updated_at = ?
                    WHERE user_id = ?
                """
                self.execute_query(query, (rights_to_add, now, now, user_id))
            
            self.log_user_activity(user_id, 'rights_added', f'+{rights_to_add} hak eklendi')
            logger.info(f"✅ Kullanıcı {user_id} - {rights_to_add} hak eklendi. Yeni toplam: {current + rights_to_add}")
            
            # Günlük istatistikleri güncelle (gelir)
            self.update_daily_stats(revenue=amount)
            
            return True
        except Exception as e:
            logger.error(f"❌ Hak eklenirken hata: {e}")
            return False
    
    def add_package_history(self, user_id: int, package_type: str, rights_added: int, amount: float = 0):
        """Paket satın alma geçmişine ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = '''
                INSERT INTO package_history 
                (user_id, package_type, rights_added, amount_paid, purchased_at)
                VALUES (?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (user_id, package_type, rights_added, amount, now))
            logger.info(f"📦 Paket geçmişi kaydedildi: {user_id} - {package_type} - {amount} TL")
        except Exception as e:
            logger.error(f"❌ Paket geçmişi eklenirken hata: {e}")
    
    # ========== ANALİZ KAYITLARI ==========
    
    def save_analysis_record(self, user_id: int, file_name: str, file_type: str, 
                            decision: str, confidence: int, structure_score: int,
                            readability_score: int, issues: List[str]) -> bool:
        """Analiz kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            issues_text = ', '.join(issues) if issues else ''
            
            query = '''
                INSERT INTO analysis_records 
                (user_id, file_name, file_type, decision, confidence, 
                 structure_score, readability_score, issues, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, file_type, decision, confidence,
                structure_score, readability_score, issues_text, now
            ))
            
            logger.info(f"📊 Analiz kaydedildi: {user_id} - {decision}")
            return True
        except Exception as e:
            logger.error(f"❌ Analiz kaydı eklenirken hata: {e}")
            return False
    
    # ========== İSİMLENDİRME KAYITLARI ==========
    
    def save_naming_record(self, user_id: int, original_name: str, new_name: str, 
                          extracted_info: Dict, confidence: int) -> bool:
        """İsimlendirme kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_text = json.dumps(extracted_info, ensure_ascii=False)
            
            query = '''
                INSERT INTO naming_records 
                (user_id, original_name, new_name, extracted_info, confidence, named_at)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, original_name, new_name, info_text, confidence, now
            ))
            
            logger.info(f"📝 İsimlendirme kaydedildi: {user_id} - {original_name} -> {new_name}")
            return True
        except Exception as e:
            logger.error(f"❌ İsimlendirme kaydı eklenirken hata: {e}")
            return False
    
    # ========== SINIFLANDIRMA KAYITLARI ==========
    
    def save_classification_record(self, user_id: int, file_name: str, document_type: str,
                                  category: str, confidence: int, allowed_formats: List[str],
                                  extracted_fields: Dict) -> bool:
        """Sınıflandırma kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formats_text = ', '.join(allowed_formats)
            fields_text = json.dumps(extracted_fields, ensure_ascii=False)
            
            query = '''
                INSERT INTO classification_records 
                (user_id, file_name, document_type, category, confidence, 
                 allowed_formats, extracted_fields, classified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, document_type, category, confidence,
                formats_text, fields_text, now
            ))
            
            logger.info(f"📊 Sınıflandırma kaydedildi: {user_id} - {document_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Sınıflandırma kaydı eklenirken hata: {e}")
            return False
    
    # ========== ÖZETLEME KAYITLARI ==========
    
    def save_summary_record(self, user_id: int, file_name: str, summary: str,
                           key_points: List[str], word_count: int, confidence: int) -> bool:
        """Özetleme kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            points_text = '\n'.join(key_points) if key_points else ''
            
            query = '''
                INSERT INTO summary_records 
                (user_id, file_name, summary, key_points, word_count, confidence, summarized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, summary, points_text, word_count, confidence, now
            ))
            
            logger.info(f"📋 Özetleme kaydedildi: {user_id} - {file_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Özetleme kaydı eklenirken hata: {e}")
            return False
    
    # ========== DOĞRULAMA KAYITLARI ==========
    
    def save_validation_record(self, user_id: int, file_name: str, is_valid: bool,
                              issues: List[str], warnings_count: int, errors_count: int,
                              critical_count: int, score: int) -> bool:
        """Doğrulama kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            issues_text = '\n'.join(issues) if issues else ''
            
            query = '''
                INSERT INTO validation_records 
                (user_id, file_name, is_valid, issues, warnings_count, 
                 errors_count, critical_count, score, validated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, 1 if is_valid else 0, issues_text,
                warnings_count, errors_count, critical_count, score, now
            ))
            
            logger.info(f"✅ Doğrulama kaydedildi: {user_id} - {file_name} - Puan: {score}")
            return True
        except Exception as e:
            logger.error(f"❌ Doğrulama kaydı eklenirken hata: {e}")
            return False
    
    # ========== KALİTE OPTİMİZASYONU KAYITLARI ==========
    
    def save_quality_record(self, user_id: int, file_name: str, original_score: int,
                           optimized_score: int, quality_level: str, optimizations: List[str],
                           processing_time: float) -> bool:
        """Kalite optimizasyonu kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            optimizations_text = '\n'.join(optimizations) if optimizations else ''
            
            query = '''
                INSERT INTO quality_records 
                (user_id, file_name, original_quality_score, optimized_quality_score,
                 quality_level, optimizations, processing_time, optimized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, original_score, optimized_score,
                quality_level, optimizations_text, processing_time, now
            ))
            
            logger.info(f"⭐ Kalite kaydedildi: {user_id} - {file_name} - {original_score}->{optimized_score}")
            return True
        except Exception as e:
            logger.error(f"❌ Kalite kaydı eklenirken hata: {e}")
            return False
    
    # ========== DÖNÜŞÜM KAYITLARI ==========
    
    def save_conversion_record(self, user_id: int, file_name: str, file_size: int, 
                              source_format: str, target_format: str, status: str, 
                              processing_time: float, conversion_type: str = 'direct',
                              quality_level: str = 'standard', quality_score: int = 0,
                              error_message: str = None) -> bool:
        """Dönüşüm kaydını veritabanına ekle"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = '''
                INSERT INTO conversions 
                (user_id, file_name, file_size, source_format, target_format, 
                 conversion_type, quality_level, status, processing_time, 
                 quality_score, error_message, converted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.execute_query(query, (
                user_id, file_name, file_size, source_format, target_format,
                conversion_type, quality_level, status, processing_time,
                quality_score, error_message, now
            ))
            
            logger.info(f"📁 Dönüşüm kaydedildi: {user_id} - {source_format}->{target_format} - {status} ({conversion_type}, {quality_level})")
            return True
        except Exception as e:
            logger.error(f"❌ Dönüşüm kaydı eklenirken hata: {e}")
            return False
    
    # ========== GÜNLÜK İSTATİSTİKLER ==========
    
    def update_daily_stats(self, new_users: int = 0, successful_conversions: int = 0,
                          failed_conversions: int = 0, total_analysis: int = 0,
                          total_quality: int = 0, revenue: float = 0):
        """Günlük istatistikleri güncelle"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Bugünkü kayıt var mı kontrol et
            existing = self.execute_query(
                "SELECT * FROM daily_stats WHERE date = ?", (today,)
            )
            
            if existing:
                # Güncelle
                query = """
                    UPDATE daily_stats SET
                        new_users = new_users + ?,
                        successful_conversions = successful_conversions + ?,
                        failed_conversions = failed_conversions + ?,
                        total_analysis = total_analysis + ?,
                        total_quality = total_quality + ?,
                        revenue = revenue + ?,
                        total_users = (SELECT COUNT(*) FROM users),
                        active_users = (
                            SELECT COUNT(DISTINCT user_id) FROM user_activity 
                            WHERE date(created_at) = date('now')
                        ),
                        updated_at = ?
                    WHERE date = ?
                """
                self.execute_query(query, (
                    new_users, successful_conversions, failed_conversions,
                    total_analysis, total_quality, revenue, now, today
                ))
            else:
                # Yeni kayıt
                query = """
                    INSERT INTO daily_stats 
                    (date, total_users, new_users, active_users, successful_conversions,
                     failed_conversions, total_analysis, total_quality, revenue, created_at)
                    VALUES (
                        ?,
                        (SELECT COUNT(*) FROM users),
                        ?,
                        (SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE date(created_at) = date('now')),
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                """
                self.execute_query(query, (
                    today, new_users, successful_conversions, failed_conversions,
                    total_analysis, total_quality, revenue, now
                ))
            
            logger.debug(f"📊 Günlük istatistikler güncellendi: {today}")
            
        except Exception as e:
            logger.error(f"❌ Günlük istatistik güncellenirken hata: {e}")
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Son N günün istatistiklerini getir"""
        try:
            return self.execute_query('''
                SELECT * FROM daily_stats 
                ORDER BY date DESC 
                LIMIT ?
            ''', (days,))
        except Exception as e:
            logger.error(f"❌ Günlük istatistikler alınırken hata: {e}")
            return []
    
    # ========== İSTATİSTİKLER ==========
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Kullanıcı istatistiklerini detaylı getir (TÜM İŞLEMLER)"""
        try:
            # Kullanıcı bilgileri
            user = self.execute_query('''
                SELECT 
                    remaining_rights,
                    total_conversions,
                    successful_conversions,
                    failed_conversions,
                    total_analysis,
                    total_smart_edits,
                    total_naming,
                    total_classification,
                    total_summaries,
                    total_validations,
                    total_quality_optimizations,
                    total_premium_conversions,
                    registered_at
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            
            if not user:
                return None
            
            # Bugünkü işlem sayısı
            today = self.execute_query('''
                SELECT COUNT(*) as count FROM conversions 
                WHERE user_id = ? AND date(converted_at) = date('now')
            ''', (user_id,))
            
            # Bugünkü analiz sayısı
            today_analysis = self.execute_query('''
                SELECT COUNT(*) as count FROM analysis_records 
                WHERE user_id = ? AND date(analyzed_at) = date('now')
            ''', (user_id,))
            
            # Son 7 günlük işlemler
            weekly = self.execute_query('''
                SELECT COUNT(*) as count FROM conversions 
                WHERE user_id = ? AND converted_at >= date('now', '-7 days')
            ''', (user_id,))
            
            # Son 30 günlük işlemler
            monthly = self.execute_query('''
                SELECT COUNT(*) as count FROM conversions 
                WHERE user_id = ? AND converted_at >= date('now', '-30 days')
            ''', (user_id,))
            
            # Akıllı düzenleme sayısı
            smart_edits = self.execute_query('''
                SELECT COUNT(*) as count FROM conversions 
                WHERE user_id = ? AND conversion_type = 'smart_edit' AND status = 'success'
            ''', (user_id,))
            
            # Kalite optimizasyonu sayısı
            quality_ops = self.execute_query('''
                SELECT COUNT(*) as count FROM quality_records 
                WHERE user_id = ?
            ''', (user_id,))
            
            u = user[0]
            return {
                'remaining': u['remaining_rights'],
                'total': u['total_conversions'] or 0,
                'success': u['successful_conversions'] or 0,
                'failed': u['failed_conversions'] or 0,
                'total_analysis': u['total_analysis'] or 0,
                'total_smart_edits': u['total_smart_edits'] or 0,
                'total_naming': u['total_naming'] or 0,
                'total_classification': u['total_classification'] or 0,
                'total_summaries': u['total_summaries'] or 0,
                'total_validations': u['total_validations'] or 0,
                'total_quality': u['total_quality_optimizations'] or 0,
                'total_premium': u['total_premium_conversions'] or 0,
                'today': today[0]['count'] if today else 0,
                'today_analysis': today_analysis[0]['count'] if today_analysis else 0,
                'weekly': weekly[0]['count'] if weekly else 0,
                'monthly': monthly[0]['count'] if monthly else 0,
                'smart_edits': smart_edits[0]['count'] if smart_edits else 0,
                'quality_ops': quality_ops[0]['count'] if quality_ops else 0,
                'registered_at': u['registered_at']
            }
        except Exception as e:
            logger.error(f"❌ İstatistik alınırken hata: {e}")
            return None
    
    def get_admin_stats(self) -> Optional[Dict]:
        """Admin için sistem istatistikleri (SÜPER GELİŞMİŞ)"""
        try:
            # Toplam kullanıcı
            total_users = self.execute_query("SELECT COUNT(*) as count FROM users")
            
            # Aktif kullanıcılar (son 24 saat)
            active_users = self.execute_query('''
                SELECT COUNT(DISTINCT user_id) as count FROM user_activity 
                WHERE created_at >= datetime('now', '-1 day')
            ''')
            
            # Bugünkü işlemler
            today_conversions = self.execute_query(
                "SELECT COUNT(*) as count FROM conversions WHERE date(converted_at) = date('now')"
            )
            
            today_analysis = self.execute_query(
                "SELECT COUNT(*) as count FROM analysis_records WHERE date(analyzed_at) = date('now')"
            )
            
            today_naming = self.execute_query(
                "SELECT COUNT(*) as count FROM naming_records WHERE date(named_at) = date('now')"
            )
            
            today_classification = self.execute_query(
                "SELECT COUNT(*) as count FROM classification_records WHERE date(classified_at) = date('now')"
            )
            
            today_summaries = self.execute_query(
                "SELECT COUNT(*) as count FROM summary_records WHERE date(summarized_at) = date('now')"
            )
            
            today_validations = self.execute_query(
                "SELECT COUNT(*) as count FROM validation_records WHERE date(validated_at) = date('now')"
            )
            
            today_quality = self.execute_query(
                "SELECT COUNT(*) as count FROM quality_records WHERE date(optimized_at) = date('now')"
            )
            
            # Başarılı/başarısız dönüşümler
            success_total = self.execute_query(
                "SELECT COUNT(*) as count FROM conversions WHERE status='success'"
            )
            
            failed_total = self.execute_query(
                "SELECT COUNT(*) as count FROM conversions WHERE status='failed'"
            )
            
            # Toplam işlemler (kullanıcı bazlı)
            total_success = self.execute_query(
                "SELECT SUM(successful_conversions) as sum FROM users"
            )
            
            total_failed = self.execute_query(
                "SELECT SUM(failed_conversions) as sum FROM users"
            )
            
            total_analysis = self.execute_query(
                "SELECT SUM(total_analysis) as sum FROM users"
            )
            
            total_naming = self.execute_query(
                "SELECT SUM(total_naming) as sum FROM users"
            )
            
            total_classification = self.execute_query(
                "SELECT SUM(total_classification) as sum FROM users"
            )
            
            total_summaries = self.execute_query(
                "SELECT SUM(total_summaries) as sum FROM users"
            )
            
            total_validations = self.execute_query(
                "SELECT SUM(total_validations) as sum FROM users"
            )
            
            total_quality = self.execute_query(
                "SELECT SUM(total_quality_optimizations) as sum FROM users"
            )
            
            total_premium = self.execute_query(
                "SELECT SUM(total_premium_conversions) as sum FROM users"
            )
            
            # Toplam gelir
            total_revenue = self.execute_query(
                "SELECT SUM(amount_paid) as sum FROM package_history"
            )
            
            # En çok kullanılan formatlar
            top_formats = self.execute_query('''
                SELECT target_format, COUNT(*) as count 
                FROM conversions 
                GROUP BY target_format 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            
            # En çok kullanılan kalite seviyeleri
            top_quality = self.execute_query('''
                SELECT quality_level, COUNT(*) as count 
                FROM conversions 
                WHERE quality_level IS NOT NULL
                GROUP BY quality_level 
                ORDER BY count DESC 
            ''')
            
            # Son 7 günlük işlem grafiği
            weekly_stats = self.execute_query('''
                SELECT date(converted_at) as date, COUNT(*) as count
                FROM conversions
                WHERE converted_at >= date('now', '-7 days')
                GROUP BY date(converted_at)
                ORDER BY date DESC
            ''')
            
            # Son 30 günlük gelir
            monthly_revenue = self.execute_query('''
                SELECT date(purchased_at) as date, SUM(amount_paid) as total
                FROM package_history
                WHERE purchased_at >= date('now', '-30 days')
                GROUP BY date(purchased_at)
                ORDER BY date DESC
            ''')
            
            format_text = "\n".join([f"  • {f['target_format']}: {f['count']}" for f in top_formats]) if top_formats else "  • Veri yok"
            
            quality_text = "\n".join([f"  • {q['quality_level']}: {q['count']}" for q in top_quality]) if top_quality else "  • Veri yok"
            
            weekly_text = "\n".join([f"  • {w['date']}: {w['count']} işlem" for w in weekly_stats]) if weekly_stats else "  • Veri yok"
            
            revenue_text = "\n".join([f"  • {r['date']}: {r['total']:.2f} TL" for r in monthly_revenue[:5]]) if monthly_revenue else "  • Veri yok"
            
            return {
                'total_users': total_users[0]['count'] if total_users else 0,
                'active_users': active_users[0]['count'] if active_users else 0,
                'today_conversions': today_conversions[0]['count'] if today_conversions else 0,
                'today_analysis': today_analysis[0]['count'] if today_analysis else 0,
                'today_naming': today_naming[0]['count'] if today_naming else 0,
                'today_classification': today_classification[0]['count'] if today_classification else 0,
                'today_summaries': today_summaries[0]['count'] if today_summaries else 0,
                'today_validations': today_validations[0]['count'] if today_validations else 0,
                'today_quality': today_quality[0]['count'] if today_quality else 0,
                'success_total': success_total[0]['count'] if success_total else 0,
                'failed_total': failed_total[0]['count'] if failed_total else 0,
                'total_success': total_success[0]['sum'] or 0 if total_success else 0,
                'total_failed': total_failed[0]['sum'] or 0 if total_failed else 0,
                'total_analysis': total_analysis[0]['sum'] or 0 if total_analysis else 0,
                'total_naming': total_naming[0]['sum'] or 0 if total_naming else 0,
                'total_classification': total_classification[0]['sum'] or 0 if total_classification else 0,
                'total_summaries': total_summaries[0]['sum'] or 0 if total_summaries else 0,
                'total_validations': total_validations[0]['sum'] or 0 if total_validations else 0,
                'total_quality': total_quality[0]['sum'] or 0 if total_quality else 0,
                'total_premium': total_premium[0]['sum'] or 0 if total_premium else 0,
                'total_revenue': total_revenue[0]['sum'] or 0 if total_revenue else 0,
                'top_formats': format_text,
                'top_quality': quality_text,
                'weekly_stats': weekly_text,
                'revenue_stats': revenue_text
            }
        except Exception as e:
            logger.error(f"❌ Admin istatistikleri alınırken hata: {e}")
            return None
    
    def get_package_history(self, user_id: int) -> List[Dict]:
        """Kullanıcının paket geçmişini getir"""
        try:
            return self.execute_query('''
                SELECT * FROM package_history 
                WHERE user_id = ? 
                ORDER BY purchased_at DESC
            ''', (user_id,))
        except Exception as e:
            logger.error(f"❌ Paket geçmişi alınırken hata: {e}")
            return []
    
    def get_pending_payments(self) -> List[Dict]:
        """Bekleyen ödemeleri getir"""
        try:
            return self.execute_query('''
                SELECT * FROM pending_payments 
                WHERE status = 'pending' 
                ORDER BY requested_at DESC
            ''')
        except Exception as e:
            logger.error(f"❌ Bekleyen ödemeler alınırken hata: {e}")
            return []
    
    def get_user_conversions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Kullanıcının son dönüşümlerini getir"""
        try:
            return self.execute_query('''
                SELECT * FROM conversions 
                WHERE user_id = ? 
                ORDER BY converted_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        except Exception as e:
            logger.error(f"❌ Kullanıcı dönüşümleri alınırken hata: {e}")
            return []
    
    def get_user_analysis(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Kullanıcının son analizlerini getir"""
        try:
            return self.execute_query('''
                SELECT * FROM analysis_records 
                WHERE user_id = ? 
                ORDER BY analyzed_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        except Exception as e:
            logger.error(f"❌ Kullanıcı analizleri alınırken hata: {e}")
            return []
    
    def get_user_quality_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Kullanıcının kalite optimizasyonu kayıtlarını getir"""
        try:
            return self.execute_query('''
                SELECT * FROM quality_records 
                WHERE user_id = ? 
                ORDER BY optimized_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        except Exception as e:
            logger.error(f"❌ Kullanıcı kalite kayıtları alınırken hata: {e}")
            return []
    
    def reset_user_stats(self, user_id: int) -> bool:
        """Kullanıcı istatistiklerini sıfırla (admin için)"""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = '''
                UPDATE users SET 
                    total_conversions = 0,
                    successful_conversions = 0,
                    failed_conversions = 0,
                    total_analysis = 0,
                    total_smart_edits = 0,
                    total_naming = 0,
                    total_classification = 0,
                    total_summaries = 0,
                    total_validations = 0,
                    total_quality_optimizations = 0,
                    total_premium_conversions = 0,
                    updated_at = ?
                WHERE user_id = ?
            '''
            self.execute_query(query, (now, user_id))
            logger.info(f"🔄 Kullanıcı {user_id} istatistikleri sıfırlandı")
            return True
        except Exception as e:
            logger.error(f"❌ İstatistik sıfırlama hatası: {e}")
            return False
    
    def backup_database(self, backup_path: str = None):
        """Veritabanı yedeği al"""
        try:
            if not backup_path:
                backup_path = f"database/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"💾 Veritabanı yedeği alındı: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Yedekleme hatası: {e}")
            return None


# ========== GLOBAL ERİŞİM NOKTALARI ==========
_db_manager = None

def get_db() -> DatabaseManager:
    """Singleton DatabaseManager instance'ı döndür"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# Kolaylık fonksiyonları (geriye uyumluluk için)
def init_database():
    """Veritabanını oluştur (geriye uyumluluk)"""
    db = get_db()
    db.create_tables()
    db.upgrade_database()

def register_user(user):
    """Kullanıcı kaydet (geriye uyumluluk)"""
    return get_db().register_user(user)

def get_remaining_rights(user_id):
    """Kalan hak (geriye uyumluluk)"""
    return get_db().get_remaining_rights(user_id)

def decrease_rights(user_id, conversion_type='direct', quality_level='standard'):
    """Hak azalt (geriye uyumluluk)"""
    return get_db().decrease_rights(user_id, conversion_type, quality_level)

def increase_analysis_count(user_id):
    """Analiz sayısı artır (1 hak tüketir)"""
    return get_db().increase_analysis_count(user_id)

def increase_naming_count(user_id):
    """İsimlendirme sayısı artır (1 hak tüketir)"""
    return get_db().increase_naming_count(user_id)

def increase_classification_count(user_id):
    """Sınıflandırma sayısı artır (1 hak tüketir)"""
    return get_db().increase_classification_count(user_id)

def increase_summary_count(user_id):
    """Özetleme sayısı artır (1 hak tüketir)"""
    return get_db().increase_summary_count(user_id)

def increase_validation_count(user_id):
    """Doğrulama sayısı artır (1 hak tüketir)"""
    return get_db().increase_validation_count(user_id)

def increase_quality_count(user_id):
    """Kalite optimizasyonu sayısı artır (1 hak tüketir)"""
    return get_db().increase_quality_count(user_id)

def increase_failed_count(user_id):
    """Başarısız sayısı artır (geriye uyumluluk)"""
    return get_db().increase_failed_count(user_id)

def save_conversion_record(user_id, file_name, file_size, source_format, target_format, 
                          status, processing_time, conversion_type='direct', 
                          quality_level='standard', quality_score=0, error_message=None):
    """Dönüşüm kaydet (geriye uyumluluk)"""
    return get_db().save_conversion_record(user_id, file_name, file_size, source_format, 
                                          target_format, status, processing_time, 
                                          conversion_type, quality_level, quality_score, error_message)

def save_analysis_record(user_id, file_name, file_type, decision, confidence, 
                        structure_score, readability_score, issues):
    """Analiz kaydet"""
    return get_db().save_analysis_record(user_id, file_name, file_type, decision, confidence,
                                        structure_score, readability_score, issues)

def save_naming_record(user_id, original_name, new_name, extracted_info, confidence):
    """İsimlendirme kaydet"""
    return get_db().save_naming_record(user_id, original_name, new_name, extracted_info, confidence)

def save_classification_record(user_id, file_name, document_type, category, confidence,
                              allowed_formats, extracted_fields):
    """Sınıflandırma kaydet"""
    return get_db().save_classification_record(user_id, file_name, document_type, category,
                                              confidence, allowed_formats, extracted_fields)

def save_summary_record(user_id, file_name, summary, key_points, word_count, confidence):
    """Özetleme kaydet"""
    return get_db().save_summary_record(user_id, file_name, summary, key_points, word_count, confidence)

def save_validation_record(user_id, file_name, is_valid, issues, warnings_count,
                          errors_count, critical_count, score):
    """Doğrulama kaydet"""
    return get_db().save_validation_record(user_id, file_name, is_valid, issues, warnings_count,
                                          errors_count, critical_count, score)

def save_quality_record(user_id, file_name, original_score, optimized_score, 
                       quality_level, optimizations, processing_time):
    """Kalite optimizasyonu kaydet"""
    return get_db().save_quality_record(user_id, file_name, original_score, optimized_score,
                                       quality_level, optimizations, processing_time)

def get_user_stats(user_id):
    """Kullanıcı istatistikleri (geriye uyumluluk)"""
    return get_db().get_user_stats(user_id)

def get_admin_stats():
    """Admin istatistikleri (geriye uyumluluk)"""
    return get_db().get_admin_stats()

def log_user_activity(user_id, activity_type, details=""):
    """Aktivite kaydet (geriye uyumluluk)"""
    return get_db().log_user_activity(user_id, activity_type, details)

def add_rights(user_id, rights_to_add, package_id=None, amount=0):
    """Hak ekle (geriye uyumluluk)"""
    return get_db().add_rights(user_id, rights_to_add, package_id, amount)

def add_package_history(user_id, package_type, rights_added, amount=0):
    """Paket geçmişi ekle"""
    return get_db().add_package_history(user_id, package_type, rights_added, amount)

def get_package_history(user_id):
    """Paket geçmişi getir"""
    return get_db().get_package_history(user_id)

def get_user_conversions(user_id, limit=10):
    """Kullanıcı dönüşümleri getir"""
    return get_db().get_user_conversions(user_id, limit)

def get_user_analysis(user_id, limit=10):
    """Kullanıcı analizleri getir"""
    return get_db().get_user_analysis(user_id, limit)

def get_user_quality_records(user_id, limit=10):
    """Kullanıcı kalite kayıtları getir"""
    return get_db().get_user_quality_records(user_id, limit)

def get_daily_stats(days=7):
    """Günlük istatistikleri getir"""
    return get_db().get_daily_stats(days)

def reset_user_stats(user_id):
    """Kullanıcı istatistiklerini sıfırla"""
    return get_db().reset_user_stats(user_id)


# ========== TEST FONKSİYONU ==========
if __name__ == "__main__":
    print("🔧 Veritabanı test ediliyor...")
    print("=" * 60)
    
    db = get_db()
    db.create_tables()
    db.upgrade_database()
    
    print("✅ Veritabanı hazır!")
    print("📊 Yeni işlem tipleri:")
    print("  • Naming (İsimlendirme)")
    print("  • Classification (Sınıflandırma)")
    print("  • Summary (Özetleme)")
    print("  • Validation (Doğrulama)")
    print("  • Quality (Kalite Optimizasyonu)")
    print("  • Premium Dönüşümler")
    print("  • Daily Stats (Günlük İstatistikler)")
    print("=" * 60)
    
    stats = db.get_admin_stats()
    if stats:
        print(f"📊 Admin istatistikleri:")
        print(f"  • Toplam Kullanıcı: {stats['total_users']}")
        print(f"  • Aktif Kullanıcı: {stats['active_users']}")
        print(f"  • Toplam Gelir: {stats['total_revenue']:.2f} TL")
        print(f"  • Başarılı: {stats['success_total']}")
        print(f"  • Başarısız: {stats['failed_total']}")
        print(f"  • Premium: {stats['total_premium']}")