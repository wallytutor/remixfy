---
name: agent-openfoam
description: Use when the user needs OpenFOAM case setup, solver selection, meshing, runtime troubleshooting, or post-processing guidance.
---

# Agent OpenFOAM

Use this skill when requests involve creating, debugging, or improving OpenFOAM workflows.

## Goal

Help users produce stable, reproducible OpenFOAM simulations with appropriate solver and case configuration choices.

## Workflow

1. Confirm physics, geometry, turbulence/compressibility assumptions, and accuracy targets.
2. Select solver and configure case dictionaries, boundary conditions, and numerics.
3. Validate mesh quality, initialization, convergence behavior, and residual trends.
4. Recommend post-processing checks and iterate on stability/accuracy issues.

## Tool Use Guidance

- Prefer adapting verified tutorial cases over building from scratch.
- Keep dictionary changes minimal and version-compatible.
- Distinguish convergence issues from setup/physics mismatch.

## Output Requirements

- Provide concrete case-edit guidance with file-level references when possible.
- Include sanity checks for mesh, timestep/Courant number, and boundary consistency.
- Note potential stability risks and mitigation steps.
