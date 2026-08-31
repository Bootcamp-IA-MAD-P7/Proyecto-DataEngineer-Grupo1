# ADR-0007: Accessibility and sustainable delivery

## Status

Accepted for future implemented user-facing and delivery work.

## Context

The project may reach an expert-level user interface and an AWS deployment. These
capabilities must not be treated as decorative additions: they need accessible,
efficient and evidence-based delivery requirements that apply before implementation.

The project adopts WCAG 2.2 AA as a target for implemented user-facing flows, WAI-ARIA
only when native HTML semantics are insufficient, and the W3C Web Sustainability
Guidelines as a reference for planet, people and prosperity. This ADR does not assert
formal WCAG conformance, an environmental certification, a carbon score or an AWS
deployment.

## Decision

### Mandatory when applicable

- Implemented user-facing flows target WCAG 2.2 AA.
- Interfaces support keyboard-only use, visible and logical focus, accessible control
  names, sufficient contrast and errors that can be understood and corrected.
- Semantic headings, landmarks and native controls take priority over ARIA.
- Colour is never the sole carrier of status or meaning. Charts, metrics and status
  indicators have an equivalent textual or tabular alternative.
- Autoplaying media and unnecessary animation are avoided; reduced-motion preferences
  are respected when motion exists.
- A user-facing flow has automated rendered-interface accessibility evidence and a
  documented keyboard-only manual check before merge.
- Work affecting APIs, frontend delivery, Docker or AWS uses the smallest justified
  architecture and dependency set, bounded responses and retention, and avoids
  duplicate work, needless transfer and aggressive polling.

### Conditional requirements

- Advanced widgets, dynamic updates, dialogs, custom controls and charts receive
  screen-reader validation when implemented.
- WAI-ARIA Authoring Practices are applied only when native HTML cannot express the
  required interaction.
- Language declaration and internationalisation requirements apply when the interface
  introduces multi-language content.
- Route or component lazy loading, caching, resource limits and sizing evidence apply
  when the actual complexity or deployment warrants them.

### Future direction and deferred evidence

- The preferred expert-level frontend is React + TypeScript + Vite as a static SPA
  consuming FastAPI. Streamlit remains a fallback only for a constrained demo.
- The intended AWS static-delivery shape is private S3 + CloudFront + OAC. API and
  workers may be independently containerised when a dedicated AWS task approves it.
- No AWS resource is provisioned by this decision.
- SCI may be used later as a measurement methodology only after the project defines a
  boundary, functional unit and measured baseline. No carbon, energy or deployment
  result is fabricated beforehand.

## Consequences

- Applicable future specs must state accessibility and sustainability scope, evidence
  and exclusions.
- Known critical accessibility failures block merge until resolved or explicitly
  re-scoped before implementation.
- Accessibility, privacy, security, maintainability and performance remain
  complementary sustainability concerns; none can be weakened to optimise another.
- The policy does not create a frontend, JavaScript dependency, AWS account, CI tool
  or carbon metric on its own.

## References

- [W3C WCAG 2 Overview](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [W3C WAI-ARIA Overview](https://www.w3.org/WAI/standards-guidelines/aria/)
- [W3C Web Sustainability Guidelines](https://www.w3.org/TR/web-sustainability-guidelines/)
- [Software Carbon Intensity specification](https://sci.greensoftware.foundation/)
