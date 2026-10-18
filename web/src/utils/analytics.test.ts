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
