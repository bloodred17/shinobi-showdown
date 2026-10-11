---
name: verification-maintenance
description: 'Audit a project verification recipe against current source and live feature behavior when the app or harness has changed.'
---

# Verification maintenance

Read the current project verification skill, feature map and relevant source changes. Identify which instructions may have drifted; do not regenerate a working recipe merely because this skill is available.

1. Inventory mapped user features and actual routes, commands or menus. Detect missing entry points, obsolete selectors, changed prerequisites and undocumented side effects.
2. Check launch, doctor, evidence storage, isolation and cleanup against the current environment. Drive the affected journeys; a full maintenance audit covers all mapped features or names every unrun case.
3. Classify discrepancies as documentation drift, harness gap, product regression or unavailable environment. A product regression must remain visible; do not edit the recipe to avoid the broken path or change product code as undocumented maintenance.
4. Update only the authorized verification instructions and helpers. Keep concrete commands, stable handles and expected outcomes grounded in observed behavior and accepted requirements.
5. Run the changed recipe end to end, including failure cleanup and evidence retention. State which features were observed and which remain unverified.

Output: corrected local recipe and feature map, evidence, product defects and limitations. This maintenance is a separately scoped task. An execution run cannot rewrite its own approved checks or governing instructions to make verification pass.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
