---
name: code-rust
description: Use when the user asks for Rust code implementation, debugging, refactoring, performance tuning, or crate setup help.
---

# Code Rust

Use this skill when the request is mainly about authoring or improving Rust code.

## Goal

Deliver idiomatic, safe Rust solutions with clear ownership, error handling, and testability.

## Workflow

1. Confirm expected behavior, API shape, and constraints.
2. Implement or update Rust code with strong type and lifetime correctness.
3. Add or adjust tests if test infrastructure exists.
4. Run available Cargo checks and report outcomes.

## Tool Use Guidance

- Prefer existing crates and repository patterns before introducing dependencies.
- Preserve backward compatibility unless the user asks for breaking changes.
- Surface tradeoffs around performance, memory, and ergonomics.

## Output Requirements

- Provide compile-ready Rust code.
- Include commands needed to build/test when relevant.
- Note any assumptions, risks, or open questions.

