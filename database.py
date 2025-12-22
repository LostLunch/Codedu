import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

DATABASE_NAME = "codedu.db"

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn

def init_database():
    """데이터베이스 테이블을 초기화합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 사용자 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            level TEXT DEFAULT '초급',
            learning_language TEXT DEFAULT 'Python',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # 기존 테이블에 learning_language 컬럼 추가 (이미 존재하면 무시)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN learning_language TEXT DEFAULT 'Python'")
        conn.commit()
    except sqlite3.OperationalError:
        # 컬럼이 이미 존재하는 경우 무시
        pass
    
    # 학습 상태 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language TEXT DEFAULT 'Python',
            chapter TEXT,
            completed BOOLEAN DEFAULT 0,
            score INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # 기존 테이블에 language 컬럼 추가 (이미 존재하면 무시)
    try:
        cursor.execute("ALTER TABLE learning_progress ADD COLUMN language TEXT DEFAULT 'Python'")
        conn.commit()
    except sqlite3.OperationalError:
        # 컬럼이 이미 존재하는 경우 무시
        pass
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """비밀번호를 해시화합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str, level: str = "초급") -> tuple[bool, str]:
    """
    새 사용자를 등록합니다.
    Returns: (성공 여부, 메시지)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 사용자명 중복 확인
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "이미 존재하는 아이디입니다."
        
        # 사용자 추가
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, level)
            VALUES (?, ?, ?)
        """, (username, password_hash, level))
        
        conn.commit()
        return True, "회원가입이 완료되었습니다."
    
    except sqlite3.Error as e:
        return False, f"데이터베이스 오류: {str(e)}"
    finally:
        conn.close()

def verify_user(username: str, password: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    사용자 로그인을 확인합니다.
    Returns: (성공 여부, 사용자 정보 딕셔너리 또는 None)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute("""
            SELECT id, username, level, learning_language, created_at
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # 마지막 로그인 시간 업데이트
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'],))
            conn.commit()
            
            return True, {
                'id': user['id'],
                'username': user['username'],
                'level': user['level'],
                'learning_language': user['learning_language'] or 'Python',
                'created_at': user['created_at']
            }
        else:
            return False, None
    
    except sqlite3.Error as e:
        return False, None
    finally:
        conn.close()

def update_user_level(user_id: int, level: str) -> bool:
    """사용자의 학습 수준을 업데이트합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users SET level = ?
            WHERE id = ?
        """, (level, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def update_user_language(user_id: int, language: str) -> bool:
    """사용자의 학습 언어를 업데이트합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users SET learning_language = ?
            WHERE id = ?
        """, (language, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_user_language(user_id: int) -> Optional[str]:
    """사용자의 학습 언어를 조회합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT learning_language FROM users WHERE id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result['learning_language'] if result and result['learning_language'] else 'Python'
    except sqlite3.Error:
        return 'Python'
    finally:
        conn.close()

def save_learning_progress(user_id: int, chapter: str, language: str, completed: bool = False, score: int = 0) -> bool:
    """학습 진행 상태를 저장합니다. (언어별로 관리)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 기존 진행 상태 확인 (언어와 챕터로 확인)
        cursor.execute("""
            SELECT id FROM learning_progress
            WHERE user_id = ? AND chapter = ? AND language = ?
        """, (user_id, chapter, language))
        
        existing = cursor.fetchone()
        
        if existing:
            # 업데이트
            cursor.execute("""
                UPDATE learning_progress
                SET completed = ?, score = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (completed, score, existing['id']))
        else:
            # 새로 추가
            cursor.execute("""
                INSERT INTO learning_progress (user_id, language, chapter, completed, score)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, language, chapter, completed, score))
        
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def get_learning_progress(user_id: int, language: Optional[str] = None) -> list[Dict[str, Any]]:
    """사용자의 학습 진행 상태를 조회합니다. (언어별 필터링 가능)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if language:
            cursor.execute("""
                SELECT language, chapter, completed, score, last_accessed
                FROM learning_progress
                WHERE user_id = ? AND language = ?
                ORDER BY last_accessed DESC
            """, (user_id, language))
        else:
            cursor.execute("""
                SELECT language, chapter, completed, score, last_accessed
                FROM learning_progress
                WHERE user_id = ?
                ORDER BY language, last_accessed DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error:
        return []
    finally:
        conn.close()

def get_user_stats(user_id: int, language: Optional[str] = None) -> Dict[str, Any]:
    """사용자의 통계 정보를 반환합니다. (언어별 필터링 가능)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if language:
            # 특정 언어의 통계
            cursor.execute("""
                SELECT COUNT(*) as completed_count
                FROM learning_progress
                WHERE user_id = ? AND language = ? AND completed = 1
            """, (user_id, language))
            completed = cursor.fetchone()['completed_count']
            
            cursor.execute("""
                SELECT COUNT(*) as total_count
                FROM learning_progress
                WHERE user_id = ? AND language = ?
            """, (user_id, language))
            total = cursor.fetchone()['total_count']
            
            cursor.execute("""
                SELECT AVG(score) as avg_score
                FROM learning_progress
                WHERE user_id = ? AND language = ?
            """, (user_id, language))
            avg_score = cursor.fetchone()['avg_score'] or 0
        else:
            # 전체 통계
            cursor.execute("""
                SELECT COUNT(*) as completed_count
                FROM learning_progress
                WHERE user_id = ? AND completed = 1
            """, (user_id,))
            completed = cursor.fetchone()['completed_count']
            
            cursor.execute("""
                SELECT COUNT(*) as total_count
                FROM learning_progress
                WHERE user_id = ?
            """, (user_id,))
            total = cursor.fetchone()['total_count']
            
            cursor.execute("""
                SELECT AVG(score) as avg_score
                FROM learning_progress
                WHERE user_id = ?
            """, (user_id,))
            avg_score = cursor.fetchone()['avg_score'] or 0
        
        return {
            'completed_chapters': completed,
            'total_chapters': total,
            'average_score': round(avg_score, 2)
        }
    except sqlite3.Error:
        return {
            'completed_chapters': 0,
            'total_chapters': 0,
            'average_score': 0
        }
    finally:
        conn.close()

# 데이터베이스 초기화 (모듈이 로드될 때 실행)
init_database()

