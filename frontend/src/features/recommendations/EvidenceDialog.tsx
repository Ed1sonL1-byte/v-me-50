import { ArrowUpRight, BookOpen, X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { Recommendation } from "../../api/contracts";
import { webUrl } from "../../api/contracts";

export function EvidenceDialog({
  movie,
  onClose,
}: {
  movie: Recommendation;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const source = webUrl(movie.source_url);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = overflow;
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="evidence-dialog"
      aria-labelledby="evidence-title"
      onCancel={onClose}
      onClose={(event) => {
        if (!event.currentTarget.open) onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="dialog-content">
        <div className="dialog-heading">
          <span className="eyebrow">
            <BookOpen size={15} />
            BEHIND THE MATCH
          </span>
          <button
            onClick={onClose}
            className="icon-button"
            aria-label="Close evidence"
          >
            <X size={20} />
          </button>
        </div>
        <h2 id="evidence-title">{movie.title}</h2>
        <p className="dialog-meta">
          {movie.year ?? "Year unavailable"} · Movie ID {movie.movie_id}
        </p>
        {!!movie.actors?.length && (
          <p className="dialog-meta">Cast: {movie.actors.join(", ")}</p>
        )}
        {!!movie.directors?.length && (
          <p className="dialog-meta">Director: {movie.directors.join(", ")}</p>
        )}
        <h3>Why it matches</h3>
        <p>{movie.explanation}</p>
        <h3>Quoted evidence</h3>
        <blockquote>“{movie.evidence_quote}”</blockquote>
        <h3>Full source plot</h3>
        <p className="full-plot">{movie.evidence}</p>
        <p className="source-note">
          The plot is a dataset source record. The explanation is an
          interpretation of that record.
        </p>
        {source && (
          <a
            href={source}
            className="source-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open original source <ArrowUpRight size={16} />
            <span className="sr-only"> (opens a new tab)</span>
          </a>
        )}
      </div>
    </dialog>
  );
}
