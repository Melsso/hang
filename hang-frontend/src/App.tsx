import { ToastProvider } from "./components/global/ToastProvider";
import AppRoutes from "./routes/index";
import Header from "./components/global/Header";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="global-container">
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </main>
    </div>
  );
}
