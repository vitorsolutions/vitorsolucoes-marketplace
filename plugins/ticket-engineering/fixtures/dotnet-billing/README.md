# Acme.Billing

Subscription billing service for the Acme storefront.

## Business rules

- **Coupons** — a coupon can be used up to and including its `ValidUntil` date. Inactive coupons
  are never accepted.
- **Overdue invoices** — an unpaid invoice has a grace period of 7 days after its due date. The
  subscription is suspended once the grace period has passed.
- **Invoice e-mail** — the customer receives one e-mail when an invoice is issued.
- **Export** — invoices can be exported to CSV for the finance team.

## Layout

```
src/Acme.Billing/
├── Coupons/         coupon model and validation
├── Customers/       customer model
├── Invoices/        invoice lifecycle and CSV export
└── Notifications/   outbound e-mail
```

E-mail delivery and persistence are provided by the host application and are not part of this
repository.
