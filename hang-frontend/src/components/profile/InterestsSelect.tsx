import { useMemo } from "react";
import Select from "react-select";
import { interests } from "../../constants/interests";

type Option = {
    value: string;
    label: string;
};

type Props = {
    name?: string;
    value?: string[];
    onChange?: (values: string[]) => void;
};

export default function InterestsSelect({ name = "interests", value = [], onChange }: Props) {
    const options = useMemo<Option[]>(
        () =>
            interests.map((interest) => ({
                value: interest,
                label: interest,
            })),
        []
    );

    const selectedOptions = useMemo(() => {
        return options.filter((opt) => value.includes(opt.value));
    }, [value, options]);

    return (
        <div className="flex flex-col gap-2 w-full">
            <label htmlFor={name} className="text-sm text-white/60">
                Interests
            </label>

            <Select
                inputId={name}
                isMulti
                options={options}
                value={selectedOptions}
                className="w-full"
                classNamePrefix="react-select"
                onChange={(selected) => {
                    const values = (selected || []).map((s) => s.value);
                    onChange?.(values);
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
                    multiValue: (base) => ({
                        ...base,
                        backgroundColor: "#333",
                        borderRadius: "999px",
                    }),
                    multiValueLabel: (base) => ({
                        ...base,
                        color: "white",
                    }),
                    multiValueRemove: (base) => ({
                        ...base,
                        color: "#aaa",
                        ":hover": {
                            backgroundColor: "#444",
                            color: "white",
                        },
                    }),
                    input: (base) => ({
                        ...base,
                        color: "white",
                    }),
                    placeholder: (base) => ({
                        ...base,
                        color: "rgba(255,255,255,0.4)",
                    }),
                }}
            />
        </div>
    );
}