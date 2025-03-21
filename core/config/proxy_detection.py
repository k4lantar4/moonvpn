"""
Proxy detection service for identifying and handling proxy/VPN connections.
"""
from typing import Dict, Optional
import aiohttp
from fastapi import Request

from ..core.config.security_config import security_settings

class ProxyDetectionService:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.api_key = security_settings.PROXY_CHECK_API_KEY

    async def check_ip(self, ip: str) -> Dict:
        """Check if an IP is a proxy/VPN using external API."""
        # Check cache first
        if ip in self.cache:
            return self.cache[ip]

        try:
            async with aiohttp.ClientSession() as session:
                # Using proxycheck.io API as an example
                # You can replace this with any proxy detection service
                url = f"https://proxycheck.io/v2/{ip}?key={self.api_key}&vpn=1"
                async with session.get(url) as response:
                    data = await response.json()
                    
                    result = {
                        "is_proxy": data.get(ip, {}).get("proxy", "no") == "yes",
                        "is_vpn": data.get(ip, {}).get("type", "") == "VPN",
                        "country": data.get(ip, {}).get("country", ""),
                        "provider": data.get(ip, {}).get("provider", ""),
                        "risk": data.get(ip, {}).get("risk", 0)
                    }

                    # Cache the result
                    self.cache[ip] = result
                    return result

        except Exception as e:
            print(f"Proxy detection failed: {e}")
            return {
                "is_proxy": False,
                "is_vpn": False,
                "country": "",
                "provider": "",
                "risk": 0
            }

    def extract_real_ip(self, request: Request) -> str:
        """Extract real IP address from request headers."""
        # Check X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to remote address
        return request.client.host

    def get_proxy_headers(self, request: Request) -> Dict[str, Optional[str]]:
        """Get proxy-related headers from request."""
        return {
            "x_forwarded_for": request.headers.get("X-Forwarded-For"),
            "x_forwarded_proto": request.headers.get("X-Forwarded-Proto"),
            "x_forwarded_host": request.headers.get("X-Forwarded-Host"),
            "x_real_ip": request.headers.get("X-Real-IP"),
            "via": request.headers.get("Via"),
            "forwarded": request.headers.get("Forwarded")
        }

    def analyze_headers(self, headers: Dict[str, Optional[str]]) -> Dict:
        """Analyze proxy-related headers for suspicious patterns."""
        analysis = {
            "proxy_indicators": 0,
            "suspicious_patterns": [],
            "risk_level": "low"
        }

        # Check for presence of proxy headers
        if headers["x_forwarded_for"]:
            analysis["proxy_indicators"] += 1
            # Check for multiple IPs in chain
            if "," in headers["x_forwarded_for"]:
                analysis["suspicious_patterns"].append("multiple_ips_in_chain")
                analysis["proxy_indicators"] += 1

        if headers["via"]:
            analysis["proxy_indicators"] += 1
            analysis["suspicious_patterns"].append("via_header_present")

        if headers["forwarded"]:
            analysis["proxy_indicators"] += 1
            analysis["suspicious_patterns"].append("forwarded_header_present")

        # Determine risk level
        if analysis["proxy_indicators"] >= 3:
            analysis["risk_level"] = "high"
        elif analysis["proxy_indicators"] >= 2:
            analysis["risk_level"] = "medium"

        return analysis

    async def is_suspicious(self, request: Request) -> Dict:
        """
        Comprehensive check for suspicious proxy/VPN usage.
        Returns a dictionary with analysis results.
        """
        ip = self.extract_real_ip(request)
        headers = self.get_proxy_headers(request)
        header_analysis = self.analyze_headers(headers)
        ip_check = await self.check_ip(ip)

        result = {
            "is_suspicious": False,
            "risk_level": "low",
            "reasons": [],
            "details": {
                "ip": ip,
                "header_analysis": header_analysis,
                "ip_check": ip_check
            }
        }

        # Evaluate header analysis
        if header_analysis["risk_level"] in ["medium", "high"]:
            result["is_suspicious"] = True
            result["reasons"].append("suspicious_headers")

        # Evaluate IP check results
        if ip_check["is_proxy"] or ip_check["is_vpn"]:
            result["is_suspicious"] = True
            result["reasons"].append(
                "proxy_ip" if ip_check["is_proxy"] else "vpn_ip"
            )

        # Set overall risk level
        if header_analysis["risk_level"] == "high" or ip_check["risk"] > 75:
            result["risk_level"] = "high"
        elif header_analysis["risk_level"] == "medium" or ip_check["risk"] > 50:
            result["risk_level"] = "medium"

        return result 