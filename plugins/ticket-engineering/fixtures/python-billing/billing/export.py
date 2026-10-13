import csv
import io
from collections.abc import Iterable

from billing.invoices import Invoice

COLUMNS = ["Number", "Customer", "IssuedOn", "DueOn", "Total", "Paid"]


def invoices_to_csv(invoices: Iterable[Invoice]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(COLUMNS)

    for invoice in invoices:
        writer.writerow(
            [
                invoice.number,
                invoice.customer.name,
                invoice.issued_on.strftime("%Y-%m-%d") if invoice.issued_on else "",
                invoice.due_on.strftime("%Y-%m-%d"),
                f"{invoice.total:.2f}",
                "yes" if invoice.paid else "no",
            ]
        )

    return buffer.getvalue()
