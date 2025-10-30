"""
Coder prompts (extracted verbatim). Do not modify content.
"""

def build_coder_v0_prompt(instruction: str) -> str:
    return f"""Create a single-page web application based on the following specification:

{instruction}

Requirements:
1. Create a complete HTML file with embedded CSS and JavaScript
2. The app should be fully functional and interactive
3. Use modern HTML5, CSS3, and vanilla JavaScript (no external libraries)
4. Include proper semantic HTML structure
5. Make the UI clean, responsive, and user-friendly
6. Add unique IDs to interactive elements for easier automation testing
7. Ensure the app works in a 1280x720 viewport

Please generate the complete HTML file:"""


def build_coder_v1_failure_prompt(app_name: str, model_name: str, v0_html: str,
                                   failed_tasks_len: int, failure_categories_keys: list,
                                   non_regression_contract_prompt: str,
                                   failure_analysis: str,
                                   apply_destylization: bool) -> str:
    prompt = f"""You are tasked with improving a web application based on detailed failure analysis from automated testing.

## CONTEXT
Application: {app_name}
Model: {model_name}
Total Failed Tasks: {failed_tasks_len}
Failure Categories: {failure_categories_keys}
Original initial HTML Length: {len(v0_html.strip())} characters

## LENGTH REQUIREMENTS
**CRITICAL**: Generate a COMPLETE, FULL-LENGTH HTML file that is comparable to or longer than the original initial website.
The output should be a fully functional web application with complete CSS and JavaScript.
DO NOT truncate, abbreviate, or use placeholders in the HTML code.
Generate the ENTIRE HTML file from <!DOCTYPE html> to </html>.

## ORIGINAL INITIAL WEBSITE (FULL)
```html
{v0_html}
```

## COMMENTER UI ANALYSIS
{(failure_analysis or "No visual UI analysis available").strip()}

{(non_regression_contract_prompt or '').strip()}

## IMPROVEMENT REQUIREMENTS

### 1. Core Issues to Address
Based on the failure analysis, you must:
- Identify missing DOM elements that tasks expect to exist
- Add missing JavaScript functionality for user interactions
- Fix timing issues that prevent task completion
- Ensure proper event handling and state management
- Add missing visual feedback and UI updates

### 2. Specific Fixes Needed
For each failed task category:
- **basic_usage**: Ensure fundamental interactions work (clicking, displaying, updating)
- **workflow**: Support complete user workflows and multi-step processes
- **advanced_feature**: Implement sophisticated UI behaviors and animations
- **edge_case**: Handle unusual inputs and boundary conditions properly

### 3. Technical Implementation Guidelines
- Preserve ALL existing working functionality from the initial version
- Add missing HTML elements with unique IDs for automation
- Implement complete JavaScript event handlers and state updates
- Ensure synchronous UI updates for immediate feedback
- Do NOT introduce new input constraints that would block task inputs implied by the tasks (e.g., accept plain text or non-HTTP payloads if tasks need them). Validation must be permissive and never reduce what the initial version allowed.
- Do NOT auto-trigger flows on page load that would change initial states relied upon by tasks (e.g., auto-generation, auto-download, auto-navigation). Initial state should be neutral and idle.
- Keep critical controls visible within a 1280x720 viewport without scrolling. Avoid multi-panel "hub" layouts; prefer single-view, compact layouts that fit important controls on screen.
- Avoid adding non-essential animations/transitions; prioritize high visibility and clarity over decoration.
- Make sure timers, counters, and dynamic content work correctly

### 4. DOM Structure Requirements
- Every interactive element MUST have a unique ID
- Form controls must have proper event listeners
- Dynamic content areas must update immediately on state changes
- Visual feedback must be implemented for all user actions

### 5. JavaScript Functionality Requirements
- All user interactions mentioned in failed tasks must be fully implemented
- State changes must be reflected in the DOM immediately
- Event handlers must properly update all related UI elements
- Any game logic, scoring, timing must be complete and functional

Surgical Revision Policy
- Preserve existing IDs; do not rename or remove working elements from the initial version.
- Avoid large rewrites. Patch only the functions, event handlers, and minimal markup necessary to satisfy the failed/unsupported tasks.
- Preserve working logic from the initial version; do not regress features that already work.
- Reuse existing elements/IDs for state wherever possible; only add new IDs if strictly necessary to expose the state of new logic.
- Preserve initial immediacy semantics. Do NOT introduce extra confirmation steps as prerequisites where the initial version achieved completion via immediate interactions. Implement functional logic first, then expose proxies from the same code path; never update proxies without the underlying state change.

Commenter JSON (if provided)
- If the COMMENTER UI ANALYSIS is a JSON object, prioritize applying entries in `actionable_changes` precisely.
- Keep changes surgical and bounded by those actionable suggestions; do not broaden scope beyond them.

## OUTPUT REQUIREMENTS
Generate a COMPLETE, FULLY FUNCTIONAL HTML file that:
1. Addresses ALL failure points identified in the analysis
2. Maintains existing successful functionality from the initial version
3. Implements missing features causing task failures
4. Provides proper DOM elements for automation testing
5. Ensures immediate UI feedback for all user actions
6. Contains COMPLETE CSS styling and JavaScript functionality
7. Is a full-length, complete web application (not truncated)"""

    if apply_destylization:
        prompt += """

You must apply strict destylization and viewport optimization while improving functionality.

Destylization And Viewport Optimization

A. Visual Simplification
- Use #ffffff background and #000000 primary text; limit accents to a small, consistent palette.
- No gradients, animations, transitions, shadows, decorative borders, or rounded corners.
- Maintain a clear visual hierarchy via weight, size, and spacing.

- Behavior preservation: Reducing visual style MUST NOT delay, throttle, or gate state updates/animations behind confirmations. Preserve interaction‑to‑state immediacy; simplify visuals only.
- Live parity: Any user action that was immediate in the initial version MUST remain immediate in the revised version. Do not convert an immediate success condition into a confirm‑gated flow.

B. Action Affordances
- Minimum target size: all primary controls (buttons, toggles, sliders, actionable links) ≥ 44×44 px.
- Clear labels: every primary action uses a visible text label (e.g., "Generate", "Solve", "Download PNG").
- Primary action placement: position near the related input, in the upper-left or central region of the control panel.
- Spacing: keep 12–16 px between controls to avoid accidental clicks.

C. Input And Submission Behavior
- Non-destructive changes (text edits, sliders, toggles, color picks) MUST immediately update functionality and completion proxies. Enter/blur triggers the same updates by default.
- Explicit primary actions are reserved for irreversible or multi‑step submissions. They MUST NOT be the only path to reach the completion state. Both the live path (immediate changes) and any confirm path MUST drive the same proxy/attribute changes.

D. Completion Feedback And Status Indicators
- When an action completes (e.g., a result is produced, a preview is ready, or a download becomes available), update a visible status indicator synchronously with that change.
  - Example: set "#downloadStatus" to "enabled" when the download link becomes available.
  - Example: set "#solveStatus" to "done" when the solution summary is populated.
- These indicators must be meaningful to users and update exactly when the underlying state changes.

E. Layout Density Guardrail
- Fit within a 1280×720 viewport without cramming controls. Prefer a two-column layout on desktop (controls left, preview/result right).
- Keep the preview/result area fully visible and not overlapped; allow scrolling only for long histories/logs.
- Do not reduce control sizes below the 44×44 px target.

F. Keyboard And Hints
- Provide short keyboard hints for both live and confirm paths (e.g., "Edits update live · Enter applies").
- Ensure obvious focus styles and that Enter/blur trigger the same live updates as mouse/touch.
 
G. Interactive Controls (Operator-Friendly)
- For sliders/continuous controls, add adjacent +/- step buttons and arrow-key handling (Left/Right or Up/Down) with visible focus styles.
- "Apply/Confirm" MAY exist as an optional consolidation step, but live adjustments MUST already update the underlying state and completion proxies without requiring Apply. Apply SHOULD mirror the same updates (and may set "#applyStatus").
- Avoid making drag the only way to change values; a click/keyboard path must exist.

H. Landing & Navigation Proxies
- After in-page navigation (e.g., scrollIntoView or clicking a nav item), set "#activeSection" to the target section id or title.
- When a CTA opens an external page, set "#lastLinkClicked" to a human-readable label; external links should use target="_blank" and be visible as anchors with href.

I. Tool/Utility Preview & Export Proxies
- When a preview is ready, expose it via attributes (e.g., "<img id='preview' src='data:image/...'>", or "<canvas id='previewCanvas' data-ready='true'>") and set a visible proxy "#previewStatus" to "ready".
- When a download is ready, ensure an anchor exists with data href (e.g., "<a id='download' href='data:...' download>") and set "#downloadStatus" to "enabled".
- Both the immediate (live) interaction path and any confirm path MUST trigger these signals. Do NOT require "Confirm/Generate" to enable preview/download if content is valid; live edits MUST produce the same ready/enabled state.

J. Input Trigger Boundaries
- Enter/blur auto-apply is limited to safe transforms (e.g., hex normalization, live preview refresh). It must not submit multi-step processes, navigate away, or dismiss dialogs.

K. ID Stability And Rerenders
- All primary interactive elements and proxies must have unique, stable ids. Rerenders must preserve these ids; do not replace them with transient ids or remove them.
"""

    # Mandatory DOM completion proxies (always required)
    prompt += """

MANDATORY DOM COMPLETION PROXIES
- For every user-visible success event, provide both of the following in the DOM:
  1) An attribute predicate signal on the real element (e.g., "#download[href^='data:']", "#btnSubmit[aria-disabled='false']", "#chartType[value='Line']", "#resultValue[data-ready='true']").
  2) A visible proxy with a stable id and text/number (e.g., "#downloadStatus" contains "enabled", "#solveStatus" == "done", "#chartTypeLabel" == "Line").
- Update both signals synchronously with the state change (no timers). Never remove these proxies.
- Signal sources MUST be wired to the functional code paths used by live interactions. Never restrict proxy updates to only the confirm action; the same code path MUST drive both attribute predicates and visible proxies for live and confirm flows.

Please generate the complete improved HTML file:"""
    return prompt


