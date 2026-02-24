import json
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import StrictUndefined

from app.core.vite_loader import vite_asset, vite_hmr_client

# Initialize templates
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["vite_hmr_client"] = vite_hmr_client  # type: ignore[assignment]
templates.env.globals["vite_asset"] = vite_asset  # type: ignore[assignment]

# Configure Jinja2 to be strict about undefined variables
templates.env.undefined = StrictUndefined


def render_page(
    request: Request,
    component_path: str,
    title: str,
    body_css_class: str = "",
    initial_data: dict[str, Any] | None = None,
    root_css_class: str = "",
) -> HTMLResponse:
    """Render a page using the page.html template with React component.

    Args:
        request: The FastAPI request object
        component_path: Path to the React component to render
        title: Page title
        body_css_class: CSS classes for the body element (default: "")
        initial_data: Initial data to pass to the React context (default: {})
        root_css_class: CSS classes for the root div element (default: "")

    Returns:
        HTMLResponse with the rendered page
    """
    if initial_data is None:
        initial_data = {}

    # Convert initial_data to JSON string for comparison
    initial_data_json = json.dumps(initial_data)

    return templates.TemplateResponse(
        request,
        "page.html",
        {
            "component_path": component_path,
            "title": title,
            "body_css_class": body_css_class,
            "initial_data_json": initial_data_json,
            "root_css_class": root_css_class,
        },
    )
