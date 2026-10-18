import type { AnomalyResult, EmaPoint } from "@/types";

export interface TxnLike {
  item_id?: string;
  transaction_type?: string;
  type?: string;
  quantity_delta: number | string;
  created_at: string;
}

const DAY_MS = 86_400_000;
const CONSUMING = new Set(["ISSUE", "WRITE_OFF"]);

const dayKey = (iso: string) => new Date(iso).toISOString().slice(0, 10);

/** Units consumed per calendar day (ISSUE / WRITE_OFF only), oldest first, gaps filled with 0. */
export function dailyConsumption(txns: TxnLike[], days: number, now = new Date()): { date: string; qty: number }[] {
  const totals = new Map<string, number>();
  for (const t of txns) {
    if (!CONSUMING.has(t.transaction_type ?? t.type ?? "")) continue;
    const k = dayKey(t.created_at);
    totals.set(k, (totals.get(k) ?? 0) + Math.abs(Number(t.quantity_delta)));
  }
  const out: { date: string; qty: number }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const k = new Date(now.getTime() - i * DAY_MS).toISOString().slice(0, 10);
    out.push({ date: k, qty: totals.get(k) ?? 0 });
  }
  return out;
}

export function emaSeries(series: { date: string; qty: number }[], span = 7): EmaPoint[] {
  const alpha = 2 / (span + 1);
  let prev: number | null = null;
  return series.map(({ date, qty }) => {
    prev = prev === null ? qty : alpha * qty + (1 - alpha) * prev;
    return { date, ema: Math.round(prev * 1000) / 1000 };
  });
}

export function averageRate(series: { qty: number }[]): number {
  return series.length ? series.reduce((s, p) => s + p.qty, 0) / series.length : 0;
}

/** Days until stock hits zero at the given rate; null when there is no consumption. */
export function predictedDaysLeft(quantity: number, rate: number): number | null {
  return rate > 0 ? quantity / rate : null;
}

export function detectAnomaly(series: { qty: number }[], itemId: string): AnomalyResult {
  const rate30 = averageRate(series);
  const rate7 = averageRate(series.slice(-7));
  const ratio = rate30 > 0 ? rate7 / rate30 : 0;
  return {
    item_id: itemId,
    rate_7d: rate7,
    rate_30d: rate30,
    ratio: Math.round(ratio * 100) / 100,
    is_anomaly: rate30 > 0 && ratio >= 2,
  };
}

/** Average units consumed per day, per item, over the last `days` days. */
export function consumptionRateByItem(txns: TxnLike[], days: number): Map<string, number> {
  const totals = new Map<string, number>();
  for (const t of txns) {
    if (!t.item_id || !CONSUMING.has(t.transaction_type ?? t.type ?? "")) continue;
    totals.set(t.item_id, (totals.get(t.item_id) ?? 0) + Math.abs(Number(t.quantity_delta)));
  }
  const rates = new Map<string, number>();
  totals.forEach((total, id) => rates.set(id, total / days));
  return rates;
}

export interface StockLevel {
  id: string;
  name: string;
  sku: string;
  unit: string;
  quantity: number;
  low: number;
  critical: number;
  /** Bar scale: the quantity that fills the bar. */
  scale: number;
  daysLeft: number | null;
  status: "critical" | "low" | "ok";
}

export function toStockLevel(
  item: { id: string; name: string; sku: string; unit?: string; quantity: number | string; low_stock_threshold: number | string; critical_stock_threshold: number | string },
  rates: Map<string, number>,
): StockLevel {
  const quantity = Number(item.quantity);
  const low = Number(item.low_stock_threshold);
  const critical = Number(item.critical_stock_threshold);
  return {
    id: item.id,
    name: item.name,
    sku: item.sku,
    unit: item.unit ?? "",
    quantity,
    low,
    critical,
    scale: Math.max(low * 2.5, quantity, 1),
    daysLeft: predictedDaysLeft(quantity, rates.get(item.id) ?? 0),
    status: quantity <= critical ? "critical" : quantity <= low ? "low" : "ok",
  };
}

/** Items closest to running out first (quantity relative to the low threshold). */
export function sortByUrgency(levels: StockLevel[]): StockLevel[] {
  const urgency = (l: StockLevel) => l.quantity / Math.max(l.low, 1);
  return [...levels].sort((a, b) => urgency(a) - urgency(b));
}
