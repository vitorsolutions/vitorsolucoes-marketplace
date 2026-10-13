from dataclasses import dataclass
from datetime import datetime

from billing.customers import Customer
from billing.notifications import InvoiceNotifier

GRACE_PERIOD_DAYS = 7


@dataclass
class Invoice:
    number: str
    customer: Customer
    due_on: datetime
    total: float
    issued_on: datetime | None = None
    paid: bool = False


class InvoiceService:
    def __init__(self, notifier: InvoiceNotifier) -> None:
        self._notifier = notifier

    def issue(self, invoice: Invoice, now_utc: datetime) -> None:
        """Marks the invoice as issued and notifies the customer.

        Called by the host application's billing job.
        """
        invoice.issued_on = now_utc

        self._notifier.send_invoice_issued(invoice)

    def should_suspend(self, invoice: Invoice, now_utc: datetime) -> bool:
        if invoice.paid:
            return False

        days_overdue = (now_utc.date() - invoice.due_on.date()).days

        return days_overdue > GRACE_PERIOD_DAYS

    def apply_suspension(self, invoice: Invoice, now_utc: datetime) -> None:
        if self.should_suspend(invoice, now_utc):
            invoice.customer.suspended = True
