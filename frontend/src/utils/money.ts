export const CURRENCY_LABELS: Readonly<Record<string, string>> = {
  CNY: "人民币",
  USD: "美元",
};

export function currencyLabel(currency: string): string {
  return CURRENCY_LABELS[currency] ?? currency;
}

export function formatMoney(currency: string, amount: string | number): string {
  const numeric = typeof amount === "number" ? amount : Number(amount);
  if (Number.isNaN(numeric)) {
    return `${currencyLabel(currency)} ${amount}`;
  }
  const formatted = new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric);
  return `${currencyLabel(currency)} ${formatted}`;
}

export function formatAmount(amount: string | number): string {
  const numeric = typeof amount === "number" ? amount : Number(amount);
  if (Number.isNaN(numeric)) {
    return String(amount);
  }
  return new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric);
}

export function amountsList(amounts: Record<string, string> | undefined): Array<{ currency: string; amount: string }> {
  return Object.entries(amounts || {}).map(([currency, amount]) => ({ currency, amount }));
}
