import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, resetUnauthorizedGuard, setRedirect } from "../../src/api/client";

const redirect = vi.fn();

function stubFetch(status: number) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: status < 300, status, json: async () => ({}) })
  );
}

beforeEach(() => {
  redirect.mockReset();
  setRedirect(redirect);
  resetUnauthorizedGuard();
  window.history.pushState({}, "", "/swipes");
});

afterEach(() => vi.unstubAllGlobals());

describe("apiFetch", () => {
  it("always sends credentials", async () => {
    stubFetch(200);
    await apiFetch("/api/x");
    expect((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].credentials).toBe("include");
  });

  it("redirects to login on 401", async () => {
    stubFetch(401);
    await apiFetch("/api/conversations");
    expect(redirect).toHaveBeenCalledWith("/login?expired=1");
  });

  it("redirects only once for parallel 401s", async () => {
    stubFetch(401);
    await Promise.all([apiFetch("/api/a"), apiFetch("/api/b")]);
    expect(redirect).toHaveBeenCalledTimes(1);
  });

  it("does not treat a failed login as an expired session", async () => {
    stubFetch(401);
    await apiFetch("/api/auth/login", { method: "POST" });
    expect(redirect).not.toHaveBeenCalled();
  });

  it("does not redirect when already on a public page", async () => {
    window.history.pushState({}, "", "/login");
    stubFetch(401);
    await apiFetch("/api/conversations");
    expect(redirect).not.toHaveBeenCalled();
  });

  it("ignores other error statuses", async () => {
    stubFetch(500);
    await apiFetch("/api/conversations");
    expect(redirect).not.toHaveBeenCalled();
  });
});
