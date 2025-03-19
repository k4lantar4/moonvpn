"""
3x-UI Protocol Package
"""

from vpn.base import VPNProtocolRegistry
from vpn.protocols.threexui.protocols.vmess import VMessProtocol
from vpn.protocols.threexui.protocols.vless import VLESSProtocol
from vpn.protocols.threexui.protocols.trojan import TrojanProtocol

# Register protocols
VPNProtocolRegistry.register("vmess", VMessProtocol)
VPNProtocolRegistry.register("vless", VLESSProtocol)
VPNProtocolRegistry.register("trojan", TrojanProtocol) 