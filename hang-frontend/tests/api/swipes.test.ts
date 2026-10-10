import { afterEach, describe, expect, it, vi } from "vitest";
import { get_swipe_profiles, swipe_action } from "../../src/api/swipes";

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

describe("get_swipe_profiles", () => {
  it("returns ok with profiles", async () => {
    mockFetch(200, [{ user_id: 1 }]);
    expect(await get_swipe_profiles()).toEqual({
      status: "ok",
      profiles: [{ user_id: 1 }],
    });
  });

  it("maps 403 to incomplete", async () => {
    mockFetch(403);
    expect(await get_swipe_profiles()).toEqual({ status: "incomplete" });
  });

  it("maps other failures to error", async () => {
    mockFetch(500);
    expect(await get_swipe_profiles()).toEqual({ status: "error" });
  });
});

describe("swipe_action", () => {
  it("converts super-like to super_like", async () => {
    const fn = mockFetch(200, { success: true });
    await swipe_action(5, "super-like");

    const [url, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/swipes/swipe-action");
    expect(JSON.parse(init.body as string)).toEqual({
      to_user_id: 5,
      swipe_type: "super_like",
    });
  });

  it("leaves like and pass untouched", async () => {
    const fn = mockFetch(200, {});
    await swipe_action(1, "pass");
    const [, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(init.body as string).swipe_type).toBe("pass");
  });

  it("returns null on failure", async () => {
    mockFetch(400);
    expect(await swipe_action(1, "like")).toBeNull();
  });
});
