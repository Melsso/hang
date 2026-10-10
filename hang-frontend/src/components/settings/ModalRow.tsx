export default function ModalRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between bg-[#222] rounded-xl p-4">{children}</div>
  );
}
