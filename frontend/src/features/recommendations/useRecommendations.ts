import { useEffect, useRef, useState } from "react";
import { gateway, GatewayError } from "../../api/gateway";
import type { RecommendationResponse } from "../../api/contracts";
import { sampleQuery, sampleResponse } from "./sample";

export type RecommendationState =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | {
      status: "success";
      query: string;
      source: "live" | "sample";
      response: RecommendationResponse;
    }
  | { status: "error"; query: string; error: GatewayError };

export function useRecommendations() {
  const [state, setState] = useState<RecommendationState>({ status: "idle" });
  const active = useRef<AbortController | null>(null);
  const version = useRef(0);
  useEffect(
    () => () => {
      active.current?.abort();
      version.current += 1;
    },
    [],
  );

  async function search(query: string) {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    const requestVersion = ++version.current;
    setState({ status: "loading", query });
    try {
      const response = await gateway.recommend(query, controller.signal);
      if (version.current === requestVersion && !controller.signal.aborted)
        setState({ status: "success", query, source: "live", response });
    } catch (error) {
      if (version.current !== requestVersion || controller.signal.aborted)
        return;
      setState({
        status: "error",
        query,
        error:
          error instanceof GatewayError
            ? error
            : new GatewayError("Something went wrong. Please try again."),
      });
    } finally {
      if (version.current === requestVersion) active.current = null;
    }
  }

  function cancel() {
    active.current?.abort();
    active.current = null;
    version.current += 1;
    setState({ status: "idle" });
  }

  function preview() {
    cancel();
    setState({
      status: "success",
      query: sampleQuery,
      source: "sample",
      response: sampleResponse,
    });
  }

  return { state, search, cancel, preview };
}
