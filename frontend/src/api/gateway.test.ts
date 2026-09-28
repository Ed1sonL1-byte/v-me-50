import { describe, expect, it, vi } from "vitest";
import { createGatewayClient } from "./gateway";
import { webUrl } from "./contracts";
import { sampleResponse } from "../features/recommendations/sample";

const signal = () => new AbortController().signal;
const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("gateway contract", () => {
  it("sends only the trimmed raw query and the gateway session cookie", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response(sampleResponse));
    const result = await createGatewayClient(
      { baseUrl: "/api/" },
      fetcher,
    ).recommend("  family bonds  ", signal());
    expect(fetcher).toHaveBeenCalledWith(
      "/api/v1/recommendations",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: '{"query":"family bonds"}',
      }),
    );
    expect(result.recommendations[0].movie_id).toBe("Q6956601");
  });

  it("preserves ambiguity choices for the release-year clarification UI", async () => {
    const candidates = [
      { movie_id: "Q1", title: "Home", year: 2010 },
      { movie_id: "Q2", title: "Home", year: 2015 },
    ];
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        response({ detail: { message: "Ambiguous", candidates } }, 422),
      );
    await expect(
      createGatewayClient({ baseUrl: "/api" }, fetcher).recommend(
        "Like Home",
        signal(),
      ),
    ).rejects.toMatchObject({ status: 422, candidates });
  });

  it("distinguishes sign-in and unavailable failures without exposing server internals", async () => {
    for (const status of [401, 403, 502, 503]) {
      const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(
          response({ detail: "secret internal failure" }, status),
        );
      await expect(
        createGatewayClient({ baseUrl: "/api" }, fetcher).recommend(
          "family",
          signal(),
        ),
      ).rejects.toMatchObject({ status });
      await expect(
        createGatewayClient({ baseUrl: "/api" }, fetcher).recommend(
          "family",
          signal(),
        ),
      ).rejects.not.toHaveProperty("message", "secret internal failure");
    }
  });

  it("rejects malformed success responses rather than inventing missing evidence", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        response({ recommendations: [{ title: "Movie", evidence: null }] }),
      );
    await expect(
      createGatewayClient({ baseUrl: "/api" }, fetcher).recommend(
        "family",
        signal(),
      ),
    ).rejects.toMatchObject({ status: 502 });
  });

  it("accepts empty results and missing optional movie metadata", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        response({
          recommendations: [],
          message: "No evidence supports the request.",
        }),
      );
    const result = await createGatewayClient(
      { baseUrl: "/api" },
      fetcher,
    ).recommend("family", signal());
    expect(result.recommendations).toEqual([]);
    expect(result.message).toContain("No evidence");
  });

  it("cancels the underlying request and treats cancellation separately from failures", async () => {
    const controller = new AbortController();
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    const pending = createGatewayClient({ baseUrl: "/api" }, fetcher).recommend(
      "family",
      controller.signal,
    );
    controller.abort();
    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true);
  });

  it("bounds a stalled request with a timeout", async () => {
    vi.useFakeTimers();
    try {
      const fetcher = vi.fn<typeof fetch>().mockImplementation(
        (_url, options) =>
          new Promise((_resolve, reject) => {
            options?.signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            );
          }),
      );
      const pending = createGatewayClient(
        { baseUrl: "/api" },
        fetcher,
      ).recommend("family", signal());
      const assertion = expect(pending).rejects.toThrow(
        "taking longer than expected",
      );
      await vi.advanceTimersByTimeAsync(120_000);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  it("does not invent a session route, and treats configured session 401 as signed out", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(response({ detail: "Unauthorized" }, 401));
    expect(
      await createGatewayClient({ baseUrl: "/api" }, fetcher).session(signal()),
    ).toBeNull();
    expect(fetcher).not.toHaveBeenCalled();
    expect(
      await createGatewayClient(
        { baseUrl: "/api", sessionPath: "/auth/session" },
        fetcher,
      ).session(signal()),
    ).toBeNull();
    expect(fetcher.mock.calls[0][0]).toBe("/api/auth/session");
  });

  it("blocks unsafe source and login URL protocols", () => {
    expect(webUrl("javascript:alert(1)")).toBeNull();
    expect(webUrl("data:text/html,hello")).toBeNull();
    expect(webUrl("https://en.wikipedia.org/wiki/Home")).toBe(
      "https://en.wikipedia.org/wiki/Home",
    );
  });
});
