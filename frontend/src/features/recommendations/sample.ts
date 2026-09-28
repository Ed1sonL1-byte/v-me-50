import type { RecommendationResponse } from "../../api/contracts";

export const sampleQuery =
  "Like Interstellar, but with less science fiction and more focus on family relationships.";

/** Manually selected from the real September 27 retrieval inspection. No LLM ran. */
export const sampleResponse: RecommendationResponse = {
  reference_movie_id: "Q13417189",
  recommendations: [
    {
      movie_id: "Q6956601",
      title: "Naanu Nanna Kanasu",
      year: 2010,
      genres: ["drama film"],
      explanation:
        "A father learning to grow alongside his daughter puts the parent-child bond at the center of the story. The retrieved plot supports the family preference, without describing a science-fiction setting.",
      evidence:
        "The film is about a relationship between a father and his daughter. It emphasizes on how a father has to go through changes as his daughter grows up from being an infant to a grown woman married as per circumstances.",
      evidence_quote:
        "The film is about a relationship between a father and his daughter.",
      source_url: "https://en.wikipedia.org/wiki/Naanu_Nanna_Kanasu",
    },
    {
      movie_id: "Q20714861",
      title: "Mothers and Daughters",
      year: 2016,
      genres: ["drama film"],
      explanation:
        "An estranged mother-daughter relationship brings the request for family connection into focus. The available synopsis centers on motherhood and reconsidering a relationship rather than a science-fiction premise.",
      evidence:
        "The film revolves around the relationships between several mothers and their children. A pregnant photographer captures motherhood on film while re-examining her relationship with her estranged mom.",
      evidence_quote:
        "A pregnant photographer captures motherhood on film while re-examining her relationship with her estranged mom.",
      source_url:
        "https://en.wikipedia.org/wiki/Mothers_and_Daughters_(2016_film)",
    },
    {
      movie_id: "Q104842890",
      title: "Beautifully Broken",
      year: 2018,
      genres: ["drama film"],
      explanation:
        "Three fathers trying to protect their families connect with the themes of sacrifice and family bonds. Forgiveness and reconciliation also appear explicitly in the retrieved plot.",
      evidence:
        "As three fathers fight to save their families, their lives become intertwined in an unlikely journey across the world, where they learn about forgiveness and reconciliation.",
      evidence_quote:
        "As three fathers fight to save their families, their lives become intertwined in an unlikely journey across the world",
      source_url: "https://en.wikipedia.org/wiki/Beautifully_Broken_(film)",
    },
  ],
};
