---
name: browser-verification
description: 'Plan or execute browser-visible verification with real user interactions and evidence when an authorized browser environment exists.'
---

# Browser verification

Identify the required user journey, relevant UI states and available browser harness. Reuse the project's proven verification recipe and stable accessible selectors.

1. Check instance ownership, build identity, readiness, authentication and isolated test data before driving it.
2. Exercise the actual user interaction; cover the requested success path and consequential loading, error, empty or denied states. Do not substitute internal state setters for the action under test.
3. Observe visible results, console/network failures and relevant side effects. A screenshot alone may not show that the action worked.
4. Check keyboard/focus behavior and responsive or accessibility requirements implicated by the change. Record viewport and other conditions for visual comparisons.
5. Capture evidence and clean up only owned browser/process/test state. Preserve proof artifacts after cleanup.

Output: exercised scenarios, actual evidence and untested cases. Shinobi's current offline Linux profile has no browser capability. In that profile this skill can specify the needed verification, but must report it unrun and request an explicitly supported environment; do not claim UI validation from a unit test.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
