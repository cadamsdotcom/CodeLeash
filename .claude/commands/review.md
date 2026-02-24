Review the changes on the current branch compared to main. Do not use subagents. Run `git diff main...HEAD` to see all changes.

Check for these classes of issues:

### Naming Consistency

- Are new function/class/method names consistent with existing naming conventions?
- Do queue job function names follow the pattern `enqueue_[full_entity_name]_[action]_job`?
- Are abbreviations avoided in favor of full descriptive names?

### Schema Design

- Do new Pydantic Create/Update models have appropriate field constraints?
- If a Create model uses `min_length`/`max_length`, does the corresponding Update model?
- Are there new schemas that largely duplicate existing ones? Could they reuse an existing schema?

### API Design

- Are there new routes that are very similar to existing routes? (e.g. singular vs plural paths, or a single-item route that duplicates a bulk route)
- Could new single-item endpoints be handled by existing bulk endpoints?
- Are route paths consistent (singular vs plural)?

### Parameter Design

- Are there Optional parameters that are always provided at every call site?
- Should they be required instead?

### Data Loading

- Are there pages that fetch data after page load (e.g. useEffect + API call on mount) where that data could instead be supplied via `initial_data` on the server-rendered response?
- Look for patterns like `useEffect(() => { fetch(...) }, [])` that load data which is known at request time and could be embedded in the initial page load.

### Route Permission Checks

- Do all new or modified API routes have appropriate permission checks (e.g. verifying the user has the correct role or ownership)?
- Are there any routes that are open to all authenticated users (or unauthenticated users) without an explicit reason? Routes like the landing page or login are expected to be open, but other routes should enforce access control.

### Docstring Accuracy

- Do modified functions' docstrings match the function's actual behavior?
- After changes, does the docstring still accurately describe parameters, return values, and purpose?

### Dependency & Instance Initialization Consistency

- Are new services or repositories instantiated directly instead of going through `app/core/container.py`?
- All shared instances (services, repositories, clients) should be created as factory methods in `Container` and accessed via the dependency layers:
  - **Routes**: Use `Depends()` with functions from `app/core/service_dependencies.py`
  - **Auth**: Access container via `_get_container()` in `app/core/auth_dependencies.py`
  - **Worker**: Access container via `app/core/worker_dependencies.py`
  - **Scripts/CLI**: Direct `_get_container()` calls are acceptable
  - **Tests**: Direct instantiation is acceptable
- Watch for `SomeService(...)` or `SomeRepository(...)` constructor calls in route handlers, other services, or middleware — these should use the container instead.
- If a new service or repository class is introduced, does it have a corresponding factory method in `Container` and a dependency function in the appropriate dependencies module?
- Are there direct calls to infrastructure clients (e.g., `get_supabase_service_client()`) that bypass an already-injected dependency?

### Test Quality

- Could new test files be consolidated with existing ones testing similar features?
- Are new test fixtures necessary, or could existing ones be reused?
- Do test file names follow `test_[feature].py` convention without redundancy (e.g. `_e2e` suffix is redundant for files in tests/e2e/)?

For each issue found, consider:

1. File path and line number
2. The class of issue
3. Suggested fix

Make a plan to address them all without using subagents.
