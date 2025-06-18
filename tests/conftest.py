"""
Base configuration for Playwright E2E tests
"""

import os

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright


class E2ETestBase:
    """Base class for E2E tests providing common setup and utilities"""

    @pytest.fixture(scope="session")
    def browser(self, playwright: Playwright) -> Browser:
        """Launch browser for testing"""
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        yield browser
        browser.close()

    @pytest.fixture(scope="function")
    def context(self, browser: Browser) -> BrowserContext:
        """Create browser context with mobile-friendly settings"""
        context = browser.new_context(
            viewport={"width": 375, "height": 667},  # iPhone-like viewport
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            device_scale_factor=2,
            has_touch=True,
            is_mobile=True,
        )
        yield context
        context.close()

    @pytest.fixture(scope="function")
    def page(self, context: BrowserContext) -> Page:
        """Create new page for each test"""
        page = context.new_page()
        yield page
        page.close()

    @property
    def base_url(self) -> str:
        """Get base URL for testing"""
        return os.getenv("E2E_BASE_URL", "http://localhost:8000")

    def login(self, page: Page, username: str = "testuser", password: str = "testpass123"):
        """Helper method to log in a user"""
        page.goto(f"{self.base_url}/accounts/login/")
        page.fill('input[name="login"]', username)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        # Wait for redirect after login
        page.wait_for_url(f"{self.base_url}/", timeout=5000)

    def wait_for_api_response(self, page: Page, api_path: str, timeout: int = 5000):
        """Wait for specific API response"""
        with page.expect_response(f"**/api/{api_path}/**", timeout=timeout) as response_info:
            pass
        return response_info.value
