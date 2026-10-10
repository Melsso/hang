import { useState, useEffect } from "react";
import { getReports, deleteReport } from "../../api/settings";
import ModalRow from "./ModalRow";
import { useToast } from "../global/ToastProvider";

interface ReportedUser {
    first_name: string;
    last_name: string;
    reported_id: number;
    reason: string;
    message: string | null;
    created_at: string;
}

export default function ReportsModal() {
    const [reports, setReports] = useState<ReportedUser[]>([]);
    const { showToast } = useToast();

    useEffect(() => {
        let cancelled = false;
        (async () => {
            const data = await getReports();
            if (cancelled) return;
            if (!data) {
                showToast("Something went wrong, try again later.", "error");
                return;
            }
            setReports(data);
        })();
        return () => { cancelled = true; };
    }, []);

    function formatDate(date: string) {
        return new Date(date).toLocaleString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    return (
        <>
            <h2 className="text-2xl font-bold text-white mb-6">
                Reports
            </h2>

            <div className="space-y-3">
                {reports.map((report) => (
                    <ModalRow key={report.reported_id}>
                        <div>
                            <div className="text-white">
                                {report.first_name} {report.last_name}
                            </div>

                            <div className="text-white/50 text-sm">
                                Reported on {formatDate(report.created_at)}
                            </div>
                        </div>

                        <button
                            className="bg-[#333] px-4 py-2 rounded-lg text-white hover:bg-[#444]"
                            onClick={async () => {
                                const success = await deleteReport(report.reported_id);
                                if (!success) {
                                    showToast("Something went wrong, try again later.", "error");
                                    return;
                                }
                                setReports(prev => prev.filter(r => r.reported_id !== report.reported_id));
                            }}
                        >
                            Delete
                        </button>
                    </ModalRow>
                ))}
            </div>
        </>
    );
}