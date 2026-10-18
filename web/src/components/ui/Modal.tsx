import React from "react";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useDialog } from "@/hooks/useDialog";
import { cn } from "@/utils/cn";

/** Shared dialog shell: Escape closes, focus is trapped and returned, labelled by its title. */
export function Modal({
  title,
  onClose,
  size = "md",
  children,
}: {
  title: React.ReactNode;
  onClose: () => void;
  size?: "md" | "lg";
  children: React.ReactNode;
}) {
  const dialog = useDialog(onClose);
  return (
    <div {...dialog.dialogProps} className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <div className={cn("card w-full p-6", size === "lg" ? "max-w-lg" : "max-w-md")}>
        <div className="mb-4 flex items-center justify-between gap-3">
          <h3 id={dialog.titleId} className="text-xl text-ink">{title}</h3>
          <button
            type="button"
            aria-label={dialog.closeLabel}
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 transition-colors hover:bg-surface-700 hover:text-ink"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Cancel / confirm footer. `confirmClass` recolours the confirm pill; a class containing
 *  `cursor-not-allowed` means "not valid yet" and truly disables the button. */
export function ModalActions({
  onClose,
  onConfirm,
  pending,
  label,
  confirmClass = "btn-primary",
}: {
  onClose: () => void;
  onConfirm: () => void;
  pending: boolean;
  label: string;
  confirmClass?: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="mt-6 flex gap-3">
      <button type="button" onClick={onClose} className="btn-secondary flex-1 px-4 py-2 text-sm font-medium">
        {t("common.cancel")}
      </button>
      <button
        type="button"
        onClick={onConfirm}
        disabled={pending || confirmClass.includes("cursor-not-allowed")}
        className={cn(
          "flex-1 rounded-full px-4 py-2 text-sm font-semibold text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50",
          confirmClass
        )}
      >
        {pending ? t("common.processing") : label}
      </button>
    </div>
  );
}
