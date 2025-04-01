import os
import sys
import asyncio

async def main():
    base_url = os.getenv("PANEL_BASE_URL")
    username = os.getenv("PANEL_USERNAME")
    password = os.getenv("PANEL_PASSWORD")

    if not all([base_url, username, password]):
        print("Error: PANEL_BASE_URL, PANEL_USERNAME, and PANEL_PASSWORD must be set in environment variables.")
        sys.exit(1)

    panel = PanelClient(base_url, username, password)
    try:
        print("Attempting login...")
        await panel.login()
        print("Login successful!")

        # --- Test Get Inbounds --- >
        print("\nDEBUG: About to call get_inbounds...")
        inbounds = await panel.get_inbounds()
        print("\nDEBUG: Call to get_inbounds finished.")

        if inbounds:
            print(f"Successfully retrieved {len(inbounds)} inbounds:")
            for inbound in inbounds:
                # Print key details - adjust fields based on actual response
                print(f"  - ID: {inbound.get('id')}, Remark: {inbound.get('remark')}, Port: {inbound.get('port')}, Protocol: {inbound.get('protocol')}")

            # --- Test Add Client to First Inbound --- >
            # first_inbound_id = inbounds[0].get('id')
            # if first_inbound_id:
            #     print(f"\nAttempting to add a client to inbound ID: {first_inbound_id}...")
            #     client_remark = "Test Client 1"
            #     client_gb = 1 # 1 GB limit
            #     client_expiry = 0 # No expiry
            #
            #     add_result = await panel.add_client_to_inbound(
            #         inbound_id=first_inbound_id,
            #         remark=client_remark,
            #         total_gb=client_gb,
            #         expire_time=client_expiry
            #     )
            #
            #     if add_result:
            #         print(f"Successfully added client '{client_remark}' to inbound {first_inbound_id}. Response: {add_result}")
            #     else:
            #         print(f"Failed to add client '{client_remark}' to inbound {first_inbound_id}.")
            # else:
            #     print("Could not get ID from the first inbound to test adding a client.")
            # <--- End Add Client Test ---

        else:
            print("Failed to retrieve inbounds or no inbounds found.")
        # <--- End Get Inbounds Test ---

    except PanelClientError as e:
        print(f"Panel client error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # await panel.close() # <-- Temporarily comment out for debugging
        print("\nTest finished.")

if __name__ == "__main__":
    # Add project root to sys.path for module discovery
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Now import after adjusting path
    from app.utils.panel_client import PanelClient, PanelClientError

    print(f"Running test script in: {os.getcwd()}")
    print(f"Project root added to path: {project_root}")
    print(f"Attempting to import PanelClient from: app.utils.panel_client")

    # asyncio.run(main())
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        # Optionally close the loop if necessary, though often not needed for run_until_complete
        # loop.close()
        pass 