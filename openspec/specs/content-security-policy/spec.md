# Content Security Policy Specification — Expanded Directives

## Purpose

Mitigate XSS and data injection attacks by expanding CSP directives beyond `default-src 'self'` to include `script-src`, `style-src`, `img-src`, `connect-src`, and `font-src`.

## Requirements

### Requirement: Expanded CSP directives in security headers

The system MUST include `script-src`, `style-src`, `img-src`, `connect-src`, and `font-src` in the `Content-Security-Policy` header, in addition to `default-src`. Each directive MUST be configurable via settings with secure defaults.

#### Scenario: CSP header contains expanded directives

- GIVEN a response from any endpoint
- WHEN inspecting the `Content-Security-Policy` header
- THEN the header includes `default-src`, `script-src`, `style-src`, `img-src`, `connect-src`, and `font-src`

#### Scenario: CSP configurable per environment

- GIVEN `CSP_SCRIPT_SRC="'self' https://trusted.cdn.com"` in settings
- WHEN inspecting the CSP header
- THEN `script-src` includes `'self'` and `https://trusted.cdn.com`

#### Scenario: Strict CSP in production

- GIVEN `ENVIRONMENT=production`
- WHEN inspecting the CSP header
- THEN `script-src` is `'self'` and `style-src` is `'self'`
