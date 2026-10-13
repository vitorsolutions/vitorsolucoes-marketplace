using System.Globalization;
using System.Text;

namespace Acme.Billing.Invoices;

public sealed class InvoiceExporter
{
    private static readonly string[] Columns = ["Number", "Customer", "IssuedOn", "DueOn", "Total", "Paid"];

    public string ToCsv(IEnumerable<Invoice> invoices)
    {
        var csv = new StringBuilder();
        csv.AppendLine(string.Join(';', Columns));

        foreach (var invoice in invoices)
        {
            csv.AppendLine(string.Join(';',
                invoice.Number,
                invoice.Customer.Name,
                invoice.IssuedOn.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                invoice.DueOn.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                invoice.Total.ToString("F2", CultureInfo.InvariantCulture),
                invoice.Paid ? "yes" : "no"));
        }

        return csv.ToString();
    }
}
