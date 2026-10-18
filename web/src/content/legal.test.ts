import { describe, expect, it } from "vitest";
import { legalDocs, type LegalKind } from "./legal";

const kinds: LegalKind[] = ["privacy", "terms", "cookies", "accessibility"];

describe("legal documents", () => {
  for (const lang of ["he", "en"]) {
    for (const kind of kinds) {
      it(`${lang}/${kind} has a title and non-empty sections`, () => {
        const doc = legalDocs(lang, kind);
        expect(doc.title.length).toBeGreaterThan(3);
        expect(doc.sections.length).toBeGreaterThan(2);
        for (const s of doc.sections) {
          expect(s.h).toBeTruthy();
          expect(s.p.every((x) => x.trim().length > 0)).toBe(true);
        }
      });
    }
  }

  it("shows a visible placeholder (not made-up data) when business details are unset", () => {
    const text = JSON.stringify(legalDocs("en", "privacy"));
    expect(text).toContain("TO COMPLETE");
    expect(JSON.stringify(legalDocs("he", "privacy"))).toContain("יש להשלים");
  });

  it("states that no third-party analytics is used", () => {
    expect(JSON.stringify(legalDocs("en", "cookies"))).toMatch(/does not use marketing cookies, analytics/);
  });
});
