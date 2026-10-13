# acme-billing

Subscription billing service for the Acme storefront.

## Business rules

- **Coupons** — a coupon can be used up to and including its `valid_until` date. Inactive coupons
  are never accepted.
- **Overdue invoices** — an unpaid invoice has a grace period of 7 days after its due date. The
  subscription is suspended once the grace period has passed.
- **Invoice e-mail** — the customer receives one e-mail when an invoice is issued.
- **Export** — invoices can be exported to CSV for the finance team.

## Layout

```
billing/
├── coupons.py         coupon model and validation
├── customers.py       customer model
├── invoices.py        invoice lifecycle
├── export.py          CSV export
└── notifications.py   outbound e-mail
```

E-mail delivery and persistence are provided by the host application and are not part of this
repository.
