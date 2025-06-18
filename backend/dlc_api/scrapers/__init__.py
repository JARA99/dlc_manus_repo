"""
Scrapers package initialization
"""

from .cemaco import CemacoScraper
from .placeholders import MaxScraper, ElektraScraper, WalmartScraper

# Available scrapers
SCRAPERS = {
    "cemaco": CemacoScraper,
    "max": MaxScraper,
    "elektra": ElektraScraper,
    "walmart": WalmartScraper,
}

__all__ = ["CemacoScraper", "MaxScraper", "ElektraScraper", "WalmartScraper", "SCRAPERS"]

