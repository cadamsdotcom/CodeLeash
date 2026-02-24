# Standard Library
import json
import os
from urllib.parse import urljoin

import jinja2
from fastapi import Request

# Only used if you override the default Vite server port
VITE_SERVER_PORT = os.getenv("VITE_SERVER_PORT", 5173)
STATIC_PATH = "/dist/"
MANIFEST_PATH = "dist/.vite/manifest.json"


def hot_reload() -> bool:
    return os.getenv("ENVIRONMENT") not in ["production", "e2e"]


def parse_manifest() -> dict:
    if not hot_reload():
        with open(MANIFEST_PATH) as manifest_file:
            manifest_content = manifest_file.read()
        try:
            return json.loads(manifest_content)
        except Exception:
            raise RuntimeError(f"Cannot read Vite manifest file at {MANIFEST_PATH}")
    return {}


def generate_script_tag(src: str, attrs: dict[str, str] | None = None) -> str:
    attrs_str = ""
    if attrs is not None:
        attrs_str = " ".join([f'{key}="{value}"' for key, value in attrs.items()])

    return f'<script {attrs_str} src="{src}"></script>'


def generate_stylesheet_tag(href: str) -> str:
    return f'<link rel="stylesheet" href="{href}" />'


def generate_modulepreload_tag(path: str) -> str:
    """
    Generates a <link rel="modulepreload"> tag for the given href.
    This is used to preload JavaScript modules in Vite.
    """
    return f'<link rel="modulepreload" href="{urljoin(STATIC_PATH, path)}">'


def get_vite_server_url(request: Request | None = None) -> str:
    """
    Get the Vite server URL from request context or fallback to environment variable.
    """
    if not hot_reload():
        raise RuntimeError(
            "Vite server is not used in production; in production, uvicorn serves Vite-built files."
        )

    if not request:
        raise RuntimeError("Cannot determine Vite server URL without request context")

    # Use request context to build URL
    scheme = request.url.scheme
    # Check for forwarded headers (when behind proxy)
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        scheme = forwarded_proto

    # Get host from headers
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        raise RuntimeError(
            "Cannot determine Vite server URL from request headers: need 'host' or 'x-forwarded-host'"
        )

    # For Vite dev server, we need to use port 5173 (or custom port if set)
    # Extract hostname without port from the request host
    hostname = host.split(":")[0]
    return f"{scheme}://{hostname}:{VITE_SERVER_PORT}/"


def generate_vite_ws_client(request: Request | None = None) -> str:
    """
    Generates the script tag for the Vite WS client for HMR.

    Only used in development, in production this method returns
    an empty string.
    """
    if not hot_reload():
        return ""

    vite_url = get_vite_server_url(request)
    return generate_script_tag(
        urljoin(vite_url, "@vite/client"),
        {"type": "module"},
    )


def generate_vite_react_hmr(request: Request | None = None) -> str:
    """
    Generates the script tag for the Vite WS client for HMR.
    """
    if hot_reload():
        vite_url = get_vite_server_url(request)
        return f"""
            <script type="module">
            import RefreshRuntime from '{vite_url}@react-refresh'
            RefreshRuntime.injectIntoGlobalHook(window)
            window.$RefreshReg$ = () => {{}}
            window.$RefreshSig$ = () => (type) => type
            window.__vite_plugin_react_preamble_installed__ = true
            </script>
            """
    return ""


def generate_vite_asset(
    path: str,
    request: Request | None = None,
    scripts_attrs: dict[str, str] | None = None,
) -> str:
    """
    Generates all assets include tags for the file in argument.
    """
    if hot_reload():
        vite_url = get_vite_server_url(request)
        return generate_script_tag(
            urljoin(vite_url, path),
            {"type": "module"},
        )

    manifest = parse_manifest()

    if manifest is None or path not in manifest:
        raise RuntimeError(f"Cannot find {path} in Vite manifest at {MANIFEST_PATH}")

    tags = []
    manifest_entry: dict = manifest[path]
    if not scripts_attrs:
        scripts_attrs = {"type": "module", "async": "", "defer": ""}

    # Add dependent CSS
    if "css" in manifest_entry:
        for css_path in manifest_entry.get("css", []):
            tags.append(generate_stylesheet_tag(urljoin(STATIC_PATH, css_path)))

    # Add dependent "vendor"
    if "imports" in manifest_entry:
        for vendor_path in manifest_entry.get("imports", []):
            tags.append(
                generate_vite_asset(
                    vendor_path, request=request, scripts_attrs=scripts_attrs
                )
            )

    # Add the script by itself
    tags.append(
        generate_script_tag(
            urljoin(STATIC_PATH, manifest_entry["file"]),
            attrs=scripts_attrs,
        )
    )

    # Add modulepreload tags for all dependencies
    if "imports" in manifest_entry:
        for vendor_path in manifest_entry.get("imports", []):
            if manifest is None or vendor_path not in manifest:
                raise RuntimeError(
                    f"Cannot find {vendor_path} in Vite manifest at {MANIFEST_PATH}"
                )
            tags.append(generate_modulepreload_tag(manifest[vendor_path]["file"]))

    return "\n".join(tags)


def vite_hmr_client(
    request: Request | None = None,
) -> jinja2.utils.markupsafe.Markup:
    """
    Generates the script tag for the Vite WS client for HMR.
    Only used in development, in production this method returns
    an empty string.
    """
    tags: list = []
    tags.append(generate_vite_react_hmr(request))
    tags.append(generate_vite_ws_client(request))
    return jinja2.utils.markupsafe.Markup("\n".join(tags))


def vite_asset(
    path: str,
    request: Request | None = None,
    scripts_attrs: dict[str, str] | None = None,
) -> jinja2.utils.markupsafe.Markup:
    """
    Generates all assets include tags for the file in argument.
    Generates all scripts tags for this file and all its dependencies
    (JS and CSS) by reading the manifest file (for production only).
    In development Vite imports all dependencies by itself.
    Place this tag in <head> section of yout page
    (this function marks automaticaly <script> as "async" and "defer").
    """
    return jinja2.utils.markupsafe.Markup(
        generate_vite_asset(path, request=request, scripts_attrs=scripts_attrs)
    )
