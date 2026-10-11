---
name: skill-improvement
description: 'Propose or apply an authorized skill revision based on demonstrated usage failures while preserving accepted decisions and counterexamples.'
---

# Skill improvement

Gather the actual request, loaded skill version, available tools, agent behavior and resulting evidence. Distinguish a bad instruction from failure to discover or follow an adequate instruction.

1. Name the decision the skill should have changed and show the relevant observed failure. Avoid adding generic advice unsupported by a real scenario.
2. Check existing local procedures for overlap or contradiction. Prefer a correction at the responsible step over another broad top-level rule.
3. Draft the smallest useful change, including trigger, expected behavior and stopping condition. Preserve approved boundaries and successful counterexamples.
4. Track accepted, rejected and deferred suggestions separately, with reasons. Do not reapply a rejected preference under different wording.
5. When the change is authorized, update local instructions and references, then exercise a realistic failure scenario and a nearby valid scenario. Structural validation is not proof of decision quality.

Output: an evidenced proposal or a validated local revision, according to the task's authority. Source attribution remains historical; local improvements do not need an upstream repository update or synchronization. Do not promote one test success into a broad reliability claim.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
