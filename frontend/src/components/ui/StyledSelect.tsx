"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

export type StyledSelectOption = { value: string; label: string };

export function StyledSelect({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  disabled = false,
  description,
  required = false,
}: {
  id?: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: StyledSelectOption[];
  placeholder?: string;
  disabled?: boolean;
  description?: string;
  required?: boolean;
}) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const listId = `${selectId}-list`;
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const items = useMemo(
    () => [{ value: "", label: placeholder ?? "Select" }, ...options],
    [options, placeholder],
  );
  const selected = items.find((item) => item.value === value) ?? items[0];

  useEffect(() => {
    const onDoc = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    const index = Math.max(0, items.findIndex((item) => item.value === value));
    setActive(index);
  }, [items, value]);

  const choose = (next: string) => {
    onChange(next);
    setOpen(false);
  };

  return (
    <div ref={rootRef} className="relative text-sm">
      <label htmlFor={selectId} className="block font-medium text-[var(--navy)]">
        {label}
        {required ? <span className="ml-1 text-[var(--danger)]">Required</span> : null}
      </label>
      {description ? <p className="mt-1 text-xs text-[var(--muted)]">{description}</p> : null}
      <button
        id={selectId}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-haspopup="listbox"
        disabled={disabled}
        className="svk-select mt-1 text-left"
        onClick={() => !disabled && setOpen((current) => !current)}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setOpen(true);
            setActive((current) => Math.min(items.length - 1, current + 1));
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive((current) => Math.max(0, current - 1));
          }
          if (event.key === "Enter" && open) {
            event.preventDefault();
            choose(items[active]?.value ?? "");
          }
          if (event.key === "Escape") {
            setOpen(false);
          }
        }}
      >
        <span className="flex items-center justify-between gap-2">
          <span>{selected?.label}</span>
          <span className="svk-nav-chevron text-[var(--navy)]" aria-hidden>
            ▾
          </span>
        </span>
      </button>
      {open ? (
        <ul id={listId} role="listbox" className="svk-select-menu">
          {items.map((item, index) => (
            <li key={`${item.value || "empty"}-${item.label}`}>
              <button
                type="button"
                role="option"
                aria-selected={item.value === value}
                data-active={index === active}
                className="svk-select-option"
                onMouseEnter={() => setActive(index)}
                onClick={() => choose(item.value)}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
