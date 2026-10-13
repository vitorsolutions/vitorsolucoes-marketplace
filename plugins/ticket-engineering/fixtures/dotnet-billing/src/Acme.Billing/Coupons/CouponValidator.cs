namespace Acme.Billing.Coupons;

public sealed class CouponValidator
{
    public CouponValidationResult Validate(Coupon? coupon, DateTime nowUtc)
    {
        if (coupon is null)
        {
            return CouponValidationResult.NotFound;
        }

        if (!coupon.Active)
        {
            return CouponValidationResult.Inactive;
        }

        if (nowUtc >= coupon.ValidUntil)
        {
            return CouponValidationResult.Expired;
        }

        return CouponValidationResult.Valid;
    }
}

public enum CouponValidationResult
{
    Valid,
    NotFound,
    Inactive,
    Expired
}
