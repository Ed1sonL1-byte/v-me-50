import { AlertCircle, ArrowRight, Film, Search, Sparkles } from "lucide-react";
import { useState } from "react";
import type { Recommendation, ReferenceCandidate } from "../../api/contracts";
import type { RecommendationState } from "./useRecommendations";
import { RecommendationCard } from "./RecommendationCard";
import { EvidenceDialog } from "./EvidenceDialog";

interface Props {
  state: RecommendationState;
  onRetry: () => void;
  onPreview: () => void;
  onClarify: (candidate: ReferenceCandidate) => void;
}

export function Results({ state, onRetry, onPreview, onClarify }: Props) {
  const [selected, setSelected] = useState<Recommendation | null>(null);
  if (state.status === "idle")
    return (
      <section className="empty-intro" aria-label="Explore a sample">
        <div className="intro-icon">
          <Film size={23} />
        </div>
        <h2>Your taste goes beyond a genre.</h2>
        <p>Tell us the details. We’ll find the stories.</p>
        <button className="text-button" onClick={onPreview}>
          Explore a sample shortlist <ArrowRight size={15} />
        </button>
      </section>
    );
  if (state.status === "loading")
    return (
      <section className="results loading-results" aria-busy="true">
        <div className="results-heading">
          <h2>
            Finding your kind of story<span className="loading-dots">…</span>
          </h2>
          <p role="status">
            Looking through plots and preferences. This can take a moment.
          </p>
        </div>
        <div className="results-grid">
          {[0, 1, 2].map((item) => (
            <div className="skeleton-card" key={item} aria-hidden="true">
              <div className="skeleton-art" />
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
              <div className="skeleton-block" />
            </div>
          ))}
        </div>
      </section>
    );
  if (state.status === "error") {
    const candidates = state.error.candidates;
    return (
      <section className="response-notice" role="alert">
        <div className="notice-icon">
          <AlertCircle size={22} />
        </div>
        <div>
          <h2>
            {candidates.length
              ? "One title, a few different stories."
              : state.error.status === 401 || state.error.status === 403
                ? "Let’s get you signed in."
                : "We couldn’t find your movies just yet."}
          </h2>
          <p>{state.error.message}</p>
          {candidates.length ? (
            <div className="candidate-list">
              {candidates.map((candidate) => (
                <button
                  key={candidate.movie_id}
                  disabled={candidate.year === null}
                  onClick={() => onClarify(candidate)}
                >
                  {candidate.title}{" "}
                  <span>
                    {candidate.year ?? "Year unavailable — add more detail"}
                  </span>
                  <ArrowRight size={15} />
                </button>
              ))}
            </div>
          ) : (
            <div className="notice-actions">
              <button onClick={onRetry} className="text-button">
                Try again <ArrowRight size={15} />
              </button>
              <button onClick={onPreview} className="text-button">
                Explore the sample
              </button>
            </div>
          )}
        </div>
      </section>
    );
  }
  const { response, source } = state;
  return (
    <section className="results" aria-labelledby="results-heading">
      {source === "sample" && (
        <div className="sample-banner" role="status">
          <Sparkles size={16} />
          <p>
            <strong>Sample preview.</strong> Real catalog records, with manually
            written example explanations. This is not a live AI result.
          </p>
        </div>
      )}
      <div className="results-heading">
        <div>
          <span className="eyebrow">
            {source === "sample"
              ? "A LOOK AT THE EXPERIENCE"
              : "CURATED FOR YOUR REQUEST"}
          </span>
          <h2 id="results-heading">
            {response.recommendations.length
              ? "Your next opening scene."
              : "Let’s try a different direction."}
          </h2>
          <p className="submitted-query">“{state.query}”</p>
        </div>
        <span className="result-count" role="status">
          {response.recommendations.length}{" "}
          {response.recommendations.length === 1 ? "movie" : "movies"}
        </span>
      </div>
      {response.message && <p className="result-message">{response.message}</p>}
      {response.recommendations.length ? (
        <div className="results-grid">
          {response.recommendations.map((movie, index) => (
            <RecommendationCard
              key={movie.movie_id}
              movie={movie}
              rank={index + 1}
              onEvidence={setSelected}
            />
          ))}
        </div>
      ) : (
        <div className="no-results">
          <Search size={28} />
          <p>
            Try a broader theme, a different reference movie, or fewer
            restrictions.
          </p>
        </div>
      )}
      {selected && (
        <EvidenceDialog movie={selected} onClose={() => setSelected(null)} />
      )}
    </section>
  );
}
