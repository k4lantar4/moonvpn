"""
Utilities for generating VPN configuration links based on panel and inbound settings.
"""

import logging
import json
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlencode

# Assuming models are accessible, adjust path if necessary
from db.models.panel import Panel
from db.models.inbound import Inbound

logger = logging.getLogger(__name__)

class ConfigGenerationError(Exception):
     """Custom exception for configuration generation errors."""
     pass

def generate_config_link(panel: Panel, inbound: Inbound, client_uuid: str, client_email: str) -> Optional[str]:
    """
    Generates the VLESS/VMess config URL based on panel and inbound details.

    Args:
        panel: The Panel object containing connection details (URL).
        inbound: The Inbound object containing protocol, port, and settings.
        client_uuid: The UUID of the client.
        client_email: The email of the client (used as remark).

    Returns:
        The generated configuration link as a string, or None if generation fails or protocol is unsupported.
        
    Raises:
        ConfigGenerationError: If a critical error occurs during generation.
    """
    log_prefix = f"[ConfigGen Panel: {panel.id}, Inbound: {inbound.remote_id}, Client: {client_uuid}]"
    logger.info(f"{log_prefix} Generating config URL.")
    
    try:
        # Required basic info
        protocol = inbound.protocol.lower() # Ensure lowercase for comparison
        if not protocol:
             logger.error(f"{log_prefix} Inbound protocol is missing.")
             return None
             
        address = urlparse(panel.url).hostname or panel.url # Use hostname, fallback to full URL
        port = inbound.port
        if not port:
             logger.error(f"{log_prefix} Inbound port is missing.")
             return None
             
        remark = client_email # Use email as remark
        
        # Settings from the DbInbound model (which should mirror SDK structure)
        stream_settings = inbound.stream_settings or {}
        sniffing_settings = inbound.sniffing or {}
        inbound_settings = inbound.settings_json or {} # VLESS/VMess/Trojan specific settings

        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "none")
        config_link = ""

        # --- VLESS --- 
        if protocol == "vless":
            base_link = f"vless://{client_uuid}@{address}:{port}"
            params: Dict[str, Any] = {"type": network, "security": security}
            
            # Network specific settings
            if network == "tcp":
                tcp_settings = stream_settings.get("tcpSettings", {})
                header = tcp_settings.get("header", {})
                if header.get("type") == "http":
                    params["headerType"] = "http"
                    req = header.get("request", {})
                    # Ensure path starts with /
                    path_list = req.get("path", ["/"])
                    path = path_list[0] if path_list and path_list[0].startswith("/") else "/" + path_list[0] if path_list else "/"
                    params["path"] = path
                    host_headers = req.get("headers", {}).get("Host", [])
                    host = host_headers[0] if host_headers else ""
                    if host: params["host"] = host
            elif network == "ws":
                ws_settings = stream_settings.get("wsSettings", {})
                path = ws_settings.get("path", "/")
                params["path"] = path if path.startswith("/") else "/" + path
                host = ws_settings.get("headers", {}).get("Host", "")
                if host: params["host"] = host
            elif network == "grpc":
                grpc_settings = stream_settings.get("grpcSettings", {})
                params["serviceName"] = grpc_settings.get("serviceName", "")
                # VLESS grpc link uses 'mode' (multi/gun), default seems to be gun
                params["mode"] = "multi" if grpc_settings.get("multiMode", False) else "gun"

            # Security specific settings
            if security == "tls":
                tls_settings = stream_settings.get("tlsSettings", {})
                params["sni"] = tls_settings.get("serverName") or tls_settings.get("sni") or address # Use serverName or sni if available
                params["fp"] = tls_settings.get("fingerprint", "")
                alpn_list = tls_settings.get("alpn", [])
                params["alpn"] = ",".join(alpn_list) if alpn_list else None # Comma separated
            elif security == "reality":
                reality_settings = stream_settings.get("realitySettings", {})
                # REALITY settings might be nested under 'settings' key in some panel versions
                inner_reality_settings = reality_settings.get("settings", reality_settings) 
                params["sni"] = reality_settings.get("serverNames", [address])[0]
                params["fp"] = inner_reality_settings.get("fingerprint", "chrome") # Default fingerprint
                params["pbk"] = inner_reality_settings.get("publicKey", "")
                params["sid"] = inner_reality_settings.get("shortIds", [""])[0]
                params["spx"] = inner_reality_settings.get("spiderX", "")
                # flow is usually part of VLESS itself, typically not in URL but can be added if needed
                vless_flow = inbound_settings.get("flow", "") # Get flow from VLESS settings
                if vless_flow:
                     params["flow"] = vless_flow
                 
            # Flow (check inbound settings first, usually xtls-rprx-vision)
            vless_settings = inbound_settings.get("clients", [{}])[0] # VLESS client settings are often in a list
            flow = vless_settings.get("flow", "")
            if flow and security in ["tls", "reality"] and "flow" not in params: # Add if not already set by REALITY
                params["flow"] = flow
                
            # Encode params
            query_string = urlencode({k: v for k, v in params.items() if v is not None and v != ""})
            config_link = f"{base_link}?{query_string}#{remark}"

        # --- VMess --- (Based on standard VMess AEAD format)
        elif protocol == "vmess":
             # Extract AlterId from the 'clients' list in settings_json
             vmess_clients = inbound_settings.get("clients", [])
             client_settings = vmess_clients[0] if vmess_clients else {}
             alter_id = client_settings.get("alterId", 0)

             vmess_data: Dict[str, Any] = {
                "v": "2",
                "ps": remark,
                "add": address,
                "port": str(port),
                "id": client_uuid,
                "aid": str(alter_id), 
                "scy": "auto", # Security cipher - auto is common
                "net": network,
                "type": "none", # Default header type
                "host": "",
                "path": "",
                "tls": "",
                "sni": "",
                "alpn": "",
                "fp": ""
             }
             
             # Network settings
             if network == "tcp":
                tcp_settings = stream_settings.get("tcpSettings", {})
                header = tcp_settings.get("header", {})
                if header.get("type") == "http":
                    vmess_data["type"] = "http"
                    req = header.get("request", {})
                    paths = req.get("path", ["/"])
                    vmess_data["path"] = ",".join(paths) if paths else "/" # Comma separated for VMess
                    host_headers = req.get("headers", {}).get("Host", [])
                    vmess_data["host"] = host_headers[0] if host_headers else ""
             elif network == "ws":
                ws_settings = stream_settings.get("wsSettings", {})
                path = ws_settings.get("path", "/")
                vmess_data["path"] = path if path.startswith("/") else "/" + path
                vmess_data["host"] = ws_settings.get("headers", {}).get("Host", "")
             elif network == "grpc":
                 grpc_settings = stream_settings.get("grpcSettings", {})
                 vmess_data["path"] = grpc_settings.get("serviceName", "") # ServiceName acts as path for grpc
                 vmess_data["type"] = "multi" if grpc_settings.get("multiMode", False) else "gun"
                 
             # Security settings
             if security == "tls":
                vmess_data["tls"] = "tls"
                tls_settings = stream_settings.get("tlsSettings", {})
                vmess_data["sni"] = tls_settings.get("serverName") or tls_settings.get("sni") or address
                vmess_data["fp"] = tls_settings.get("fingerprint", "")
                alpn_list = tls_settings.get("alpn", [])
                vmess_data["alpn"] = ",".join(alpn_list) if alpn_list else "" # Comma separated for VMess
             # VMess usually doesn't support REALITY directly in standard links
             
             # Remove empty fields before dumping
             vmess_data_cleaned = {k: v for k, v in vmess_data.items() if v not in [None, ""]}
             
             json_string = json.dumps(vmess_data_cleaned, separators=(',', ':'), sort_keys=True)
             encoded_bytes = base64.urlsafe_b64encode(json_string.encode('utf-8'))
             encoded_string = encoded_bytes.decode('utf-8').rstrip('=')
             config_link = f"vmess://{encoded_string}"
             
        else:
            logger.warning(f"{log_prefix} Unsupported protocol '{protocol}' for config generation.")
            return None
            
        logger.info(f"{log_prefix} Successfully generated config link for protocol {protocol}.")
        return config_link.strip() # Ensure no leading/trailing whitespace
        
    except KeyError as ke:
         logger.error(f"{log_prefix} Missing expected key in inbound settings: {ke}", exc_info=True)
         raise ConfigGenerationError(f"Missing key '{ke}' in settings for {protocol}/{network}/{security}") from ke
    except Exception as e:
         logger.error(f"{log_prefix} Error generating config URL: {e}", exc_info=True)
         # Raise specific error?
         raise ConfigGenerationError(f"Failed to generate config: {e}") from e
         # return None # Return None on error

# Ensure file ends cleanly 