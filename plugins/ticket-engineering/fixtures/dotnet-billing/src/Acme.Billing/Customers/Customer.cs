namespace Acme.Billing.Customers;

public sealed class Customer
{
    public required Guid Id { get; init; }

    public required string Name { get; init; }

    public required string Email { get; init; }

    public bool Suspended { get; set; }
}
