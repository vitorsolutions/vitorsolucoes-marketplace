using Acme.Billing.Customers;

namespace Acme.Billing.Invoices;

public sealed class Invoice
{
    public required string Number { get; init; }

    public required Customer Customer { get; init; }

    public DateTime IssuedOn { get; set; }

    public DateTime DueOn { get; init; }

    public decimal Total { get; init; }

    public bool Paid { get; set; }
}
