import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'roads_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'roadsdb2024secure')
}

# Connection string
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv('DB_POOL_MIN', 10)),
    max_overflow=int(os.getenv('DB_POOL_MAX', 50)),
    pool_pre_ping=True,
    echo=False
)

def get_db_connection():
    """Get a database connection using psycopg2"""
    return psycopg2.connect(**DB_CONFIG)

def get_db_cursor():
    """Get a database cursor with RealDictCursor for dict-like results"""
    conn = get_db_connection()
    return conn, conn.cursor(cursor_factory=RealDictCursor)

def execute_query(query, params=None, fetch_one=False):
    """Execute a query and return results"""
    conn = None
    try:
        conn, cursor = get_db_cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
            return cursor.rowcount
        else:
            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.execute("SELECT PostGIS_version();")
        postgis_version = cursor.fetchone()
        conn.close()
        return {
            'status': 'connected',
            'postgres_version': version[0],
            'postgis_version': postgis_version[0]
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

if __name__ == "__main__":
    # Test the connection
    result = test_connection()
    print("Database connection test:")
    print(f"Status: {result['status']}")
    if result['status'] == 'connected':
        print(f"PostgreSQL: {result['postgres_version']}")
        print(f"PostGIS: {result['postgis_version']}")
    else:
        print(f"Error: {result['error']}")