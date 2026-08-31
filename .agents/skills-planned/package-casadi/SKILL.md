---
name: package-casadi
description: Use when the user asks to install, configure, troubleshoot, or package projects that depend on CasADi.
---

# Package CasADi

Use this skill for dependency and environment tasks involving CasADi in Python, C++, or mixed workflows.

## Goal

Help users set up CasADi reliably and reproducibly across local development and CI environments.

## Workflow

1. Determine language/runtime, OS, package manager, and CasADi version needs.
2. Recommend install steps using the project's existing dependency management approach.
3. Verify import/linking and basic solver functionality.
4. Document reproducible setup and troubleshooting notes.

## Tool Use Guidance

- Prefer pinned versions and lockfiles when supported by the project.
- Avoid mixing package managers unless required.
- Include platform-specific caveats only when they apply.

## Output Requirements

- Provide concrete install/config commands.
- Include a minimal verification snippet for CasADi availability.
- Call out known compatibility or binary-distribution limitations.

