# Security policy

## What Topoli does and does not do

Topoli runs on your machine. It sends requests only to official public data sources (listed in `LICENCES.md`) and never to a Topoli server. It stores a local cache in `~/.topoli/cache/`. It sends no telemetry. The only network destinations are documented in each adapter's docstring and enforced by the egress test (`tests/regression`).

## Reporting a vulnerability

Please use GitHub's **private vulnerability reporting** on this repository ("Security" tab → "Report a vulnerability"). Do not open a public issue for security problems.

Include: affected version or commit, steps to reproduce, and the impact you see. You will get an acknowledgement within 7 days and a fix or mitigation plan within 30 days for confirmed issues.

## Scope

In scope: code in this repository, the skill's scripts, the generated HTML report and share artefacts (for example, injection of untrusted source data into the report), and the CI workflows.

Out of scope: the availability or correctness of third-party government data sources (report those with the `wrong-finding` template instead).

## Supported versions

Only the latest release and `main` receive security fixes.
