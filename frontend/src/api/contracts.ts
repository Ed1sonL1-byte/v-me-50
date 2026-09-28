import { z } from "zod";

export const recommendationSchema = z.object({
  movie_id: z.string().min(1),
  title: z.string().min(1),
  year: z.number().int().nullable(),
  genres: z.array(z.string()),
  explanation: z.string().min(1),
  evidence: z.string().min(1),
  evidence_quote: z.string().min(1),
  source_url: z.string().nullable(),
});

export const responseSchema = z.object({
  recommendations: z.array(recommendationSchema).max(5),
  reference_movie_id: z.string().nullable().optional(),
  message: z.string().nullable().optional(),
});

export const candidateSchema = z.object({
  movie_id: z.string(),
  title: z.string(),
  year: z.number().int().nullable(),
});

export const sessionSchema = z.object({
  user: z
    .object({ id: z.string().min(1), name: z.string().optional() })
    .nullable(),
});

export type Recommendation = z.infer<typeof recommendationSchema>;
export type RecommendationResponse = z.infer<typeof responseSchema>;
export type ReferenceCandidate = z.infer<typeof candidateSchema>;
export type GatewayUser = NonNullable<z.infer<typeof sessionSchema>["user"]>;

/** Only navigate to ordinary web addresses, including configured relative paths. */
export function webUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value, window.location.origin);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}
