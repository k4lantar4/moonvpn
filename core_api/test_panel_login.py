import asyncio
import sys
import os

# Add project root to path to find modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.panel_client import PanelClient, PanelClientError

async def main():
    # Get credentials from environment variables passed by docker-compose run
    base_url = os.getenv('PANEL_BASE_URL')
    username = os.getenv('PANEL_USERNAME')
    password = os.getenv('PANEL_PASSWORD')

    if not all([base_url, username, password]):
        print("Error: PANEL_BASE_URL, PANEL_USERNAME, and PANEL_PASSWORD environment variables must be set.")
        return

    client = PanelClient(base_url=base_url, username=username, password=password)
    cookie = None
    try:
        print('--- Testing Panel Login ---')
        print(f"URL: {base_url}, User: {username}")
        cookie = await client._login()
        print(f'Login Result Cookie: {cookie}')
        # You could add another test call here that requires the cookie
        # e.g., await client.get_some_data()
    except PanelClientError as e:
        print(f'Panel Client Error: {e}')
    except Exception as e:
        print(f'Unexpected Error during test: {e}')
    finally:
        if client:
            await client.close()
        print('--- Test Finished ---')

if __name__ == "__main__":
    # Use asyncio.run() for cleaner execution
    asyncio.run(main()) 