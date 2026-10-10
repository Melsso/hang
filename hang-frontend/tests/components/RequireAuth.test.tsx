import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../../src/api/auth", () => ({ getSession: vi.fn() }));

import { getSession } from "../../src/api/auth";
import RequireAuth from "../../src/components/global/RequireAuth";

function renderGuarded() {
  return render(
    <MemoryRouter initialEntries={["/swipes"]}>
      <Routes>
        <Route path="/login" element={<div>login page</div>} />
        <Route element={<RequireAuth />}>
          <Route path="/swipes" element={<div>private page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.mocked(getSession).mockReset();
});

describe("RequireAuth", () => {
  it("shows a loading state while the session is checked", async () => {
    vi.mocked(getSession).mockResolvedValue({ authenticated: true });
    renderGuarded();

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(await screen.findByText("private page")).toBeInTheDocument();
  });

  it("renders the private route when authenticated", async () => {
    vi.mocked(getSession).mockResolvedValue({ authenticated: true, user_id: 1 });
    renderGuarded();

    expect(await screen.findByText("private page")).toBeInTheDocument();
  });

  it("redirects to /login when not authenticated", async () => {
    vi.mocked(getSession).mockResolvedValue({ authenticated: false });
    renderGuarded();

    expect(await screen.findByText("login page")).toBeInTheDocument();
    expect(screen.queryByText("private page")).not.toBeInTheDocument();
  });

  it("redirects to /login when the session request fails", async () => {
    vi.mocked(getSession).mockResolvedValue(null);
    renderGuarded();

    expect(await screen.findByText("login page")).toBeInTheDocument();
  });
});
