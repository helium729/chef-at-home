"""
Base configuration for Playwright E2E tests
"""

import os
import sys

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check for Playwright availability
PLAYWRIGHT_AVAILABLE = False
try:
    import playwright
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Browser = BrowserContext = Page = Playwright = None


class E2ETestBase:
    """Base class for E2E tests providing common setup and utilities"""

    @property
    def base_url(self) -> str:
        """Get base URL for testing"""
        return os.getenv("E2E_BASE_URL", "http://localhost:8000")


# Configure pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "pwa: mark test as PWA functionality test")
    config.addinivalue_line("markers", "workflow: mark test as user workflow test")


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests if Playwright is not available"""
    if not PLAYWRIGHT_AVAILABLE:
        skip_e2e = pytest.mark.skip(reason="Playwright not available")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
