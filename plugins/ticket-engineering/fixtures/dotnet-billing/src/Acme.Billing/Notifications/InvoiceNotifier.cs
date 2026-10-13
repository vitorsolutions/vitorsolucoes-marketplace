using Acme.Billing.Invoices;

namespace Acme.Billing.Notifications;

public interface IEmailSender
{
    Task SendAsync(string to, string subject, string body);
}

public sealed class InvoiceNotifier
{
    private readonly IEmailSender _emailSender;

    public InvoiceNotifier(IEmailSender emailSender)
    {
        _emailSender = emailSender;
    }

    public Task SendInvoiceIssuedAsync(Invoice invoice)
    {
        var subject = $"Invoice {invoice.Number} issued";
        var body = $"Hello {invoice.Customer.Name}, your invoice {invoice.Number} is due on {invoice.DueOn:yyyy-MM-dd}.";

        return _emailSender.SendAsync(invoice.Customer.Email, subject, body);
    }
}
