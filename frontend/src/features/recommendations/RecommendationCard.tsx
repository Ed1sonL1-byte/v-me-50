import { ArrowUpRight, BookOpen, Quote } from "lucide-react";
import type { Recommendation } from "../../api/contracts";
import { webUrl } from "../../api/contracts";

export function RecommendationCard({
  movie,
  rank,
  onEvidence,
}: {
  movie: Recommendation;
  rank: number;
  onEvidence: (movie: Recommendation) => void;
}) {
  const source = webUrl(movie.source_url);
  return (
    <article className="movie-card">
      <div className={`movie-art art-${(rank - 1) % 3}`} aria-hidden="true">
        <span className="art-rank">0{rank} / THE SHORTLIST</span>
        <div className="art-orbit" />
        <span className="art-title">{movie.title}</span>
        <span className="art-year">{movie.year ?? "YEAR UNKNOWN"}</span>
      </div>
      <div className="movie-content">
        <div className="movie-meta">
          <span className="rank-label">MATCH 0{rank}</span>
          <span>{movie.year ?? "Year unavailable"}</span>
        </div>
        <h3>{movie.title}</h3>
        {movie.genres.length > 0 && (
          <div className="genres">
            {movie.genres.map((genre, index) => (
              <span key={`${genre}-${index}`}>
                {genre.replace(/ film$/i, "")}
              </span>
            ))}
          </div>
        )}
        <p className="movie-explanation">{movie.explanation}</p>
        <blockquote className="evidence-quote">
          <Quote size={16} aria-hidden="true" />
          <div>
            <span>FROM THE PLOT</span>
            <p>“{movie.evidence_quote}”</p>
          </div>
        </blockquote>
        <div className="movie-actions">
          <button onClick={() => onEvidence(movie)}>
            <BookOpen size={15} />
            Read the evidence
          </button>
          {source && (
            <a href={source} target="_blank" rel="noopener noreferrer">
              Source
              <ArrowUpRight size={14} />
              <span className="sr-only">
                {" "}
                for {movie.title} (opens a new tab)
              </span>
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
