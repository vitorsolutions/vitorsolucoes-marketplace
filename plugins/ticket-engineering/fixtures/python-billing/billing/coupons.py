from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CouponValidation(Enum):
    VALID = "valid"
    NOT_FOUND = "not_found"
    INACTIVE = "inactive"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Coupon:
    code: str
    active: bool
    percent_off: float
    # Last date on which the coupon can be used. Stored as a date with the time set to 00:00 UTC.
    valid_until: datetime


def validate_coupon(coupon: Coupon | None, now_utc: datetime) -> CouponValidation:
    if coupon is None:
        return CouponValidation.NOT_FOUND

    if not coupon.active:
        return CouponValidation.INACTIVE

    if now_utc >= coupon.valid_until:
        return CouponValidation.EXPIRED

    return CouponValidation.VALID
