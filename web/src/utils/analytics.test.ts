import { describe, expect, it } from "vitest";
import { averageRate, dailyConsumption, detectAnomaly, emaSeries, predictedDaysLeft } from "./analytics";

const now = new Date("2026-10-18T12:00:00Z");
const tx = (d: string, q: number, type = "ISSUE") => ({ transaction_type: type, quantity_delta: q, created_at: `${d}T10:00:00Z` });

describe("analytics", () => {
  it("sums only consuming transactions and fills gaps", () => {
    const s = dailyConsumption([tx("2026-10-18", 3), tx("2026-10-18", 2), tx("2026-10-17", 9, "RESTOCK")], 3, now);
    expect(s.map((p) => p.qty)).toEqual([0, 0, 5]);
  });
  it("EMA starts at first value and smooths", () => {
    const e = emaSeries([{ date: "a", qty: 8 }, { date: "b", qty: 0 }]);
    expect(e[0].ema).toBe(8);
    expect(e[1].ema).toBe(6);
  });
  it("predicts depletion", () => {
    expect(predictedDaysLeft(10, 2)).toBe(5);
    expect(predictedDaysLeft(10, 0)).toBeNull();
    expect(averageRate([])).toBe(0);
  });
  it("flags a 7d spike", () => {
    const series = Array.from({ length: 30 }, (_, i) => ({ qty: i >= 23 ? 10 : 0 }));
    expect(detectAnomaly(series, "x").is_anomaly).toBe(true);
    expect(detectAnomaly(series.map(() => ({ qty: 1 })), "x").is_anomaly).toBe(false);
  });
});

import { consumptionRateByItem, sortByUrgency, toStockLevel } from "./analytics";

describe("dashboard stock levels", () => {
  const item = (id: string, qty: number, low = 20, crit = 8) => ({
    id, name: id, sku: id, unit: "pcs", quantity: qty, low_stock_threshold: low, critical_stock_threshold: crit,
  });

  it("computes per-item rate and days left", () => {
    const rates = consumptionRateByItem(
      [
        { item_id: "a", transaction_type: "ISSUE", quantity_delta: 14, created_at: "2026-10-01T00:00:00Z" },
        { item_id: "a", transaction_type: "RESTOCK", quantity_delta: 99, created_at: "2026-10-02T00:00:00Z" },
      ],
      14,
    );
    expect(rates.get("a")).toBe(1);
    expect(toStockLevel(item("a", 10), rates).daysLeft).toBe(10);
    expect(toStockLevel(item("b", 10), rates).daysLeft).toBeNull();
  });

  it("classifies status and sorts the most urgent first", () => {
    const rates = new Map<string, number>();
    const levels = [item("ok", 90), item("low", 15), item("crit", 4)].map((i) => toStockLevel(i, rates));
    expect(levels.map((l) => l.status)).toEqual(["ok", "low", "critical"]);
    expect(sortByUrgency(levels).map((l) => l.id)).toEqual(["crit", "low", "ok"]);
  });
});

import { dailyHealthSeries, lastDelta, netChange } from "./analytics";

describe("dashboard trends", () => {
  const now = new Date("2026-10-18T12:00:00Z");
  const items = [
    { id: "a", quantity: 4, low_stock_threshold: 20, critical_stock_threshold: 8, unit_cost: 10 },
    { id: "b", quantity: 50, low_stock_threshold: 20, critical_stock_threshold: 8, unit_cost: 2 },
  ];

  it("uses before/after quantities for the net change, with a type fallback", () => {
    expect(netChange({ transaction_type: "ISSUE", quantity_delta: 5, quantity_before: 20, quantity_after: 15, created_at: "" })).toBe(-5);
    expect(netChange({ transaction_type: "RESTOCK", quantity_delta: 5, created_at: "" })).toBe(5);
    expect(netChange({ transaction_type: "ISSUE", quantity_delta: 5, created_at: "" })).toBe(-5);
  });

  it("rebuilds earlier days by reversing later movements", () => {
    // 'a' was restocked from 4 to 24 two days ago -> it was critical before, healthy after
    const txns = [{ item_id: "a", transaction_type: "RESTOCK", quantity_delta: 20, quantity_before: 4, quantity_after: 24, created_at: "2026-10-16T09:00:00Z" }];
    const t = dailyHealthSeries(items, txns, 4, now); // 15,16,17,18 Oct
    // end of 15 Oct: a = 4 (critical); end of 16/17/18: a is 24 only if no later movement... current is 4
    expect(t.dates).toEqual(["2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18"]);
    expect(t.critical[3]).toBe(1); // today: a = 4
    expect(t.critical[0]).toBe(1 + 0); // 15 Oct: 4 - (24-4) < 0 clamps to 0 -> critical
    expect(t.ok[3]).toBe(1); // b stays healthy
    expect(t.value[3]).toBe(4 * 10 + 50 * 2);
  });

  it("lastDelta compares today with yesterday", () => {
    expect(lastDelta([1, 1, 3])).toBe(2);
    expect(lastDelta([5])).toBe(0);
  });
});

import { weekOverWeek } from "./analytics";
describe("weekOverWeek", () => {
  it("compares the last 7 days with the previous 7", () => {
    const series = [...Array(7).fill({ qty: 1 }), ...Array(7).fill({ qty: 2.6 })];
    expect(weekOverWeek(series)).toBe(2.6);
    expect(weekOverWeek(Array(14).fill({ qty: 0 }))).toBeNull();
  });
});
