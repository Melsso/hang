import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../../src/api/swipes", () => ({
  get_swipe_profiles: vi.fn(),
  swipe_action: vi.fn(),
}));

vi.mock("../../src/components/swipes/SwipeCard", () => ({
  default: ({ profile }: { profile?: { first_name: string } }) => (
    <div>{profile ? profile.first_name : "No more profiles"}</div>
  ),
}));

vi.mock("../../src/components/swipes/SwipeAction", () => ({
  default: ({ onSwipe }: { onSwipe: (type: string) => void }) => (
    <button onClick={() => onSwipe("like")}>like</button>
  ),
}));

vi.mock("../../src/components/global/ActionBar", () => ({ default: () => null }));

import { get_swipe_profiles, swipe_action } from "../../src/api/swipes";
import type { SwipeProfile } from "../../src/components/swipes/SwipeCard";
import { ToastProvider } from "../../src/components/global/ToastProvider";
import Swipes from "../../src/pages/Swipes";

function profile(id: number, name: string): SwipeProfile {
  return {
    user_id: id,
    first_name: name,
    bio: "bio",
    interests: ["music"],
    gender: "female",
    images: [],
  };
}

function renderPage() {
  return render(
    <ToastProvider>
      <Swipes />
    </ToastProvider>
  );
}

beforeEach(() => {
  vi.mocked(get_swipe_profiles).mockReset();
  vi.mocked(swipe_action).mockReset();
});

describe("Swipes page", () => {
  it("asks the user to complete their profile when the feed is locked", async () => {
    vi.mocked(get_swipe_profiles).mockResolvedValue({ status: "incomplete" });
    renderPage();

    expect(await screen.findByText("Please complete your profile.")).toBeInTheDocument();
    expect(screen.getByText("No more profiles")).toBeInTheDocument();
  });

  it("shows an error toast and the empty state when loading fails", async () => {
    vi.mocked(get_swipe_profiles).mockResolvedValue({ status: "error" });
    renderPage();

    expect(await screen.findByText("Something went wrong, try again later.")).toBeInTheDocument();
    expect(screen.getByText("No more profiles")).toBeInTheDocument();
  });

  it("shows the first profile", async () => {
    vi.mocked(get_swipe_profiles).mockResolvedValue({
      status: "ok",
      profiles: [profile(1, "Jane"), profile(2, "Amy")],
    });
    renderPage();

    expect(await screen.findByText("Jane")).toBeInTheDocument();
  });

  it("records a swipe and advances to the next profile", async () => {
    const user = userEvent.setup();
    vi.mocked(get_swipe_profiles).mockResolvedValue({
      status: "ok",
      profiles: [profile(1, "Jane"), profile(2, "Amy")],
    });
    vi.mocked(swipe_action).mockResolvedValue({ success: true, conversation: null });
    renderPage();

    await screen.findByText("Jane");
    await user.click(screen.getByText("like"));

    expect(swipe_action).toHaveBeenCalledWith(1, "like");
    expect(await screen.findByText("Amy")).toBeInTheDocument();
  });

  it("fetches the next page after the last profile", async () => {
    const user = userEvent.setup();
    vi.mocked(get_swipe_profiles)
      .mockResolvedValueOnce({ status: "ok", profiles: [profile(1, "Jane")] })
      .mockResolvedValueOnce({ status: "ok", profiles: [profile(3, "Bob")] });
    vi.mocked(swipe_action).mockResolvedValue({ success: true, conversation: null });
    renderPage();

    await screen.findByText("Jane");
    await user.click(screen.getByText("like"));

    expect(await screen.findByText("Bob")).toBeInTheDocument();
    expect(get_swipe_profiles).toHaveBeenCalledTimes(2);
  });

  it("keeps the profile and shows an error when the swipe fails", async () => {
    const user = userEvent.setup();
    vi.mocked(get_swipe_profiles).mockResolvedValue({
      status: "ok",
      profiles: [profile(1, "Jane"), profile(2, "Amy")],
    });
    vi.mocked(swipe_action).mockResolvedValue(null);
    renderPage();

    await screen.findByText("Jane");
    await user.click(screen.getByText("like"));

    expect(await screen.findByText("Something went wrong, try again later.")).toBeInTheDocument();
    expect(screen.getByText("Jane")).toBeInTheDocument();
  });
});
