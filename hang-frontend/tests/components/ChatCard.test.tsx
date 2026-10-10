import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatCard from "../../src/components/conversations/ChatCard";
import type { MessageListResponse } from "../../src/components/conversations/ChatCard";

function makeData(overrides: Partial<MessageListResponse> = {}): MessageListResponse {
  return {
    conversation_id: 1,
    current_user_id: 1,
    messages: [
      {
        message_id: 1,
        sender_id: 2,
        content: "hi there",
        created_at: "2026-01-01T00:00:00Z",
        is_read: true,
      },
      {
        message_id: 2,
        sender_id: 1,
        content: "hello",
        created_at: "2026-01-01T00:01:00Z",
        is_read: false,
      },
    ],
    next_cursor: null,
    has_more: false,
    ...overrides,
  };
}

describe("ChatCard", () => {
  it("prompts to select a conversation when there is no data", () => {
    render(<ChatCard data={null} />);
    expect(screen.getByText("Select a conversation")).toBeInTheDocument();
  });

  it("shows an empty state for a conversation without messages", () => {
    render(<ChatCard data={makeData({ messages: [] })} />);
    expect(screen.getByText("No messages yet")).toBeInTheDocument();
  });

  it("renders all messages", () => {
    render(<ChatCard data={makeData()} />);
    expect(screen.getByText("hi there")).toBeInTheDocument();
    expect(screen.getByText("hello")).toBeInTheDocument();
  });

  it("shows a delivery status only on the last message", () => {
    render(<ChatCard data={makeData()} />);
    expect(screen.getAllByText(/^(Sent|Read)$/)).toHaveLength(1);
    expect(screen.getByText("Sent")).toBeInTheDocument();
  });

  it("shows Read once the last message is read", () => {
    const data = makeData();
    data.messages[1].is_read = true;
    render(<ChatCard data={data} />);
    expect(screen.getByText("Read")).toBeInTheDocument();
  });

  it("shows the typing indicator only while typing", () => {
    const { rerender } = render(<ChatCard data={makeData({ typing: true })} />);
    expect(screen.getByText("typing...")).toBeInTheDocument();

    rerender(<ChatCard data={makeData({ typing: false })} />);
    expect(screen.queryByText("typing...")).not.toBeInTheDocument();
  });

  it("sends on Enter and clears the input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatCard data={makeData()} onSend={onSend} />);

    const input = screen.getByPlaceholderText("Type a message...");
    await user.type(input, "hey{Enter}");

    expect(onSend).toHaveBeenCalledWith("hey");
    expect(input).toHaveValue("");
  });

  it("sends with the Send button", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatCard data={makeData()} onSend={onSend} />);

    await user.type(screen.getByPlaceholderText("Type a message..."), "yo");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).toHaveBeenCalledWith("yo");
  });

  it("does not send blank messages", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatCard data={makeData()} onSend={onSend} />);

    await user.type(screen.getByPlaceholderText("Type a message..."), "   {Enter}");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).not.toHaveBeenCalled();
  });

  it("reports typing on every change", async () => {
    const user = userEvent.setup();
    const onTyping = vi.fn();
    render(<ChatCard data={makeData()} onTyping={onTyping} />);

    await user.type(screen.getByPlaceholderText("Type a message..."), "ab");

    expect(onTyping).toHaveBeenCalledTimes(2);
    expect(onTyping).toHaveBeenLastCalledWith("ab");
  });

  it("loads older messages when scrolled to the top and more exist", async () => {
    const onLoadMore = vi.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ChatCard data={makeData({ has_more: true, next_cursor: 5 })} onLoadMore={onLoadMore} />
    );

    const scroller = container.querySelector(".overflow-y-auto") as HTMLElement;
    scroller.scrollTop = 0;
    fireEvent.scroll(scroller);

    await waitFor(() => expect(onLoadMore).toHaveBeenCalledWith(5));
  });

  it("does not load more when there is nothing older", () => {
    const onLoadMore = vi.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ChatCard data={makeData({ has_more: false })} onLoadMore={onLoadMore} />
    );

    fireEvent.scroll(container.querySelector(".overflow-y-auto") as HTMLElement);

    expect(onLoadMore).not.toHaveBeenCalled();
  });
});
