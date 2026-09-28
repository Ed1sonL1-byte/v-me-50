import { act, render, renderHook, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { gateway, GatewayError } from "../api/gateway";
import { sampleResponse } from "../features/recommendations/sample";
import { useRecommendations } from "../features/recommendations/useRecommendations";

describe("recommendation experience", () => {
  it("shows clearly labelled sample records without calling recommendations", async () => {
    const recommend = vi.spyOn(gateway, "recommend");
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Explore a sample shortlist" }),
    );
    expect(screen.getByText("Sample preview.")).toBeVisible();
    expect(screen.getByText(/This is not a live AI result/)).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Naanu Nanna Kanasu" }),
    ).toBeVisible();
    expect(recommend).not.toHaveBeenCalled();
  });

  it("validates input, submits a request, and displays an evidence-limited empty result", async () => {
    const recommend = vi
      .spyOn(gateway, "recommend")
      .mockResolvedValue({
        recommendations: [],
        message: "No supported match.",
      });
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Find my movies" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("3–1,000");
    expect(recommend).not.toHaveBeenCalled();
    await userEvent.type(screen.getByRole("textbox"), "Family bonds");
    await userEvent.click(
      screen.getByRole("button", { name: "Find my movies" }),
    );
    expect(await screen.findByText("No supported match.")).toBeVisible();
    expect(screen.getByText("0 movies")).toBeVisible();
    expect(recommend).toHaveBeenCalledWith(
      "Family bonds",
      expect.any(AbortSignal),
    );
  });

  it("clarifies an ambiguous reference by appending a year to the same raw query", async () => {
    const recommend = vi
      .spyOn(gateway, "recommend")
      .mockRejectedValueOnce(
        new GatewayError("Which movie did you have in mind?", 422, [
          { movie_id: "Q1", title: "Home", year: 2015 },
        ]),
      )
      .mockResolvedValueOnce({ recommendations: [] });
    render(<App />);
    await userEvent.type(screen.getByRole("textbox"), "Like Home, more family");
    await userEvent.click(
      screen.getByRole("button", { name: "Find my movies" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Home 2015" }),
    );
    expect(recommend.mock.calls[1][0]).toBe(
      "Like Home, more family\nThe reference movie is Home (2015).",
    );
  });

  it("cancels pending work and ignores its late response when showing a sample", async () => {
    let resolve!: (value: typeof sampleResponse) => void;
    const recommend = vi.spyOn(gateway, "recommend").mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const { result } = renderHook(useRecommendations);
    let request!: Promise<void>;
    act(() => {
      request = result.current.search("Old request");
    });
    expect(result.current.state.status).toBe("loading");
    act(() => {
      result.current.preview();
    });
    expect(recommend.mock.calls[0][1].aborted).toBe(true);
    await act(async () => {
      resolve({ recommendations: [] });
      await request;
    });
    expect(result.current.state).toMatchObject({
      status: "success",
      source: "sample",
    });
  });

  it("makes sign-in availability explicit instead of creating a fake session", async () => {
    render(<App />);
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Sign-in is not available yet.",
    );
  });
});
