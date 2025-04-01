import os
import sys
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Test the synchronous panel client functionality.
    """
    # Get environment variables
    base_url = os.getenv("PANEL_BASE_URL")
    username = os.getenv("PANEL_USERNAME")
    password = os.getenv("PANEL_PASSWORD")

    if not all([base_url, username, password]):
        logger.error("Error: PANEL_BASE_URL, PANEL_USERNAME, and PANEL_PASSWORD must be set in environment variables.")
        sys.exit(1)

    logger.info(f"Testing with Panel URL: {base_url}")
    
    # Import after path setup
    from core_api.app.utils.sync_panel_client import SyncPanelClient, PanelClientError
    
    # Create the client and test functionality
    try:
        with SyncPanelClient(base_url, username, password) as panel:
            # Test 1: Login
            logger.info("TEST 1: Attempting login...")
            session_cookie = panel.login()
            logger.info(f"Login successful! Session cookie obtained: {session_cookie[:10]}...")
            
            # Test 2: Get Inbounds
            logger.info("TEST 2: Fetching inbounds...")
            inbounds = panel.get_inbounds()
            if inbounds:
                logger.info(f"Successfully retrieved {len(inbounds)} inbounds:")
                for inbound in inbounds:
                    # Print key details
                    logger.info(f"  - ID: {inbound.get('id')}, "
                               f"Remark: {inbound.get('remark')}, "
                               f"Port: {inbound.get('port')}, "
                               f"Protocol: {inbound.get('protocol')}")
                
                # Test 3: Add Client to the first inbound
                if len(inbounds) > 0:
                    first_inbound_id = inbounds[0].get('id')
                    if first_inbound_id:
                        logger.info(f"TEST 3: Adding client to inbound ID: {first_inbound_id}...")
                        client_remark = "test_sync_client_1"
                        client_gb = 1  # 1 GB limit
                        expire_days = 30  # 30 days expiry
                        
                        client_info = panel.add_client_to_inbound(
                            inbound_id=first_inbound_id,
                            remark=client_remark,
                            total_gb=client_gb,
                            expire_days=expire_days
                        )
                        
                        if isinstance(client_info, dict) and client_info:
                            logger.info(f"Successfully added client to inbound {first_inbound_id}.")
                            logger.info(f"Client details: {client_info}")
                        else:
                            logger.error(f"Failed to add client to inbound {first_inbound_id}.")
                    else:
                        logger.error("Could not get ID from the first inbound to test adding a client.")
            else:
                logger.error("Failed to retrieve inbounds or no inbounds found.")
                
    except PanelClientError as e:
        logger.error(f"Panel client error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Test completed.")

if __name__ == "__main__":
    # Add project root to sys.path for module discovery
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    logger.info(f"Running test script in: {os.getcwd()}")
    logger.info(f"Project root added to path: {project_root}")
    
    main() 