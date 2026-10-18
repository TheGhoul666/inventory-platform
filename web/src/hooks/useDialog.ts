import { useEffect, useId, useRef } from "react";
import { useTranslation } from "react-i18next";

const FOCUSABLE =
  'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

/**
 * Accessible modal behaviour (WCAG 2.1.1, 2.1.2, 2.4.3, 4.1.2):
 * role/aria attributes, Escape to close, focus moves in, Tab is trapped,
 * and focus returns to the trigger on close. Spread `dialogProps` on the overlay
 * element, put `id={titleId}` on the heading and `aria-label={closeLabel}` on the close button.
 */
export function useDialog(onClose: () => void) {
  const ref = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const { t } = useTranslation();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    const node = ref.current;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const focusables = () => Array.from(node?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []);
    (focusables().find((el) => el.tagName !== "BUTTON") ?? focusables()[0] ?? node)?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        closeRef.current();
      } else if (e.key === "Tab") {
        const items = focusables();
        if (items.length === 0) return;
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previouslyFocused?.focus?.();
    };
  }, []);

  return {
    titleId,
    closeLabel: t("a11y.closeDialog"),
    dialogProps: { ref, role: "dialog" as const, "aria-modal": true as const, "aria-labelledby": titleId, tabIndex: -1 },
  };
}
