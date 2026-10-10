import { afterEach, describe, expect, it, vi } from "vitest";
import { getSession, login, logout, register } from "../../src/api/auth";

function mockFetch(status: number, body: unknown = {}) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("auth api", () => {
  it("getSession returns the body when ok", async () => {
    mockFetch(200, { authenticated: true, user_id: 1 });
    expect(await getSession()).toEqual({ authenticated: true, user_id: 1 });
  });

  it("getSession returns null when the request fails", async () => {
    mockFetch(500);
    expect(await getSession()).toBeNull();
  });

  it("login posts credentials and returns null on 401", async () => {
    const fn = mockFetch(401);
    expect(await login("a@b.co", "pw")).toBeNull();

    const [url, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/auth/login");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ email: "a@b.co", password: "pw" });
  });

  it("logout throws when the request fails", async () => {
    mockFetch(500);
    await expect(logout()).rejects.toThrow("Logout failed");
  });

  it("register uses a relative URL and throws on failure", async () => {
    const fn = mockFetch(409);
    await expect(register({ email: "a@b.co" })).rejects.toThrow("Registration failed");
    expect((fn.mock.calls[0] as [string])[0]).toBe("/api/auth/register");
  });
});
