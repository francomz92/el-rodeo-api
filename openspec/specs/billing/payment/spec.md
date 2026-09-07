# Billing — Payment Specification

## Purpose

Defines the Payment entity, lifecycle mapping from MercadoPago IPN, and the repository port for payment history queries.

## Requirements

### Requirement: Payment entity

The system MUST define a Payment dataclass with: `id: UUID`, `tenant_id: UUID`, `subscription_id: UUID`, `mp_payment_id: str`, `mp_preference_id: str`, `status: PaymentStatus`, `amount: Decimal`, `currency: str` (default "ARS"), `description: str | None`, `payment_method: PaymentMethod | None`, `installments: int | None`, `paid_at: datetime | None`, `created_at: datetime`, `updated_at: datetime`.

#### Scenario: Payment created from webhook

- GIVEN a valid MP IPN notification with payment_id="12345"
- WHEN `PaymentWebhookService.handle_ipn` processes the notification
- THEN a Payment is created with mp_payment_id="12345" and status=PENDING

#### Scenario: Duplicate mp_payment_id is rejected

- GIVEN a Payment with mp_payment_id="12345" already exists
- WHEN a second IPN with the same mp_payment_id arrives
- THEN no duplicate Payment is created (idempotent)

### Requirement: PaymentStatus enum

The system MUST define `PaymentStatus` as a StrEnum with values: `PENDING`, `APPROVED`, `REJECTED`, `REFUNDED`, `CANCELLED`, `CHARGED_BACK`.

#### Scenario: Payment approved activates subscription

- GIVEN a Payment with status=PENDING
- WHEN the IPN delivers status=approved
- THEN Payment.status becomes APPROVED
- AND the associated subscription status becomes ACTIVE

#### Scenario: Payment rejected flags PAST_DUE

- GIVEN a Payment with status=PENDING
- WHEN the IPN delivers status=rejected
- THEN Payment.status becomes REJECTED
- AND the associated subscription status becomes PAST_DUE

### Requirement: PaymentMethod value object

The system MUST define a PaymentMethod dataclass with: `card_brand: str | None`, `payment_type_id: str | None`. It SHALL be extracted from MP payment response fields `payment_method_id` and `payment_type_id`.

#### Scenario: Credit card payment method

- GIVEN an MP payment with `payment_method_id="visa"` and `payment_type_id="credit_card"`
- WHEN the payment webhook is processed
- THEN Payment.payment_method contains `card_brand="visa"`, `payment_type_id="credit_card"`

### Requirement: IPaymentRepository port

The system MUST define `IPaymentRepository` with: `create(payment) -> Payment`, `get_by_id(id) -> Payment | None`, `get_by_tenant(tenant_id, limit, offset) -> list[Payment]`, `get_by_mp_payment_id(mp_payment_id) -> Payment | None`, `save(payment) -> Payment`. All methods are async.

#### Scenario: Payment lookup by MP ID

- GIVEN a Payment with mp_payment_id="12345"
- WHEN `get_by_mp_payment_id("12345")` is called
- THEN the correct Payment is returned

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

### Requirement: Payment confirmation email on APPROVED

On APPROVED payment, the system MUST send a confirmation email to the tenant owner. The handler SHALL resolve the recipient via `IUserRepository.list(tenant_id, role=OWNER)`, returning the first owner's email. The email subject MUST be `"Pago confirmado - El Rodeo"`. The body MUST include: amount paid, payment date, plan type, next billing date, and an invoice/receipt link.

The handler MUST catch all exceptions so a failure NEVER crashes the event dispatch.

#### Scenario: Confirmation email sent to tenant owner

- GIVEN a PaymentReceived event for an APPROVED payment with `payment_id="pay-123"`, `tenant_id="t1"`, `amount=Decimal("1500.00")`
- WHEN `PaymentConfirmationEmailHandler` processes the event
- THEN the handler resolves the tenant owner via `IUserRepository.list(tenant_id="t1", role=OWNER)` returning a user with `email="owner@example.com"`
- AND an email with subject `"Pago confirmado - El Rodeo"` is sent to `"owner@example.com"`
- AND the email body includes the amount paid, payment date, plan type, next billing date, and invoice link

#### Scenario: No email for non-APPROVED payment

