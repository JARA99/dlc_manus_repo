"""
Vendor definitions for all supported stores
"""

from .models import Vendor

# Define all supported vendors
VENDORS = {
    "cemaco": Vendor(
        id="cemaco",
        name="Cemaco",
        base_url="https://www.cemaco.com",
        country="GT",
        currency="GTQ",
        active=True
    ),
    "max": Vendor(
        id="max",
        name="Max",
        base_url="https://www.max.com.gt",
        country="GT", 
        currency="GTQ",
        active=True
    ),
    "elektra": Vendor(
        id="elektra",
        name="Elektra",
        base_url="https://www.elektra.com.gt",
        country="GT",
        currency="GTQ", 
        active=True
    ),
    "walmart": Vendor(
        id="walmart",
        name="Walmart Guatemala",
        base_url="https://www.walmart.com.gt",
        country="GT",
        currency="GTQ",
        active=True
    )
}

def get_vendor(vendor_id: str) -> Vendor:
    """Get vendor by ID."""
    if vendor_id not in VENDORS:
        raise ValueError(f"Unknown vendor: {vendor_id}")
    return VENDORS[vendor_id]

def get_all_vendors() -> dict[str, Vendor]:
    """Get all vendors."""
    return VENDORS.copy()

def get_active_vendors() -> dict[str, Vendor]:
    """Get only active vendors."""
    return {vid: vendor for vid, vendor in VENDORS.items() if vendor.active}

