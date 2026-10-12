export type RangePreset = "month" | "3m" | "6m" | "year" | "custom";

export type DateRange = {
  date_from: string;
  date_to: string;
};

function iso(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function rangeFromPreset(preset: RangePreset, custom?: DateRange): DateRange {
  const today = new Date();
  const to = iso(today);
  if (preset === "custom" && custom?.date_from && custom?.date_to) {
    return custom;
  }
  if (preset === "month") {
    return { date_from: iso(new Date(today.getFullYear(), today.getMonth(), 1)), date_to: to };
  }
  if (preset === "3m") {
    const from = new Date(today.getFullYear(), today.getMonth() - 2, 1);
    return { date_from: iso(from), date_to: to };
  }
  if (preset === "6m") {
    const from = new Date(today.getFullYear(), today.getMonth() - 5, 1);
    return { date_from: iso(from), date_to: to };
  }
  return { date_from: iso(new Date(today.getFullYear(), 0, 1)), date_to: to };
}

export const RANGE_OPTIONS: Array<{ value: RangePreset; label: string }> = [
  { value: "month", label: "本月" },
  { value: "3m", label: "近3个月" },
  { value: "6m", label: "近6个月" },
  { value: "year", label: "今年" },
  { value: "custom", label: "自定义" },
];
