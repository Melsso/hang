import { createContext, useContext, useState, useCallback } from "react";

type ToastType = "info" | "success" | "error";
type Toast = {
    id: number;
    message: string;
    type: ToastType;
};
type ToastContextType = {
    showToast: (
        message: string,
        type?: "info" | "success" | "error"
    ) => void;
};

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const showToast = useCallback((message: string, type: ToastType = "info") => {
        const id = Date.now();
        setToasts((prev) => [...prev, { id, message, type }]);
        setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}

            <div className="fixed top-5 right-5 z-[9999] flex flex-col gap-2">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        className={`
                            px-4 py-3 rounded-lg shadow-lg
                            border animate-fadeIn
                            ${
                                t.type === "error"
                                    ? "bg-[#2d0f12] border-red-500 text-red-200"
                                    : t.type === "success"
                                    ? "bg-[#0f2418] border-green-500 text-green-200"
                                    : "bg-[#222] border-white/10 text-white"
                            }
                        `}
                    >
                        {t.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error("useToast must be used inside ToastProvider");
    return ctx;
}