import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useConversationsSocket } from "../../src/api/useConversationSocket";

class FakeSocket {
  static OPEN = 1;
  static instances: FakeSocket[] = [];

  readyState = 1;
  url: string;
  sent: string[] = [];
  closed = false;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((err: unknown) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.closed = true;
    this.readyState = 3;
  }

  emit(payload: unknown) {
    const data = typeof payload === "string" ? payload : JSON.stringify(payload);
    this.onmessage?.({ data });
  }
}

beforeEach(() => {
  FakeSocket.instances.length = 0;
  vi.stubGlobal("WebSocket", FakeSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useConversationsSocket", () => {
  it("connects to the conversations endpoint on the page origin", () => {
    renderHook(() => useConversationsSocket(vi.fn()));

    expect(FakeSocket.instances).toHaveLength(1);
    expect(FakeSocket.instances[0].url).toMatch(/^wss?:\/\/.+\/api\/ws\/conversations$/);
  });

  it("answers server pings with a pong and does not forward them", () => {
    const onMessage = vi.fn();
    renderHook(() => useConversationsSocket(onMessage));
    const socket = FakeSocket.instances[0];

    socket.emit({ type: "ping" });

    expect(socket.sent).toEqual([JSON.stringify({ type: "pong" })]);
    expect(onMessage).not.toHaveBeenCalled();
  });

  it("forwards other events to the callback", () => {
    const onMessage = vi.fn();
    renderHook(() => useConversationsSocket(onMessage));

    const event = { type: "read", conversation_id: 1, user_id: 2 };
    FakeSocket.instances[0].emit(event);

    expect(onMessage).toHaveBeenCalledWith(event);
  });

  it("uses the latest callback without reconnecting", () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = renderHook(({ cb }) => useConversationsSocket(cb), {
      initialProps: { cb: first },
    });

    rerender({ cb: second });
    FakeSocket.instances[0].emit({ type: "ready" });

    expect(FakeSocket.instances).toHaveLength(1);
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });

  it("sends JSON only while the socket is open", () => {
    const { result } = renderHook(() => useConversationsSocket(vi.fn()));
    const socket = FakeSocket.instances[0];

    result.current.send({ type: "typing", conversation_id: 1, is_typing: true });
    expect(socket.sent).toEqual([
      JSON.stringify({ type: "typing", conversation_id: 1, is_typing: true }),
    ]);

    socket.readyState = 3;
    result.current.send({ type: "typing" });
    expect(socket.sent).toHaveLength(1);
  });

  it("ignores malformed frames", () => {
    const onMessage = vi.fn();
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    renderHook(() => useConversationsSocket(onMessage));

    FakeSocket.instances[0].emit("not json");

    expect(onMessage).not.toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();
  });

  it("closes the socket on unmount", () => {
    const { unmount } = renderHook(() => useConversationsSocket(vi.fn()));
    const socket = FakeSocket.instances[0];

    unmount();

    expect(socket.closed).toBe(true);
  });
});
