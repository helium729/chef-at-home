"""
E2E tests for core user workflows in FamilyChef application
"""

import pytest
from playwright.sync_api import Page, expect

from .conftest import E2ETestBase


class TestUserWorkflows(E2ETestBase):
    """Test core user workflows end-to-end"""

    def test_menu_browsing_workflow(self, page: Page):
        """Test user can browse available menu items"""
        # Navigate to home page (menu)
        page.goto(self.base_url)

        # Check that the page loads
        expect(page).to_have_title("FamilyChef")

        # Check for menu elements
        expect(page.locator("h1")).to_contain_text("Menu")

        # Check for PWA meta tags
        expect(page.locator('meta[name="theme-color"]')).to_have_attribute("content", "#4CAF50")
        expect(page.locator('link[rel="manifest"]')).to_have_attribute("href", "/manifest.json")

    def test_order_creation_workflow(self, page: Page):
        """Test complete order creation workflow"""
        # This test would require authentication setup
        # For now, just test that the order page is accessible
        page.goto(f"{self.base_url}/")

        # Look for order-related elements
        order_buttons = page.locator('button:has-text("Order")')
        if order_buttons.count() > 0:
            # If there are available items to order
            order_buttons.first.click()

            # Wait for any modal or navigation
            page.wait_for_timeout(1000)

            # Check for order confirmation elements
            expect(page.locator("body")).to_be_visible()

    def test_chef_workflow(self, page: Page):
        """Test chef dashboard and order management"""
        # Navigate to chef page
        page.goto(f"{self.base_url}/chef/")

        # Check chef dashboard loads
        expect(page.locator("h1")).to_contain_text("Chef")

        # Look for order management elements
        orders_section = page.locator('.orders, #orders, [data-testid="orders"]')
        if orders_section.count() > 0:
            expect(orders_section.first).to_be_visible()

    def test_pantry_management_workflow(self, page: Page):
        """Test pantry stock management"""
        # Navigate to pantry page
        page.goto(f"{self.base_url}/pantry/")

        # Check pantry page loads
        expect(page.locator("h1")).to_contain_text("Pantry")

        # Look for stock management elements
        stock_elements = page.locator('.stock, .pantry-item, [data-testid="stock"]')
        if stock_elements.count() > 0:
            expect(stock_elements.first).to_be_visible()

    def test_shopping_list_workflow(self, page: Page):
        """Test shopping list functionality"""
        # Navigate to shopping list page
        page.goto(f"{self.base_url}/shopping/")

        # Check shopping list page loads
        expect(page.locator("h1")).to_contain_text("Shopping")

        # Look for shopping list elements
        shopping_elements = page.locator('.shopping-item, [data-testid="shopping-item"]')
        # Shopping list might be empty, so just check the page structure exists
        expect(page.locator("body")).to_be_visible()

    def test_api_health_endpoint(self, page: Page):
        """Test that API health endpoint is accessible"""
        response = page.request.get(f"{self.base_url}/api/health/")
        expect(response).to_be_ok()

        # Check response content
        json_response = response.json()
        assert "status" in json_response
        assert json_response["status"] == "ok"
