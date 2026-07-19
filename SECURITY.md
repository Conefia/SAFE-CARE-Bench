# Security and Disclosure Policy

## Reporting a concern

Email **dev@conefia.com**. Do not open a public issue for anything in the categories below.

Report privately if you find:

- Any content in this repository that identifies a specific production deployment, client, or patient
- Any real (non-synthetic) data
- Credentials, endpoints, keys, or deployment configuration
- A defect in the judge prompts or scoring anchors that would systematically misreport safety performance

We aim to acknowledge within 5 business days.

## Scope note

This repository contains no executable service, no network listener, and no credential store. The realistic risk surface is **information disclosure** and **evaluation validity**, not remote exploitation. Both are treated as security concerns here.

## Evaluation validity is a safety issue

A benchmark that reports a healthcare agent as safe when it is not causes downstream harm. If you identify a scoring anchor, judge prompt, or ablation configuration that produces systematically optimistic safety results, report it under this policy. It will be handled with the same seriousness as a disclosure issue.

## Using this benchmark

Passing scores here do not certify any system as safe to deploy. Results are technical performance within a tested scenario boundary. Deployment decisions require qualified clinical, legal, and regulatory review.

© 2026 Conefia.
