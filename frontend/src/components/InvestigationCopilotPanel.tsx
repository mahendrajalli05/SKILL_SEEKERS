"use client";

import { useCallback, useEffect, useState } from "react";

import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { fetchCopilotContext, sendCopilotChat } from "@/lib/api";
import type { CopilotChatResponse, CopilotContextResponse, DataMode } from "@/lib/types";

const REQUIRED_PROMPTS = [
  "What evidence exists?",
  "Why is this being reviewed?",
  "What is the main anomaly?",
  "Which model generated the ML score?",
  "What evidence is missing?",
  "What external context is available?",
  "Is the ML score a fraud probability?",
  "Why is this project high priority?",
  "What evidence supports this?",
  "What information is missing?",
  "What should I inspect next?",
  "Summarize Plan → Claim → Evidence.",
  "Which model generated the ML signal?",
];

const FALLBACK_SUGGESTIONS = [
  ...REQUIRED_PROMPTS,
  "Why is this project flagged?",
  "What evidence is strongest?",
  "Why is Time Intelligence inconclusive?",
  "Show comparable projects.",
];

export function InvestigationCopilotPanel({
  projectId,
  mode,
}: {
  projectId: number;
  mode: DataMode;
}) {
  const [context, setContext] = useState<CopilotContextResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [turns, setTurns] = useState<CopilotChatResponse[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const body = await fetchCopilotContext(projectId, mode, sessionId);
      setContext(body);
      setSessionId(body.session_id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation Copilot could not be loaded.");
    }
  }, [projectId, mode, sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function ask(nextQuestion: string) {
    const text = nextQuestion.trim();
    if (!text || loading) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await sendCopilotChat(projectId, {
        question: text,
        session_id: sessionId,
        data_mode: mode,
      });
      setSessionId(response.session_id);
      setTurns((current) => [...current, response]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "The Copilot could not answer.");
    } finally {
      setLoading(false);
    }
  }

  const suggestions = Array.from(
    new Set([
      ...REQUIRED_PROMPTS,
      ...((context?.suggested_questions?.length ? context.suggested_questions : FALLBACK_SUGGESTIONS) ?? []),
    ]),
  );
  const latest = turns[turns.length - 1];

  return (
    <section id="copilot" className="space-y-4 border border-[var(--line)] bg-white p-5">
      <div>
        <h2 className="font-semibold text-[var(--navy)]">INVESTIGATION COPILOT</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Evidence-grounded assistance for project investigation.
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Evidence-grounded assistant for this investigation. It explains stored
          findings and does not determine fraud or release funds.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <StatusBadge value={context?.data_mode ?? mode} />
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Data mode: {context?.data_mode ?? mode} · Provider: {context?.llm_provider ?? "deterministic"}
          </p>
        </div>
        {context?.data_mode_notice ? (
          <p className="mt-2 text-sm text-[var(--saffron)]">{context.data_mode_notice}</p>
        ) : null}
      </div>

      {error ? <PageState kind="error" message={error} compact /> : null}

      <div className="flex flex-wrap gap-2">
        {suggestions.map((item) => (
          <button
            key={item}
            type="button"
            className="border border-[var(--line)] px-2 py-1 text-left text-xs text-[var(--navy)] focus-visible:outline focus-visible:outline-2"
            onClick={() => void ask(item)}
            disabled={loading}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {turns.length === 0 ? (
          <PageState
            kind="empty"
            title="No Results"
            message="No Copilot questions in this investigation session yet."
            compact
          />
        ) : (
          turns.map((turn, index) => (
            <article key={`${turn.session_id}-${index}`} className="svk-message svk-card p-3 text-sm" data-tone="violet">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--violet)]">AI answer</p>
              <p className="font-medium text-[var(--navy)]">Officer: {turn.question}</p>
              <pre className="mt-2 whitespace-pre-wrap font-sans text-sm">{turn.answer}</pre>
              {turn.insufficient_evidence ? (
                <p className="mt-2 text-sm text-[var(--saffron)]">Insufficient evidence to answer confidently.</p>
              ) : null}
              {turn.source_refs.length ? (
                <div className="svk-card mt-2 p-3" data-tone="indigo">
                  <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--indigo)]">Source evidence</p>
                  <ul className="mt-1 space-y-1 text-xs">
                  {turn.source_refs.map((ref) => (
                    <li key={`${turn.question}-${ref.id}`}>
                      {ref.kind === "evidence" ? (
                        <a className="text-[var(--navy)] underline" href={`#evidence-${ref.id}`}>
                          {ref.label}: {ref.id}
                        </a>
                      ) : (
                        <span>
                          {ref.label}: {ref.id}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
                </div>
              ) : null}
              {turn.hybrid_used ? (
                <p className="mt-2 text-xs text-[var(--saffron)]">{turn.data_mode_notice}</p>
              ) : null}
            </article>
          ))
        )}
        {loading ? <PageState kind="loading" message="Retrieving stored evidence…" compact /> : null}
      </div>

      {latest?.recommended_action ? (
        <p className="text-sm">
          Recommended action: <span className="font-medium">{latest.recommended_action}</span>
        </p>
      ) : null}

      <form
        className="space-y-2"
        onSubmit={(event) => {
          event.preventDefault();
          void ask(question);
        }}
      >
        <label className="block text-sm">
          Ask about this project
          <textarea
            className="svk-textarea mt-1"
            rows={3}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Why is this project flagged?"
          />
        </label>
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="svk-btn disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </section>
  );
}
