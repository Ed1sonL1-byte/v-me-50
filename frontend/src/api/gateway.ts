import { z } from "zod";
import { candidateSchema, responseSchema, sessionSchema } from "./contracts";
import type { ReferenceCandidate } from "./contracts";

export interface GatewayConfig {
  baseUrl: string;
  loginUrl?: string;
  sessionPath?: string;
}
export const gatewayConfig: GatewayConfig = {
  baseUrl: import.meta.env.VITE_GATEWAY_BASE_URL || "/api",
  loginUrl: import.meta.env.VITE_GATEWAY_LOGIN_URL || undefined,
  sessionPath: import.meta.env.VITE_GATEWAY_SESSION_PATH || undefined,
};

export class GatewayError extends Error {
  constructor(
    message: string,
    public readonly status: number = 0,
    public readonly candidates: ReferenceCandidate[] = [],
  ) {
    super(message);
    this.name = "GatewayError";
  }
}

function httpError(status: number, body: unknown): GatewayError {
  const detail = z.object({ detail: z.unknown() }).safeParse(body);
  const value = detail.success ? detail.data.detail : undefined;
  if (status === 401)
    return new GatewayError(
      "Please sign in to get your movie recommendations.",
      status,
    );
  if (status === 403)
    return new GatewayError(
      "Your session cannot access recommendations. Please sign in again.",
      status,
    );
  if (status === 422) {
    const ambiguous = z
      .object({ candidates: z.array(candidateSchema).min(1) })
      .safeParse(value);
    if (ambiguous.success)
      return new GatewayError(
        "Which movie did you have in mind?",
        status,
        ambiguous.data.candidates,
      );
    return new GatewayError(
      typeof value === "string"
        ? value
        : "Please check your request. Use between 3 and 1,000 characters.",
      status,
    );
  }
  if (status === 429)
    return new GatewayError(
      "A few too many requests. Please give it a moment and try again.",
      status,
    );
  if (status === 502)
    return new GatewayError(
      "We couldn’t put together reliable recommendations. Please try again.",
      status,
    );
  if (status === 503)
    return new GatewayError(
      "Live recommendations are unavailable right now. Try again later, or explore the sample.",
      status,
    );
  return new GatewayError(
    "Something went wrong while finding your movies. Please try again.",
    status,
  );
}

export function createGatewayClient(
  config: GatewayConfig = gatewayConfig,
  fetcher: typeof fetch = fetch,
) {
  const endpoint = (path: string) =>
    `${config.baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;

  async function request(path: string, signal: AbortSignal, body?: object) {
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timeout = setTimeout(() => {
      timedOut = true;
      abort();
    }, 120_000);
    try {
      const response = await fetcher(endpoint(path), {
        method: body ? "POST" : "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
          ...(body ? { "Content-Type": "application/json" } : {}),
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
        signal: controller.signal,
      });
      const data: unknown = await response.json().catch((error: unknown) => {
        if (controller.signal.aborted) throw error;
        return null;
      });
      if (!response.ok) throw httpError(response.status, data);
      return data;
    } catch (error) {
      if (signal.aborted) throw new DOMException("Cancelled", "AbortError");
      if (timedOut)
        throw new GatewayError(
          "This is taking longer than expected. Please try again.",
        );
      if (error instanceof GatewayError) throw error;
      throw new GatewayError(
        "We couldn’t connect. Check your connection and try again.",
      );
    } finally {
      clearTimeout(timeout);
      signal.removeEventListener("abort", abort);
    }
  }

  return {
    async recommend(query: string, signal: AbortSignal) {
      const parsed = responseSchema.safeParse(
        await request("/v1/recommendations", signal, { query: query.trim() }),
      );
      if (!parsed.success)
        throw new GatewayError(
          "The movie response was incomplete. Please try again.",
          502,
        );
      return parsed.data;
    },
    async session(signal: AbortSignal) {
      if (!config.sessionPath) return null;
      let data: unknown;
      try {
        data = await request(config.sessionPath, signal);
      } catch (error) {
        if (error instanceof GatewayError && error.status === 401) return null;
        throw error;
      }
      const parsed = sessionSchema.safeParse(data);
      if (!parsed.success)
        throw new GatewayError("We couldn’t check your sign-in status.", 502);
      return parsed.data.user;
    },
  };
}

export const gateway = createGatewayClient();
