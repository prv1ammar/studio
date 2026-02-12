from typing import Dict, Optional
from app.core.config import settings

class TierManager:
    """
    Tier-based subscription management.
    Defines limits and features for each subscription tier.
    """
    
    # Tier definitions with limits
    TIERS = {
        "free": {
            "name": "Free",
            "price": 0,
            "limits": {
                "max_concurrent_jobs": 2,
                "max_workflows": 5,
                "max_executions_per_day": 50,
                "max_nodes_per_workflow": 10,
                "cache_enabled": True,
                "analytics_retention_days": 7,
                "webhook_endpoints": 1,
                "api_rate_limit": 100,  # requests per hour
            },
            "features": [
                "Basic workflow automation",
                "Community support",
                "7-day analytics retention"
            ]
        },
        "pro": {
            "name": "Pro",
            "price": 29,  # USD per month
            "limits": {
                "max_concurrent_jobs": 10,
                "max_workflows": 50,
                "max_executions_per_day": 1000,
                "max_nodes_per_workflow": 50,
                "cache_enabled": True,
                "analytics_retention_days": 30,
                "webhook_endpoints": 10,
                "api_rate_limit": 1000,
            },
            "features": [
                "Advanced workflow automation",
                "Priority support",
                "30-day analytics retention",
                "Custom integrations",
                "Webhook support"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 299,  # USD per month
            "limits": {
                "max_concurrent_jobs": -1,  # unlimited
                "max_workflows": -1,
                "max_executions_per_day": -1,
                "max_nodes_per_workflow": -1,
                "cache_enabled": True,
                "analytics_retention_days": 365,
                "webhook_endpoints": -1,
                "api_rate_limit": -1,
            },
            "features": [
                "Unlimited workflows",
                "Unlimited executions",
                "24/7 dedicated support",
                "365-day analytics retention",
                "Custom SLA",
                "SSO integration",
                "Multi-region deployment",
                "Priority processing"
            ]
        }
    }
    
    @classmethod
    def get_tier_info(cls, tier: str) -> Dict:
        """Get tier information and limits."""
        return cls.TIERS.get(tier, cls.TIERS["free"])
    
    @classmethod
    def get_limit(cls, tier: str, limit_name: str) -> int:
        """Get a specific limit for a tier."""
        tier_info = cls.get_tier_info(tier)
        return tier_info["limits"].get(limit_name, 0)
    
    @classmethod
    def check_limit(cls, tier: str, limit_name: str, current_value: int) -> tuple[bool, Optional[str]]:
        """
        Check if current value is within tier limits.
        Returns (allowed, reason_if_not_allowed)
        """
        limit = cls.get_limit(tier, limit_name)
        
        # -1 means unlimited
        if limit == -1:
            return True, None
        
        if current_value >= limit:
            tier_info = cls.get_tier_info(tier)
            return False, f"Tier limit reached: {limit_name} ({current_value}/{limit}). Upgrade to {cls._suggest_upgrade(tier)} for higher limits."
        
        return True, None
    
    @classmethod
    def _suggest_upgrade(cls, current_tier: str) -> str:
        """Suggest next tier for upgrade."""
        if current_tier == "free":
            return "Pro"
        elif current_tier == "pro":
            return "Enterprise"
        return "Enterprise"
    
    @classmethod
    def get_concurrent_job_limit(cls, tier: str, custom_limits: Optional[Dict] = None) -> int:
        """
        Get concurrent job limit for a tier.
        Supports custom limits override.
        """
        if custom_limits and "max_concurrent_jobs" in custom_limits:
            return custom_limits["max_concurrent_jobs"]
        
        return cls.get_limit(tier, "max_concurrent_jobs")
    
    @classmethod
    def compare_tiers(cls) -> Dict:
        """Get comparison table of all tiers."""
        comparison = {
            "tiers": [],
            "features": []
        }
        
        for tier_key, tier_data in cls.TIERS.items():
            comparison["tiers"].append({
                "key": tier_key,
                "name": tier_data["name"],
                "price": tier_data["price"],
                "limits": tier_data["limits"],
                "features": tier_data["features"]
            })
        
        return comparison

tier_manager = TierManager()
