import { ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import type { FormEvent } from "react";

const prompts = [
  {
    label: "Family over sci-fi",
    query:
      "Like Interstellar, but with less science fiction and more focus on family relationships.",
  },
  {
    label: "A little mystery",
    query:
      "A slow-burning mystery with clever twists, but without graphic violence.",
  },
  {
    label: "Something uplifting",
    query:
      "An uplifting movie about friendship and starting over, ideally under two hours.",
  },
];

interface Props {
  query: string;
  setQuery: (value: string) => void;
  loading: boolean;
  onSearch: (query: string) => void;
  onCancel: () => void;
}

export function QueryForm({
  query,
  setQuery,
  loading,
  onSearch,
  onCancel,
}: Props) {
  const [validation, setValidation] = useState("");
  const input = useRef<HTMLTextAreaElement>(null);
  function submit(event: FormEvent) {
    event.preventDefault();
    const length = Array.from(query.trim()).length;
    if (length < 3 || length > 1000) {
      setValidation("Describe what you’re looking for in 3–1,000 characters.");
      input.current?.focus();
      return;
    }
    setValidation("");
    onSearch(query.trim());
  }
  return (
    <section className="search-panel" aria-labelledby="search-heading">
      <div className="search-topline">
        <h2 id="search-heading">
          <Sparkles size={18} />
          What are you in the mood for?
        </h2>
        <span>YOUR NEXT GREAT WATCH</span>
      </div>
      <form onSubmit={submit}>
        <label htmlFor="movie-query" className="sr-only">
          Describe your movie preferences
        </label>
        <textarea
          id="movie-query"
          ref={input}
          value={query}
          disabled={loading}
          rows={3}
          onChange={(event) => {
            setQuery(event.target.value);
            setValidation("");
          }}
          placeholder="A movie like Interstellar, but less sci-fi and more about family…"
          aria-describedby="query-help query-count"
          aria-invalid={!!validation}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              (event.metaKey || event.ctrlKey) &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
        />
        <div className="search-bottom">
          <p id="query-help">
            A feeling, a favorite film, or a very specific wish.
          </p>
          <span
            id="query-count"
            className={
              Array.from(query.trim()).length > 1000 ? "over-limit" : ""
            }
          >
            {Array.from(query.trim()).length.toLocaleString()} / 1,000
          </span>
          {loading ? (
            <button type="button" className="search-button" onClick={onCancel}>
              <LoaderCircle size={17} className="spin" />
              Cancel search
            </button>
          ) : (
            <button type="submit" className="search-button">
              Find my movies <ArrowRight size={18} />
            </button>
          )}
        </div>
        {validation && (
          <p className="form-error" role="alert">
            {validation}
          </p>
        )}
      </form>
      <div className="prompt-row">
        <span>TRY A PROMPT</span>
        {prompts.map((prompt) => (
          <button
            key={prompt.label}
            type="button"
            disabled={loading}
            onClick={() => {
              setQuery(prompt.query);
              setValidation("");
              input.current?.focus();
            }}
          >
            {prompt.label}
            <ArrowUpIcon />
          </button>
        ))}
      </div>
    </section>
  );
}

function ArrowUpIcon() {
  return <ArrowRight size={13} className="prompt-arrow" aria-hidden="true" />;
}
