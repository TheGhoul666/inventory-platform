import React, { useId } from "react";

/** Form field with a label programmatically tied to its control (WCAG 1.3.1 / 3.3.2). */
export function Field({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  const id = useId();
  let wired = false;
  const content = React.Children.map(children, (child) => {
    if (
      !wired &&
      React.isValidElement<{ id?: string }>(child) &&
      (child.type === "input" || child.type === "select" || child.type === "textarea")
    ) {
      wired = true;
      return React.cloneElement(child, { id: child.props.id ?? id });
    }
    return child;
  });
  return (
    <div>
      <label htmlFor={id} className="text-sm text-slate-300 block mb-1">
        {label}
      </label>
      {content}
    </div>
  );
}
