from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from billing.invoices import Invoice


class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class InvoiceNotifier:
    def __init__(self, email_sender: EmailSender) -> None:
        self._email_sender = email_sender

    def send_invoice_issued(self, invoice: Invoice) -> None:
        subject = f"Invoice {invoice.number} issued"
        body = (
            f"Hello {invoice.customer.name}, your invoice {invoice.number} "
            f"is due on {invoice.due_on:%Y-%m-%d}."
        )

        self._email_sender.send(invoice.customer.email, subject, body)
