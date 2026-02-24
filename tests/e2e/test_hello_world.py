"""E2E test for the hello world page."""

from playwright.sync_api import Page, expect

from tests.e2e.conftest import get_base_url


def test_hello_world_page(page: Page) -> None:
    """Test that visiting / shows the hello world page with the seeded greeting."""
    base_url = get_base_url()
    page.goto(base_url)

    # Verify the page title
    expect(page.locator("h1")).to_have_text("CodeLeash")

    # Verify the seeded greeting is displayed
    expect(page.get_by_text("Hello from CodeLeash!")).to_be_visible()
