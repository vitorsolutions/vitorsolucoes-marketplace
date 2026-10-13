namespace Acme.Billing.Coupons;

public sealed class Coupon
{
    public required string Code { get; init; }

    public bool Active { get; init; }

    public decimal PercentOff { get; init; }

    /// <summary>
    /// Last date on which the coupon can be used. Stored as a date with the time set to 00:00 UTC.
    /// </summary>
    public DateTime ValidUntil { get; init; }
}
