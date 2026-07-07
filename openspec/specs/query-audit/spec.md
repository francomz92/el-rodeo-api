# N+1 Query Audit Specification

## Purpose

Detect and eliminate N+1 query patterns in SQLAlchemy repositories where a `list_*` method loads a collection then lazily loads related entities per item, degrading pagination and report performance.

## Requirements

### Requirement: Repository audit of list methods

Every `list_*` repository method that returns a collection of entities with relationships MUST be reviewed for eager-loading gaps. The review MUST check `selectinload` or `joinedload` coverage on all `relationship()` attributes accessed during list iteration.

#### Scenario: Audit detects missing eager load

- GIVEN a `list_animals` method that queries `Animal` and then iterates accessing `animal.type.name`
- WHEN reviewing the query for eager loading
- THEN the review flags `animal.type` as a missing eager load

#### Scenario: Fixed repository uses selectinload

- GIVEN a `list_animals` method with detected N+1 on `animal.type`
- WHEN `selectinload(Animal.type)` is added to the query
- THEN a single query (2 total) replaces the N+1 pattern

### Requirement: Audit report

The system MUST produce an audit report listing each reviewed repository method, its N+1 status (clean / fixed / unfixable), and the fix applied. Zero instances MUST remain unfixed at completion.

#### Scenario: Report documents all reviewed methods

- GIVEN the audit completes
- WHEN inspecting the report
- THEN every `list_*` repository method in the codebase is listed with status
- AND zero methods have status `unfixable`

### Requirement: Zero regression baseline

All 883 existing tests MUST pass after N+1 fixes are applied. Eager loading changes MUST NOT alter the returned data shape or ordering — only the query count.

#### Scenario: Data shape preserved after eager load fix

- GIVEN a repository returning `Animal` entities
- WHEN the queries are equivalent before and after adding `selectinload`
- THEN the returned entity list has the same items, order, and attribute values
