# Behavioral test design

Choose the public boundary that expresses the requirement. A test names the initial state, action and externally observable result. Derive expected values from the accepted specification or an independent oracle, not from the implementation's own formula.

A useful regression test fails against the buggy baseline for the intended behavioral reason and passes against the fix. Syntax errors, missing imports and broken fixtures do not establish red. Assertions should discriminate the wrong behavior: a test that also passes with the implementation removed or replaced by a constant needs investigation.

Cover meaningful classes and boundaries rather than mirror every branch. Assert relevant side effects and failures, not incidental helper calls. Keep setup explicit and isolated. New tests follow the approved admission workflow; existing protected assertions are not editable during a repair.
