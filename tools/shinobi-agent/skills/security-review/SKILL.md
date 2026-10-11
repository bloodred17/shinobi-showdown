---
name: security-review
description: 'Assess trust boundaries and abuse cases for changes involving authorization, untrusted input, secrets or tool execution.'
---

# Security review

Identify assets, actors, entry points and trust boundaries relevant to the change. Read the actual authorization and data flow rather than rely on framework labels.

1. Trace untrusted input to privileged operations, queries, filesystem paths, subprocesses and output rendering. Distinguish authentication from authorization at the resource and action boundary.
2. Examine least privilege, tenant/user isolation, secret handling, error disclosure and resource exhaustion where implicated. Do not print credentials into evidence.
3. Construct concrete abuse scenarios and expected rejection behavior. Include legitimate operations so hardening does not simply disable the feature.
4. Recommend the smallest correction and tests at the real boundary. Avoid an unrelated organization-wide checklist or dependency upgrade campaign.
5. Verify fixes with authorized local fixtures. Scanning third-party services, exploiting production systems or changing permissions requires separate scope.

Output: prioritized findings with triggering conditions, evidence, corrections and residual risks. A scanner pass is evidence about its coverage, not proof that the system is secure.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
