# Internal Server Error in AI Poll Generation

## Goal
Fix the "Internal Server Error" that occurs when clicking "Create Poll from this Opinion" button.
The error is likely caused by an unhandled exception during the import of `features.poll_manager` or its execution within `generate_ai_poll`.

## User Review Required
None.

## Proposed Changes

### Diagnosis
1. Create `debug_import.py` to attempt importing `features.poll_manager` and print any errors.
2. Run this script using the project's virtual environment to identify the missing dependency or configuration issue.

### Fixes
1. **Install Missing Dependencies**: If a dependency is missing (e.g., `line-bot-sdk`), install it.
2. **Add Error Handling**: Modify `admin/admin_app.py` to wrap the import and execution of `create_poll_draft_from_analysis` in a `try...except` block that catches `ImportError` and other exceptions, flashing a user-friendly error message instead of crashing.

#### [MODIFY] [admin_app.py](file:///root/workspace/hirakata_bot1/admin/admin_app.py)
- Wrap `from features.poll_manager import create_poll_draft_from_analysis` in a try-except block.
- Ensure all exceptions are caught and logged, returning a redirect with a flash message.

## Verification Plan

### Automated Tests
- Run `debug_import.py` after the fix to ensure the module can be imported.
- Run `python3 -c "from admin.admin_app import generate_ai_poll; print('Function loaded')"` to verify syntax.

### Manual Verification
- Since I cannot access the browser, I will rely on the script execution success and the presence of error handling code.
