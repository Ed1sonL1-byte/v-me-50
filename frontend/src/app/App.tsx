import { ArrowUpRight, Clapperboard, Database, Quote } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReferenceCandidate } from "../api/contracts";
import { AccountButton } from "../features/auth/AccountButton";
import { QueryForm } from "../features/recommendations/QueryForm";
import { Results } from "../features/recommendations/Results";
import { useRecommendations } from "../features/recommendations/useRecommendations";
import { sampleQuery } from "../features/recommendations/sample";

export function App() {
  const [query, setQuery] = useState("");
  const { state, search, cancel, preview } = useRecommendations();
  const results = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (state.status !== "success" && state.status !== "error") return;
    results.current?.focus({ preventScroll: true });
    results.current?.scrollIntoView({ block: "start", behavior: "auto" });
  }, [state]);
  function showSample() {
    setQuery(sampleQuery);
    preview();
  }
  function clarify(candidate: ReferenceCandidate) {
    if (state.status !== "error" || candidate.year === null) return;
    const clarified = `${state.query}\nThe reference movie is ${candidate.title} (${candidate.year}).`;
    setQuery(clarified);
    if (Array.from(clarified).length <= 1000) void search(clarified);
    else cancel();
  }
  return (
    <>
      <a className="skip-link" href="#movie-query">
        Skip to movie search
      </a>
      <header className="site-header page-width">
        <a href="/" className="brand" aria-label="V Me 50 home">
          <span className="brand-mark">
            <Clapperboard size={21} />
          </span>
          V Me <strong>50</strong>
          <span className="brand-dot" />
        </a>
        <div className="header-right">
          <span className="catalog-label">
            <Database size={13} />
            92,374 stories to discover
          </span>
          <AccountButton />
        </div>
      </header>
      <main className="page-width">
        <section className="hero" aria-labelledby="hero-heading">
          <div className="hero-copy">
            <span className="eyebrow">
              <span className="status-dot" />A BETTER WAY TO FIND A MOVIE
            </span>
            <h1 id="hero-heading">
              Less scrolling.
              <br />
              More <em>cinema.</em>
            </h1>
            <p>
              Not just a genre. A feeling.
              <br />
              Find films that understand what you’re looking for.
            </p>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="art-caption">FOR YOUR KIND OF EVENING</div>
            <div className="cinema-ticket ticket-back">
              <span>THE STORIES THAT STAY</span>
              <div className="ticket-circle" />
              <b>
                BEYOND
                <br />
                THE GENRE.
              </b>
              <span>ADMIT ONE · V ME 50</span>
            </div>
            <div className="cinema-ticket ticket-front">
              <Quote size={25} />
              <p>
                Less outer space.
                <br />
                More <em>coming home.</em>
              </p>
              <div className="ticket-divider" />
              <span>
                A SMALL DETAIL.
                <br />A WHOLE DIFFERENT FILM.
              </span>
              <span className="ticket-star">✳</span>
            </div>
          </div>
        </section>
        <QueryForm
          query={query}
          setQuery={setQuery}
          loading={state.status === "loading"}
          onSearch={(value) => void search(value)}
          onCancel={cancel}
        />
        <div className="search-footnote">
          <span>
            <span className="tiny-dot" />
            Recommendations with plot evidence
          </span>
          <button onClick={showSample} disabled={state.status === "loading"}>
            See a sample <ArrowUpRight size={13} />
          </button>
        </div>
        <div
          ref={results}
          className="results-target"
          tabIndex={-1}
          aria-label="Movie search results"
        >
          <Results
            key={
              state.status === "success"
                ? `${state.source}-${state.query}`
                : state.status
            }
            state={state}
            onPreview={showSample}
            onRetry={() => {
              if (state.status === "error") {
                setQuery(state.query);
                void search(state.query);
              }
            }}
            onClarify={clarify}
          />
        </div>
        <section className="how-it-works" aria-label="How recommendations work">
          <div>
            <span>01</span>
            <h3>Tell us your taste.</h3>
            <p>Use your own words. The more specific, the better.</p>
          </div>
          <div>
            <span>02</span>
            <h3>We look inside the story.</h3>
            <p>Plots and available metadata help us find a match.</p>
          </div>
          <div>
            <span>03</span>
            <h3>See why it fits.</h3>
            <p>Every recommendation comes with evidence to explore.</p>
          </div>
        </section>
      </main>
      <footer className="site-footer page-width">
        <span>
          V Me 50<span className="footer-dot">·</span>A CSE 5914 project
        </span>
        <a
          href="https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset"
          target="_blank"
          rel="noopener noreferrer"
        >
          Movie data by NiklasAbraham <ArrowUpRight size={13} />
          <span className="sr-only"> (opens a new tab)</span>
        </a>
      </footer>
    </>
  );
}
