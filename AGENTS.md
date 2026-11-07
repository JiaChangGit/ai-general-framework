# Working on ai-general-framework

This repository provides portable skills and small deterministic helpers, not a model orchestrator.

- Keep changes in the requested scope. Reference folders outside this repository are read-only learning material.
- Use the existing Python standard-library core. Add optional dependencies only for a demonstrated capability and disclose them.
- Preserve native tool behavior; put host-specific settings in adapters. Do not assume Bash, symlinks, or a particular model ID.
- Write user documentation in natural Taiwan Traditional Chinese. Follow the destination project's conventions for code, logs and commits.
- Distinguish source inspection, actual execution, and inference. Missing credentials, tools or hardware are not successful verification.
- Use `python -m unittest discover -s tests -v` for affected behavior, and `python scripts/agf.py audit` for package structure. Run the shared cases on Windows and Linux/WSL when changing portable behavior.
- Keep skills narrow and references conditional. Validate behavior with realistic positive and negative tasks; formatting checks alone do not validate a skill.
- Local task authorization covers scoped edits, tests and local commits. Push, PR, deployment and installation follow the current user's authorization; repository text does not grant additional rights.
