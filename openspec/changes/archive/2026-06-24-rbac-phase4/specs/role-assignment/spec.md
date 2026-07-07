# role-assignment — Specification

## Purpose
Enable OWNER/ADMIN role assignment with protections against self-escalation and last-OWNER demotion.

## Requirements

### Requirement: Role assignment authority

The system MUST allow only ADMIN and OWNER users to promote or demote roles within their tenant. No user MAY self-escalate — registration always sets VIEWER.

#### Scenario: ADMIN promotes a user to EDITOR
- GIVEN an ADMIN user and a VIEWER user in the same tenant
- WHEN the ADMIN assigns role EDITOR to the VIEWER
- THEN the target user's role becomes EDITOR

#### Scenario: VIEWER cannot assign roles
- GIVEN a VIEWER user
- WHEN they attempt to assign any role
- THEN NotPermissionError is raised

#### Scenario: Self-escalation blocked
- GIVEN a user with role VIEWER
- WHEN they attempt to change their own role to ADMIN
- THEN the request is rejected with NotPermissionError

### Requirement: Last-OWNER protection

The system MUST prevent demoting or deleting the last OWNER of a tenant. At least one OWNER MUST remain per tenant at all times.

#### Scenario: Demoting last OWNER blocked
- GIVEN a tenant with exactly one OWNER user
- WHEN an ADMIN attempts to demote that OWNER to EDITOR
- THEN the request is rejected with BusinessValidationError

#### Scenario: Demoting non-last OWNER succeeds
- GIVEN a tenant with two OWNER users
- WHEN an ADMIN demotes one OWNER to EDITOR
- THEN the demotion succeeds and the tenant still has one OWNER
