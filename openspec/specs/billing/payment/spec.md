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
