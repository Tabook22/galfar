import type { BilingualText } from "../api/settings";

interface Props {
  label: string;
  value: BilingualText;
  onChange: (value: BilingualText) => void;
  enLabel: string;
  arLabel: string;
  enPlaceholder?: string;
  arPlaceholder?: string;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  required?: boolean;
}

export default function BilingualField({
  label,
  value,
  onChange,
  enLabel,
  arLabel,
  enPlaceholder,
  arPlaceholder,
  disabled = false,
  multiline = false,
  rows = 3,
  required = false,
}: Props) {
  const Input = multiline ? "textarea" : "input";

  return (
    <fieldset className="bilingual-field">
      <legend>
        {label}
        {required && " *"}
      </legend>
      <div className="bilingual-field-grid">
        <label className="edit-field">
          <span>{enLabel}</span>
          <Input
            {...(multiline ? { rows } : {})}
            value={value.en}
            onChange={(e) => onChange({ ...value, en: e.target.value })}
            placeholder={enPlaceholder}
            disabled={disabled}
            dir="ltr"
          />
        </label>
        <label className="edit-field">
          <span>{arLabel}</span>
          <Input
            {...(multiline ? { rows } : {})}
            value={value.ar}
            onChange={(e) => onChange({ ...value, ar: e.target.value })}
            placeholder={arPlaceholder}
            disabled={disabled}
            dir="rtl"
          />
        </label>
      </div>
    </fieldset>
  );
}
