"""Test database connection."""
import psycopg2
import traceback

try:
    # Try with 127.0.0.1 instead of localhost (Windows IPv6 issue)
    dsn = "postgresql://agent_system:dev_password@127.0.0.1:5432/research_collective"
    print(f'Connecting with DSN: {dsn}')
    conn = psycopg2.connect(dsn)
    print('✓ Connected to PostgreSQL successfully!')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'PostgreSQL version: {version[0]}')
    cursor.close()
    conn.close()
except Exception as e:
    print('✗ Connection failed!')
    traceback.print_exc()
    print(f'\nError details: {str(e)}')
    print(f'Error type: {type(e).__name__}')
    print(f'Error args: {e.args}')
