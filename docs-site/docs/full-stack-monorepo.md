---
title: 'Full-Stack Monorepo'
sidebar_position: 2
---

CodeLeash runs Vite and FastAPI as a single application. In development, two servers run concurrently with hot module replacement. In production, Vite builds static assets and FastAPI serves everything.

## Dual-Server Architecture

The `npm run dev` command starts three processes via `concurrently`:

```bash
concurrently -n vite,uvicorn,worker \
  vite \
  "uv run python main.py" \
  "uv run python worker.py"
```

> [`package.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/package.json)

- **Vite** (port 5173) serves JavaScript/CSS with HMR
- **Uvicorn** (port 8000) serves HTML pages and API routes
- **Worker** processes background jobs (see [Worker System](./worker-system.md))

In production (`npm run build` then `uv run uvicorn main:app`), Vite compiles assets into `dist/` and FastAPI serves them directly using the Vite manifest for cache-busted URLs.

## The `render_page()` Pattern

Every page follows the same flow: a FastAPI route gathers data, passes it to `render_page()`, which renders a Jinja2 template that mounts a React component.

### Route Layer

```python
@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    greeting_service: GreetingService = Depends(get_greeting_service),
) -> HTMLResponse:
    greetings = await greeting_service.get_all()
    initial_data = {
        "greetings": [g.model_dump(mode="json") for g in greetings],
    }
    return render_page(
        request, "src/roots/index.tsx",
        title="CodeLeash", initial_data=initial_data,
    )
```

> [`app/routes/index.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/routes/index.py)

The route calls a service (injected via `Depends()`), serializes the result to a dict, and passes it as `initial_data`.

### Template Layer

`render_page()` JSON-serializes the initial data into the template context:

```python
def render_page(request, component_path, title, initial_data=None, ...):
    initial_data_json = json.dumps(initial_data or {})
    return templates.TemplateResponse(request, "page.html", {
        "component_path": component_path,
        "title": title,
        "initial_data_json": initial_data_json,
    })
```

> [`app/core/templates.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/templates.py)

The [`page.html`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/templates/page.html) template contains the critical bridge:

```html
<div
  id="root"
  data-initial="{{ initial_data_json | escape }}"
  class="{{ root_css_class }}"
></div>
{{ vite_hmr_client(request) }} {{ vite_asset(component_path, request) }}
```

The initial data is embedded as a `data-initial` attribute on the root div --- HTML-escaped JSON that React reads on mount.

### React Layer

`createReactRoot()` parses the `data-initial` attribute and wraps the component in providers:

```tsx
export const createReactRoot = (ComponentClass: React.ComponentType) => {
  const initializeRoot = () => {
    const rootElement = document.getElementById('root');
    const initialData = rootElement.dataset.initial;
    const data = initialData ? JSON.parse(initialData) : {};

    createRoot(rootElement).render(
      <React.StrictMode>
        <ErrorBoundary>
          <InitialDataProvider data={data}>
            {React.createElement(ComponentClass)}
          </InitialDataProvider>
        </ErrorBoundary>
      </React.StrictMode>
    );
  };
  // ...
};
```

> [`src/roots/util.tsx`](https://github.com/cadamsdotcom/CodeLeash/blob/main/src/roots/util.tsx)

Each page's root file is minimal:

```tsx
import Index from '../pages/Index';
import { createReactRoot } from './util';
createReactRoot(Index);
```

> [`src/roots/index.tsx`](https://github.com/cadamsdotcom/CodeLeash/blob/main/src/roots/index.tsx)

Components access the data via a `useInitialData()` hook provided by `InitialDataProvider`.

## Complete Data Flow

```
Route handler
  → service.get_all()
  → initial_data dict
  → render_page()
  → json.dumps(initial_data)
  → page.html template
  → data-initial="..." attribute
  → createReactRoot()
  → JSON.parse(dataset.initial)
  → InitialDataProvider
  → useInitialData() hook
  → Component renders
```

## Vite Integration

The [`vite_loader.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/vite_loader.py) module handles both development and production modes:

**Development** (`ENVIRONMENT != "production"`):

`vite_hmr_client()` builds the Vite dev server URL from the request hostname, so HMR works regardless of how the browser reaches the server:

```python
def get_vite_server_url(request: Request | None = None) -> str:
    hostname = request.headers.get("host").split(":")[0]
    return f"{scheme}://{hostname}:{VITE_SERVER_PORT}/"
```

> [`app/core/vite_loader.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/vite_loader.py)

**Production**:

`vite_asset()` reads `dist/.vite/manifest.json` to resolve cache-busted file paths, CSS dependencies, and module preload hints:

```python
manifest = parse_manifest()
manifest_entry = manifest[path]

# Add CSS, vendor imports, the script itself, and modulepreload tags
tags.append(generate_stylesheet_tag(urljoin(STATIC_PATH, css_path)))
tags.append(generate_script_tag(
    urljoin(STATIC_PATH, manifest_entry["file"]), attrs=scripts_attrs,
))
```

> [`app/core/vite_loader.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/vite_loader.py)

```python
# Development: script points at Vite server
<script type="module" src="http://localhost:5173/src/roots/index.tsx"></script>

# Production: script points at built asset
<script type="module" async defer src="/dist/assets/index-a1b2c3d4.js"></script>
<link rel="stylesheet" href="/dist/assets/index-e5f6g7h8.css" />
```

## Type Safety: Pydantic to TypeScript

The `npm run types` command runs `scripts/generate_types.py`, which converts Pydantic models to TypeScript interfaces. A pre-commit hook (`check-initial-data`) verifies these types stay in sync, so the `data-initial` JSON and TypeScript types never drift apart.

## Rollup Entry Points

Vite is configured with three entry points in [`vite.config.js`](https://github.com/cadamsdotcom/CodeLeash/blob/main/vite.config.js):

```javascript
rollupOptions: {
  input: {
    main: './src/main.ts',      // Global CSS and shared code
    app: './src/app.ts',        // Application-wide scripts
    index: './src/roots/index.tsx',  // Page-specific root
  },
},
```

Adding a new page means adding a new root file in `src/roots/` and a corresponding entry in the Vite config.
