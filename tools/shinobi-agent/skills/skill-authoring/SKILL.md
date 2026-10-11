---
name: skill-authoring
description: 'Author or revise a focused Shinobi skill with discoverable triggers, useful procedures, local references and observable completion conditions.'
---

# Skill authoring

Design for a capable agent arriving with a real task and limited context. A skill should change decisions or make a fragile workflow reliable, not repeat generic engineering advice.

1. Define the task trigger and the important neighboring task that should route elsewhere. Put a clear name and discriminating description in frontmatter.
2. Identify necessary inputs, ordered dependencies, decision points, outputs and completion conditions. Retain domain-specific mechanics; do not compress a useful procedure into slogans.
3. Put conditional detail in linked local references and state when to read each. Ensure tools and dependent skills are available in Shinobi. Do not link to an upstream procedure as a runtime prerequisite.
4. Preserve user intent, approved scope and realistic tool limits. Match rigor to consequences; avoid arbitrary quotas, confidence percentages and rituals.
5. For adapted material, retain required license notices and record source ancestry. Independently edit local content; no sync script or upstream byte equality is required.
6. Validate frontmatter, names, links, registration and resource loading. Then evaluate a realistic task plus a likely misrouting or failure case when the change affects behavior. Run any executable helpers you introduce.

Output: a locally maintained skill with the minimum supporting resources it actually needs. A parser pass proves structural validity only. Skill availability does not establish that the model reliably selects or follows it.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
