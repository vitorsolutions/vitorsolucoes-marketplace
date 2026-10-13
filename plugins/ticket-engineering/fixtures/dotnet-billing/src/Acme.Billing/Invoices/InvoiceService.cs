using Acme.Billing.Notifications;

namespace Acme.Billing.Invoices;

public sealed class InvoiceService
{
    public const int GracePeriodDays = 7;

    private readonly InvoiceNotifier _notifier;

    public InvoiceService(InvoiceNotifier notifier)
    {
        _notifier = notifier;
    }

    /// <summary>
    /// Marks the invoice as issued and notifies the customer. Called by the host application's
    /// billing job.
    /// </summary>
    public async Task IssueAsync(Invoice invoice, DateTime nowUtc)
    {
        invoice.IssuedOn = nowUtc;

        await _notifier.SendInvoiceIssuedAsync(invoice);
    }

    public bool ShouldSuspend(Invoice invoice, DateTime nowUtc)
    {
        if (invoice.Paid)
        {
            return false;
        }

        var daysOverdue = (nowUtc.Date - invoice.DueOn.Date).Days;

        return daysOverdue > GracePeriodDays;
    }

    public void ApplySuspension(Invoice invoice, DateTime nowUtc)
    {
        if (ShouldSuspend(invoice, nowUtc))
        {
            invoice.Customer.Suspended = true;
        }
    }
}
