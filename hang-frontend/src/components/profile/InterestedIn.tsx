type Props = {
  value?: string;
  setValue: (value: string) => void;
};

export default function InterestedIn({ value, setValue }: Props) {
  return (
    <div className="flex flex-col gap-2 w-full">
      <label className="text-sm text-white/60">Interested In</label>

      <div className="relative w-full">
        <select
          value={value || ""}
          onChange={(e) => setValue(e.target.value)}
          className="
                        w-full
                        bg-[#222]
                        text-white
                        border border-[rgba(255,255,255,0.2)]
                        rounded-[12px]
                        px-[10px]
                        py-[10px]
                        pr-10
                        leading-[20px]
                        outline-none
                        appearance-none
                    "
        >
          <option value="" disabled>
            Select Interested In
          </option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="everyone">Everyone</option>
        </select>

        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2">
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M5 7.5L10 12.5L15 7.5"
              stroke="rgb(255,255,255, 0.7)"
              strokeWidth="2.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
