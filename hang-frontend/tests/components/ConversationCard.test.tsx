import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ConversationCard from "../../src/components/conversations/ConversationCard";
import type { Conversation } from "../../src/components/conversations/ConversationCard";

function makeConversation(overrides: Partial<Conversation> = {}): Conversation {
  return {
    conversation_id: 1,
    other_user_id: 7,
    other_user_name: "Jane",
    other_user_img_url: null,
    last_message: "see you",
    last_message_at: "2026-01-01T00:00:00Z",
    unread_count: 0,
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderCard(props: Parameters<typeof ConversationCard>[0]) {
  return render(
    <MemoryRouter initialEntries={["/conversations"]}>
      <Routes>
        <Route path="/conversations" element={<ConversationCard {...props} />} />
        <Route path="/profile/:userId" element={<div>profile page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ConversationCard", () => {
  it("shows an empty state", () => {
    renderCard({ conversations: [] });
    expect(screen.getByText("No conversations yet")).toBeInTheDocument();
  });

  it("treats null as empty", () => {
    renderCard({ conversations: null });
    expect(screen.getByText("No conversations yet")).toBeInTheDocument();
  });

  it("renders name and last message", () => {
    renderCard({ conversations: [makeConversation()] });
    expect(screen.getByText("Jane")).toBeInTheDocument();
    expect(screen.getByText("see you")).toBeInTheDocument();
  });

  it("falls back when there are no messages", () => {
    renderCard({ conversations: [makeConversation({ last_message: null })] });
    expect(screen.getByText("No messages yet")).toBeInTheDocument();
  });

  it("shows the unread badge only when there are unread messages", () => {
    renderCard({
      conversations: [
        makeConversation({ conversation_id: 1, unread_count: 3 }),
        makeConversation({
          conversation_id: 2,
          other_user_name: "Amy",
          unread_count: 0,
        }),
      ],
    });

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("selects a conversation when its row is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const conversation = makeConversation();
    renderCard({ conversations: [conversation], onSelect });

    await user.click(screen.getByText("Jane"));

    expect(onSelect).toHaveBeenCalledWith(conversation);
  });

  it("deletes without selecting", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onDelete = vi.fn();
    const conversation = makeConversation();
    renderCard({ conversations: [conversation], onSelect, onDelete });

    await user.click(screen.getByLabelText("Delete conversation with Jane"));

    expect(onDelete).toHaveBeenCalledWith(conversation);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("opens the profile from the avatar without selecting", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderCard({ conversations: [makeConversation()], onSelect });

    await user.click(screen.getByAltText("Jane"));

    expect(await screen.findByText("profile page")).toBeInTheDocument();
    expect(onSelect).not.toHaveBeenCalled();
  });
});
