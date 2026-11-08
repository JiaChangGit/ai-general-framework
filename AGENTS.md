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
- Align intent using available context first; ask about unknowns that change the result, then proceed when understood. Explain technical terms in questions and what each choice changes.
- SVN repository writes, device flashing/erasure, broker connections and order submission require the user's explicit special grant for that action in the current task. A general full-access grant does not cover these actions.
- For changes to this framework's discovery, deployment or update behavior, read `docs/maintenance.md`. Preserve drift checks and recovery while removing unused abstractions and duplicate guidance.
