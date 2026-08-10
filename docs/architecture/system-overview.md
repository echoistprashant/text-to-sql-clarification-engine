# System Architecture

## Overview

The Text-to-SQL Clarification Engineer is designed as a controlled workflow
rather than a fully autonomous agent.

The system combines deterministic software components with targeted
LLM-powered components.

## High-Level Flow

User
↓
API / Session
↓
Intent Analysis
↓
Schema Intelligence
↓
Clarification Engineer
↓
Query Planning
↓
SQL Generation
↓
SQL Validation
↓
Safe SQL Execution
↓
Result Validation
↓
Answer Generation
↓
Final Response

## LLM Responsibilities

The LLM may be used for:

- intent interpretation
- ambiguity detection
- clarification generation
- query planning
- SQL generation
- constrained SQL repair
- natural-language answer generation

## Deterministic Responsibilities

Deterministic application code is preferred for:

- API handling
- session management
- database connections
- schema introspection
- SQL parsing
- SQL safety checks
- query limits
- execution timeouts
- authentication
- authorization
- logging
- evaluation

## Core Design Principle

LLM output is treated as untrusted input.

Generated SQL must pass validation and security controls before it can be
executed.

## Cross-Cutting Concerns

The architecture also includes:

- security
- observability
- evaluation
- configuration
- error handling

These concerns apply across the workflow rather than belonging to a single
LLM component.