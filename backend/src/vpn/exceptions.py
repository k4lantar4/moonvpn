"""
Exceptions for the VPN module
"""

class VPNError(Exception):
    """Base exception for all VPN-related errors"""
    pass

class VPNConnectionError(VPNError):
    """Error connecting to a VPN server"""
    pass

class VPNAuthenticationError(VPNError):
    """Authentication error with VPN server"""
    pass

class VPNSyncError(VPNError):
    """Error synchronizing data with VPN server"""
    pass

class VPNUserError(VPNError):
    """Error with VPN user operations"""
    pass

class VPNProtocolError(VPNError):
    """Error related to VPN protocols"""
    pass

class VPNServerError(VPNError):
    """Error with the VPN server itself"""
    pass

class VPNConfigError(VPNError):
    """Configuration error for VPN"""
    pass

class VPNTrafficError(VPNError):
    """Error with VPN traffic data"""
    pass

class VPNNotSupportedError(VPNError):
    """Feature not supported by the VPN protocol or server"""
    pass 