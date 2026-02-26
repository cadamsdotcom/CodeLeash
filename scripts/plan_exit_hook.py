#!/usr/bin/env python3
"""PreToolUse hook for ExitPlanMode - provides TDD checklist and nested Claude review.

On first call in a session:
- Outputs the TDD Planning Checklist reminder
- Invokes nested Claude to review the plan
- Blocks the ExitPlanMode call (exit 2) so Claude addresses feedback

On second+ calls in same session:
- Allows the call to proceed (exit 0)

Uses session_id from stdin to track state, so plan edits don't reset the review cycle.
"""

import json
import subprocess
import sys
from pathlib import Path


def get_state_file(session_id: str) -> Path:
    """Get state file path for tracking reviewed plans.

    Uses session ID so plan edits don't trigger new reviews within same session.
    """
    return Path(f"/tmp/.claude-plan-reviewed-{session_id}")


def get_nested_claude_review(plan_content: str) -> str:
    """Invoke nested Claude to review the plan."""
    prompt = f"""Review this implementation plan. Focus on:
- Does it specify writing e2e tests before implementation?
- Does it plan TDD at unit/integration/component level?
- Could existing e2e tests be enhanced instead of writing new ones?
- Could any planned e2e tests be unit/integration/component tests instead?
- If e2e tests are excluded, is the justification reasonable?
- If e2e tests are included, are they being implemented first then used as acceptance criteria?
- Can part or all of this task be accomplished by writing scripts (regex, shell scripts, AST walking)
  instead of manual edits? Consider automation especially for large refactors, renames, or bulk transformations.
- If the plan removes features, routes, or UI elements: does it include a cleanup step
  to remove absence tests, dead code, stale references, and vestigial branches?
- If the plan adds or updates queries or handles untrusted user data:
  are role-based access checks present? Is the updatable data (eg. specific fields) restricted to only what is needed?
For test efficiency:
- Does the plan prefer to add assertions to existing tests rather than add new tests in cases where
  the setup is largely the same and the existing test covers substantially the same scenario, or the
  new behavior is additional to the same operation and not a different code path?
- Are there planned tests that construct the same object multiple times to assert
  one property each? These should be consolidated into fewer tests with multiple
  assertions on the same instance.
- Do any planned test classes duplicate coverage already provided by another class
  in the same file?
- Could @pytest.mark.parametrize replace groups of near-identical test functions
  that vary only in input/expected values?
- Does the plan say "no test needed" or rationalize skipping tests for any changed file?
  If so, flag it - if it's worth implementing, it's worth testing.
- If the plan modifies UI rendering (new elements, conditional display, disabled states,
  event handlers), does it require component-level tests? Hook tests and backend tests
  do NOT substitute for component tests that verify rendering and interaction.

Provide brief, actionable feedback. Be critical. Keep response under 200 words.

Plan:
{plan_content}"""

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout.strip():
            return result.stdout.strip()
        return "(No review output)"
    except subprocess.TimeoutExpired:
        return "(Review timed out after 60 seconds)"
    except FileNotFoundError:
        return "(Claude CLI not found)"
    except Exception as e:
        return f"(Review failed: {e})"


def main() -> None:
    # Parse JSON from stdin
    stdin_data = sys.stdin.read()
    try:
        data = json.loads(stdin_data)
        session_id = data.get("session_id", "default")
        plan_content = data.get("tool_input", {}).get("plan", "")
    except (json.JSONDecodeError, AttributeError):
        session_id = "default"
        plan_content = ""

    state_file = get_state_file(session_id)

    # Already reviewed once this session? Allow through (plan edits don't reset)
    if state_file.exists():
        sys.exit(0)

    # Mark as reviewed BEFORE outputting feedback
    # This ensures the second call will pass through
    state_file.touch()

    # Part 1: Output TDD checklist to stderr
    print(
        """
BLOCKED: Plan requires TDD review before user approval.

Claude: Before the user approves this plan, verify it addresses:

1. Consider if this plan can be implemented without e2e tests by moving coverage to unit/integration/component tests
2. Write e2e tests FIRST before implementation to use as acceptance tests
3. Plan TDD at unit/integration/component level for all changes
4. Even if you have e2e coverage, you need to write unit/integration/component tests
5. Can existing e2e tests be enhanced to cover this work instead of writing new ones?
6. Can planned e2e tests be unit/integration/component tests instead?
7. Prefer adding assertions to existing tests over writing new tests when:
   - The setup/fixtures would be largely the same
   - The existing test covers substantially the same scenario
   - New behavior is additional to the same operation, and not a different code path
8. Consider automation: Can part or all of this task be accomplished by writing scripts instead of manual edits?
   - Large refactors, renames across files, bulk transformations → use regex, shell commands, or AST walking
   - Pattern-based changes → write a script to apply them consistently
   - Multi-file updates → automate with find/sed/awk or Python scripts
   - Even if you can't automate everything, automating parts can speed things up significantly
   - Especially valuable for tasks touching 5+ files or requiring consistent transformations
9. Review planned tests for efficient construction:
   - If multiple tests construct the same object to assert one property each,
     write one test with multiple assertions instead
   - If a test class fully overlaps another class in the same file, delete it
   - Prefer parameterized tests over copy-paste functions with minor variations
10. Consider access control and what data/fields are writable:
   - Are role-based access checks present?
   - If the plan adds or updates queries or handles user data, are the updatable fields restricted to only those needed?
11. If the plan modifies UI rendering (new elements, conditional display, disabled states,
    event handlers), component tests are required - not optional. Hook tests verify data flow,
    backend tests verify the API, but neither verifies that elements render or wire events correctly.
12. Reject any plan section that says "no test needed" - if it's worth implementing, it's worth testing.
13. Add a CLEANUP step at the end of your plan that addresses:
   - Remove "absence tests" used during TDD to verify removal of features/routes/UI
     (tests that assert something is NOT present are scaffolding, not long-term value)
   - Collapse thin wrapper functions that now just delegate to a single call
   - Update or remove comments and docstrings that reference removed features
   - Remove stale TODO/FIXME comments that were addressed during implementation
   - Address any test construction issues from item 9 that slipped through
   - Clean up unused Pydantic model fields and API response fields
   - Run pre-commit checks (npm run pre-commit) and fix all failures - this catches
     unused imports, dead functions, vestigial conditionals, unused routes, and more
""",
        file=sys.stderr,
    )

    # Part 2: Get nested Claude's review
    print("--- Nested Claude Review ---", file=sys.stderr)
    review = get_nested_claude_review(plan_content)
    print(review, file=sys.stderr)

    print(
        "\nUpdate your plan to address this feedback, then call ExitPlanMode again.",
        file=sys.stderr,
    )

    # Block the tool call
    sys.exit(2)


if __name__ == "__main__":
    main()
