import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { ToastProvider, useToast } from "../../src/components/global/ToastProvider";

function Trigger() {
  const { showToast } = useToast();
  return <button onClick={() => showToast("Saved", "success")}>go</button>;
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("ToastProvider", () => {
  it("shows a toast and removes it after 3 seconds", () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText("go"));
    expect(screen.getByText("Saved")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2999);
    });
    expect(screen.getByText("Saved")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(screen.queryByText("Saved")).not.toBeInTheDocument();
  });

  it("keeps showToast referentially stable across state changes", () => {
    const { result } = renderHook(() => useToast(), { wrapper: ToastProvider });
    const first = result.current.showToast;

    act(() => {
      result.current.showToast("one");
    });

    expect(result.current.showToast).toBe(first);
  });

  it("throws when used outside the provider", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<Trigger />)).toThrow("useToast must be used inside ToastProvider");
  });
});
