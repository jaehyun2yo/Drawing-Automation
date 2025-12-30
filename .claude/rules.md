# Project Development Rules

## 1. Architecture: Clean Architecture

Follow Clean Architecture principles strictly:

- **Domain Layer (Core)**: Business entities and use cases. No external dependencies.
- **Application Layer**: Use cases, interfaces, and application logic.
- **Infrastructure Layer**: External implementations (DB, APIs, frameworks).
- **Presentation Layer**: UI and controllers.

### Dependency Rule
Dependencies must point inward only. Inner layers must never depend on outer layers.

```
Presentation → Application → Domain
Infrastructure → Application → Domain
```

### Directory Structure Example
```
src/
├── domain/           # Entities, value objects, domain services
├── application/      # Use cases, ports (interfaces)
├── infrastructure/   # Repositories, external services, adapters
└── presentation/     # UI, controllers, routes
```

## 2. Test-Driven Development (TDD)

Apply TDD rigorously for all features:

### Red-Green-Refactor Cycle
1. **Red**: Write a failing test first
2. **Green**: Write minimum code to pass the test
3. **Refactor**: Improve code while keeping tests green

### Testing Requirements
- Unit tests for all domain logic
- Integration tests for infrastructure components
- E2E tests for critical user flows
- Maintain high test coverage (target: 80%+)

### Test Organization
```
tests/
├── unit/
├── integration/
└── e2e/
```

## 3. Skills & Agent Utilization

Leverage available skills and agents effectively:

- Use **specialized agents** for complex multi-step tasks
- Invoke **skills** before starting any relevant task
- Use **Task tool** with appropriate subagent types for:
  - Code exploration (`Explore`)
  - Architecture planning (`Plan`)
  - Feature development (`feature-dev:*`)
  - Code review (`code-review:*`)

## 4. Problem Solving: Root Cause Analysis

Always seek fundamental solutions:

### Approach
1. **Understand** the problem deeply before coding
2. **Identify** the root cause, not just symptoms
3. **Design** a solution that addresses the core issue
4. **Implement** with proper abstractions
5. **Verify** the solution prevents recurrence

### Avoid
- Quick fixes that mask underlying issues
- Band-aid solutions without understanding
- Workarounds that create technical debt

## 5. Response Language

**Respond in Korean (한국어)** for all communications with the user.
