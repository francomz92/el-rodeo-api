# Delta for billing/payment

## ADDED Requirements

### Requirement: PaymentReceived event on IPN approval

When the IPN webhook handler processes an APPROVED payment, the system MUST emit a `PaymentReceived` domain event via IEventBus containing the payment_id, tenant_id, and amount. This SHALL happen after the Payment status update and before the use-case returns.

#### Scenario: Event emitted on approval

- GIVEN a valid MP IPN with status=approved for payment_id="pay-123"
- WHEN `PaymentWebhookService.handle_ipn` processes it
- THEN a PaymentReceived event is dispatched with aggregate_id matching the payment's id

#### Scenario: Event NOT emitted on rejection

- GIVEN a valid MP IPN with status=rejected
- WHEN `PaymentWebhookService.handle_ipn` processes it
- THEN no PaymentReceived event is dispatched
