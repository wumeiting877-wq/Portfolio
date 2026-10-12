export const CHART_SERIES = ["#0f62fe", "#525252", "#0043ce", "#24a148", "#8c8c8c"];

export const CHART_AXIS = "#8c8c8c";
export const CHART_SPLIT = "#e0e0e0";
export const CHART_INK = "#161616";

export function seriesColor(index: number): string {
  return CHART_SERIES[index % CHART_SERIES.length];
}