- GIVEN a PaymentReceived event for a payment with `status=REJECTED`
- WHEN `PaymentConfirmationEmailHandler` processes the event
- THEN no email is sent
- AND the handler returns without side effects

#### Scenario: Owner not found logs warning and skips

- GIVEN a PaymentReceived event for an APPROVED payment
- WHEN `IUserRepository.list(tenant_id, role=OWNER)` returns an empty list
- THEN the handler logs a warning with the tenant_id
- AND no email is sent
- AND the handler does NOT propagate the error

#### Scenario: All Celery retries exhausted logs error

- GIVEN a PaymentReceived event for an APPROVED payment
- WHEN `IEmailNotifier.send` raises an exception on all 3 Celery retries with exponential backoff
- THEN the handler catches the final failure
- AND an error is logged with the payment_id and exception details
- AND the event dispatch continues without crashing

### Requirement: Handle subscription_preapproval webhook topic

When `PaymentWebhookService.handle_ipn` receives `topic=subscription_preapproval`, the system MUST fetch the subscription from MP via `IPaymentGateway.get_subscription(id)`, find the local subscription by `external_reference` or `payer_email`, and update `mp_subscription_id`, `status`, `next_billing_date`, and `billing_date` on the local entity. If no local subscription matches, the system SHALL log a warning and skip.

#### Scenario: subscription_preapproval processed

- GIVEN a valid IPN with `topic=subscription_preapproval` and `id="preapp-123"`
- WHEN `handle_ipn` dispatches to the subscription_preapproval handler
- THEN `IPaymentGateway.get_subscription("preapp-123")` is called
- AND the local subscription is found by `external_reference`
- AND `mp_subscription_id` is set to "preapp-123"
- AND subscription status is updated from MP's response
- AND `next_billing_date` and `billing_date` are synced from MP

#### Scenario: Unknown subscription_preapproval skipped

- GIVEN a valid IPN with `topic=subscription_preapproval` and `id="preapp-unknown"`
- WHEN the handler cannot match a local subscription by external_reference or payer_email
- THEN a warning is logged with the MP subscription ID
- AND no local state is modified

### Requirement: Handle subscription_authorized_payment webhook topic

When `PaymentWebhookService.handle_ipn` receives `topic=subscription_authorized_payment`, the system MUST fetch the authorized payment via `IPaymentGateway.get_authorized_payment(id)`, create a Payment record with the associated `payment_id`, and activate the subscription. The `mp_payment_id` unique constraint SHALL provide idempotency against dual `subscription_authorized_payment` + `payment` notifications for the same charge.

#### Scenario: subscription_authorized_payment creates payment

- GIVEN a valid IPN with `topic=subscription_authorized_payment` and `id="auth-pay-456"`
- WHEN `handle_ipn` dispatches to the authorized_payment handler
- THEN `IPaymentGateway.get_authorized_payment("auth-pay-456")` is called
- AND a Payment is created with the associated `payment_id` as `mp_payment_id`
- AND the subscription status transitions to ACTIVE
- AND `next_billing_date` is updated from the authorized payment

#### Scenario: Duplicate subscription_authorized_payment is idempotent

- GIVEN a Payment with `mp_payment_id="pay-789"` already exists from a prior `subscription_authorized_payment`
- WHEN a second `subscription_authorized_payment` arrives for the same `payment_id`
- THEN no duplicate Payment is created
- AND subscription status is NOT changed again (idempotent)

#### Scenario: Dual notification (authorized_payment + payment) is idempotent

- GIVEN MP sends BOTH `subscription_authorized_payment` and `payment` for the same charge with `mp_payment_id="pay-789"`
- WHEN both webhooks arrive (in any order)
- THEN only one Payment record is created
- AND subscription status transitions to ACTIVE exactly once

### Requirement: Unknown webhook topic logged

When `PaymentWebhookService.handle_ipn` receives a topic that is not `payment`, `merchant_order`, `subscription_preapproval`, or `subscription_authorized_payment`, the system MUST log a warning with the unknown topic and skip processing.

#### Scenario: Unknown topic logged

- GIVEN an IPN with `topic=unknown_topic`
- WHEN `handle_ipn` processes it
- THEN a warning is logged with the topic name
- AND no state is modified
