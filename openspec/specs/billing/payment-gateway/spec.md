# Billing — Payment Gateway Specification

## Purpose

Defines MercadoPago Checkout Pro integration: preference creation, IPN webhook handling, and Celery billing cycle tasks.

## Requirements

### Requirement: MercadoPagoService.create_checkout_preference

The system MUST create an MP Checkout Pro preference via `POST https://api.mercadopago.com/checkout/preferences` and return the `init_point` URL. The preference body SHALL contain: `items[0]` with `title="Plan {plan.name} - El Rodeo"`, `unit_price=plan.price_monthly`, `quantity=1`, `currency_id="ARS"`; `external_reference` set to `"{tenant_id}:{plan_type}"`; `back_urls` for success/failure/pending; `notification_url` set to `settings.MP_WEBHOOK_URL`.

#### Scenario: Successful preference creation

- GIVEN a tenant with id `uuid-1` selects PRO plan (price_monthly=15.00)
- WHEN `create_checkout_preference(pro_plan, uuid-1, PlanType.PRO)` is called
- THEN an httpx POST is sent to MP with Bearer token
- AND the returned `init_point` URL is returned to the caller

#### Scenario: MP API error propagates

- GIVEN MP returns 400 or 401
- WHEN `create_checkout_preference` is called
- THEN the error is mapped to a `MercadoPagoError` domain exception
- AND no preference is created

### Requirement: MercadoPagoService.validate_webhook

The system MUST validate incoming IPN requests using MercadoPago x-signature HMAC-SHA256. The `x-request-id` header and `data.id` query param SHALL be concatenated with a period, HMAC-signed with `MP_WEBHOOK_SECRET`, and compared against the `x-signature` header value after stripping the `ts=` and `v1=` prefixes.

#### Scenario: Valid signature passes

- GIVEN `x-signature="ts=123456|v1=abc123def"`, `x-request-id="req-1"`, `data.id="pay-1"`, and `MP_WEBHOOK_SECRET="s3cret"`
- WHEN `validate_webhook("ts=123456|v1=abc123def", "req-1", "pay-1")` is called
- THEN the computed HMAC matches `abc123def` and validation returns True

#### Scenario: Invalid signature rejects

- GIVEN a mangled x-signature
- WHEN `validate_webhook` is called
- THEN validation returns False

### Requirement: PaymentWebhookService.handle_ipn

The system MUST process incoming MP IPN notifications. For `topic=payment`, it SHALL fetch the payment details from MP, create/update the Payment record, and transition the associated subscription status. The handler SHALL return HTTP 200 within 22 seconds and MAY defer processing to a background task.

#### Scenario: IPN for approved payment

- GIVEN an IPN with topic=payment and id="pay-1"
- WHEN `handle_ipn("payment", "pay-1")` is called
- THEN MercadoPagoService.get_payment is called to fetch payment details
- AND a Payment record is created with status=APPROVED
- AND the subscription status transitions to ACTIVE

#### Scenario: IPN for rejected payment

- GIVEN an IPN with topic=payment and id="pay-2"
- WHEN the MP payment status is "rejected"
- THEN Payment status is REJECTED
- AND subscription status becomes PAST_DUE

### Requirement: Celery monthly billing task

The system MUST schedule a Celery periodic task (`monthly_billing_task`) that queries all ACTIVE subscriptions approaching their `current_period_end`, creates a new MP Checkout Pro preference for each, and logs the result. This task SHALL run daily via Celery Beat.

#### Scenario: Monthly preference for active subscription

- GIVEN an ACTIVE subscription with current_period_end in 3 days
- WHEN `monthly_billing_task` runs
- THEN a new MP preference is created via `MercadoPagoService.create_checkout_preference`
- AND the new `mp_preference_id` is stored on the subscription
- AND the task logs the preference URL

### Requirement: Celery trial expiration task

The system MUST schedule a Celery periodic task (`expire_trials_task`) that queries all TRIAL subscriptions past `trial_end`, sets their status to EXPIRED, and sets the tenant `plan_id` to FREE.

#### Scenario: Expired trial downgrades to FREE

- GIVEN a TRIAL subscription with trial_end=7 days ago
- WHEN `expire_trials_task` runs
- THEN subscription status becomes EXPIRED
- AND tenant plan_id is set to FREE
