from decimal import ROUND_DOWN, Decimal

MONEY_QUANT = Decimal("0.01")
AMOUNT_QUANT = Decimal("0.0001")
RATIO_QUANT = Decimal("0.000001")


def to_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_amount(value: Decimal | int | str) -> Decimal:
    return to_decimal(value).quantize(AMOUNT_QUANT)


def quantize_money(value: Decimal | int | str) -> Decimal:
    return to_decimal(value).quantize(MONEY_QUANT)


def quantize_ratio(value: Decimal | int | str) -> Decimal:
    return to_decimal(value).quantize(RATIO_QUANT)


def amounts_equal(left: Decimal, right: Decimal) -> bool:
    return quantize_amount(left) == quantize_amount(right)


def split_equal(total: Decimal, count: int) -> list[Decimal]:
    if count <= 0:
        raise ValueError("split count must be positive")
    quantized = quantize_money(total)
    base = (quantized / count).quantize(MONEY_QUANT, rounding=ROUND_DOWN)
    amounts = [base] * count
    remainder = quantized - sum(amounts)
    index = 0
    while remainder > 0:
        amounts[index] += MONEY_QUANT
        remainder -= MONEY_QUANT
        index += 1
    return amounts


def split_by_ratio(total: Decimal, ratios: list[Decimal]) -> list[Decimal]:
    if not ratios:
        raise ValueError("ratios required")
    quantized = quantize_money(total)
    ratio_sum = sum((to_decimal(item) for item in ratios), Decimal("0"))
    if ratio_sum <= 0:
        raise ValueError("ratio sum must be positive")
    amounts: list[Decimal] = []
    allocated = Decimal("0.00")
    for index, ratio in enumerate(ratios):
        if index == len(ratios) - 1:
            amounts.append(quantize_money(quantized - allocated))
        else:
            part = quantize_money(quantized * to_decimal(ratio) / ratio_sum)
            amounts.append(part)
            allocated += part
    return amounts
