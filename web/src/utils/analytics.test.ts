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
