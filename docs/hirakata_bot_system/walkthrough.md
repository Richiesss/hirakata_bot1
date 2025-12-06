# AI Poll Generation Error Fix

## Changes
Fixed an "Internal Server Error" (500) that occurred when clicking "Create Poll from this Opinion".

### [MODIFY] [admin_app.py](file:///root/workspace/hirakata_bot1/admin/admin_app.py)
- Added `try-except` block around the `generate_ai_poll` function.
- Implemented specific handling for `ImportError` to catch missing dependency issues gracefully.
- Added logging (`app.logger.error`) to capture the specific error details for future debugging.
- Added user feedback via `flash` messages to inform the user of the error instead of crashing the page.

## Verification Results

### Automated Checks
- **Syntax Check**: Passed (`python3 -m py_compile admin/admin_app.py`).
- **Import Check**: `debug_import.py` confirmed that `features.poll_manager` can be imported in the current environment.

### Manual Verification Steps
1. Navigate to the AI Analysis Dashboard.
2. Click "Create Poll from this Opinion" on any cluster card.
3. **Expected Result**:
    - If successful: Redirects to Polls list with a success message.
    - If failed: Redirects back to Analysis Dashboard with an error message (e.g., "Error occurred: ...") instead of showing a 500 Internal Server Error page.
