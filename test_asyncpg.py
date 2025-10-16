"""Test asyncpg connection."""
import asyncio
import asyncpg
import sys

# On Windows, use the selector event loop instead of proactor
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def test_connection():
    try:
        # Disable SSL for local Docker connections
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5433,
            database='research_collective',
            user='agent_system',
            password='dev_password',
            ssl=False,
            server_settings={'jit': 'off'}
        )
        print('✓ Connected to PostgreSQL with asyncpg!')
        version = await conn.fetchval('SELECT version()')
        print(f'PostgreSQL version: {version}')
        await conn.close()
    except Exception as e:
        print('✗ Connection failed!')
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_connection())
