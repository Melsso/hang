import { useMemo } from "react";
import Select from "react-select";
import { getNames, getCode } from "country-list";

type Option = {
  value: string; // ISO code
  label: string; // country name
};

type Props = {
  name?: string;
  value?: string; // "DE"
  onChange?: (value: string) => void;
};

export default function CountrySelect({ name = "country", value, onChange }: Props) {
  const options = useMemo<Option[]>(
    () =>
      getNames().map((country) => ({
        value: getCode(country) || "",
        label: country,
      })),
    []
  );

  const selectedOption = useMemo(() => {
    if (!value) return null;
    return options.find((o) => o.value === value) || null;
  }, [value, options]);

  return (
    <div className="flex flex-col gap-2 w-full">
      <label htmlFor={name} className="text-sm text-white/60">
        Country
      </label>

      <Select
        inputId={name}
        options={options}
        value={selectedOption}
        isClearable
        className="w-full"
        classNamePrefix="react-select"
        onChange={(selected) => {
          onChange?.(selected?.value || "");
        }}
        styles={{
          control: (base, state) => ({
            ...base,
            backgroundColor: "#222",
            border: state.isFocused
              ? "1px solid rgba(255,255,255,0.4)"
              : "1px solid rgba(255,255,255,0.2)",
            borderRadius: "12px",
            boxShadow: "none",
            padding: "4px 6px",
            color: "white",
          }),
          singleValue: (base) => ({
            ...base,
            color: "white",
          }),
          menu: (base) => ({
            ...base,
            backgroundColor: "#111",
            borderRadius: "12px",
            overflow: "hidden",
          }),
          option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused ? "#222" : "#111",
            color: "white",
            cursor: "pointer",
          }),
          input: (base) => ({
            ...base,
            color: "white",
          }),
          placeholder: (base) => ({
            ...base,
            color: "rgba(255,255,255,0.9)",
          }),
        }}
      />

      <input type="hidden" name={name} value={value || ""} />
    </div>
  );
}