def build_coder_v1_unsupported_prompt(app_name: str, model_name: str, v0_html: str,
                                       unsupported_summary: str,
                                       non_regression_contract_prompt: str,
                                       ablate_no_contract: bool) -> str:
    return f"""You are tasked with improving a web application to support additional tasks that are currently unsupported.

## CONTEXT
Application: {app_name}
Model: {model_name}
Total Unsupported Tasks: {unsupported_summary.count('Task ID:')}
Original initial HTML Length: {len(v0_html.strip())} characters

## ORIGINAL INITIAL WEBSITE (FULL)
```html
{v0_html}
```

## UNSUPPORTED TASKS ANALYSIS
{unsupported_summary}

## CODE PRESERVATION CONTRACT (Non-Regression)
{'' if ablate_no_contract else (non_regression_contract_prompt or '').strip()}

## IMPROVEMENT REQUIREMENTS

### 1. Task Support Issues to Address
Based on the unsupported task analysis, you must ADD missing functionality:
- Add missing DOM elements that tasks expect to exist
- Implement missing JavaScript functionality for user interactions
- Add missing form controls and input handling
- Implement missing display areas and visual feedback
- Add missing navigation and UI components

### 2. Implementation Guidelines
- PRESERVE all existing working functionality from the initial version
- ADD new HTML elements with unique IDs for automation
- IMPLEMENT complete JavaScript event handlers for new features
- ENSURE new UI elements are properly styled and visible
- DO NOT introduce new input constraints that would block task inputs implied by tasks; validation must be permissive and must not reduce what the initial version allowed.
- DO NOT auto-trigger flows on load that change initial states (no auto-generation, auto-download, auto-navigation). Start in a neutral, idle state.
- FIT critical controls within a 1280x720 viewport without scrolling. Avoid multi-panel hub layouts and unnecessary panels that push controls below the fold.
- IMPLEMENT missing workflows and user interaction patterns

### 3. DOM Structure Requirements
- Every new interactive element MUST have a unique ID
- New form controls must have proper event listeners
- New content areas must update appropriately on state changes
- New visual feedback must be implemented for added interactions

### 4. JavaScript Functionality Requirements
- All new user interactions mentioned in unsupported tasks must be fully implemented
- New state changes must be reflected in the DOM immediately
- New event handlers must properly update all related UI elements
- Any new game logic, scoring, timing must be complete and functional

## OUTPUT REQUIREMENTS
Generate a COMPLETE, FULLY FUNCTIONAL HTML file that:
1. Maintains ALL existing functionality from the initial version
2. ADDS missing functionality to support the unsupported tasks
3. Implements new DOM elements and JavaScript for task support
4. Ensures all new features are testable and functional
5. Contains COMPLETE CSS styling for all new elements
6. Is a full-length, complete web application (not truncated)

Commenter JSON (if provided)
- If upstream provides a commenter JSON analysis with `actionable_changes`, follow those changes first, precisely and surgically.

Surgical Revision Policy
- Preserve existing IDs; do not rename or remove working elements from the initial version.
- Avoid large rewrites. Patch only the functions, event handlers, and minimal markup necessary to satisfy the failed/unsupported tasks.
- Preserve working logic from the initial version; do not regress features that already work.
- Reuse existing elements/IDs for state wherever possible; only add new IDs if strictly necessary to expose the state of new logic.
- Preserve initial immediacy semantics. Do NOT introduce extra confirmation steps as prerequisites where the initial version achieved completion via immediate interactions. Implement functional logic first, then expose proxies from the same code path; never update proxies without the underlying state change.

Please generate the complete improved HTML file:"""
