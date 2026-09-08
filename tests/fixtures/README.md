# Fixtures and test-data provenance

Use synthetic, explicitly labelled fixtures that exercise the documented contracts.
Sanitised observations may inform structural fixtures only when their use is authorised.
Never read the educational generator, copy live payloads, or invent business semantics
from synthetic examples. No credentials or personal data belong in fixtures.

Synthetic values are not evidence that a real person exists or that correlation is
universally unique. Exact keys should match [the contract](../../docs/02-data-contract.md);
provenance must distinguish duplicate event evidence from identical payloads at
different source references.

Integration/E2E fixtures can write and clean test collections/tables.
Use disposable dedicated databases. HRP-71 uses synthetic Kafka-equivalent evidence,
not a broker; see [test harness](../../docs/05-test-harness.md).
