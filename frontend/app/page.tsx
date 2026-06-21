'use client';

import { useState } from 'react';

const EXAMPLES = [
  'Silver cylindrical bracket arrived without labels, came with PO-2024-0445',
  'Large red brake caliper assembly, no serial number on the part',
  'Which suppliers have the highest defect rates this month?',
  'What are our biggest cost overruns by part category this quarter?',
  'Combined view of supplier defect rates and spend vs budget',
];

type WorkflowResult = {
  query_type: string;
  identified_part: Record<string, unknown> | null;
  identification_confidence: number;
  recovered_serial: string | null;
  recovered_part_number: string | null;
  target_business_unit: string | null;
  priority: string;
  contact_person: string | null;
  storage_location: string | null;
  qc_required: boolean;
  action_plan: string | null;
  escalated: boolean;
  escalation_reason: string | null;
  investigation_package: Record<string, unknown> | null;
  supply_chain_answer: string | null;
  finance_answer: string | null;
  final_answer: string | null;
};

type AgentEvent = { agent: string; update: Record<string, unknown> };

const PRIORITY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  normal: 'bg-blue-100 text-blue-700 border-blue-200',
  low: 'bg-gray-100 text-gray-500 border-gray-200',
};

const AGENT_LABELS: Record<string, string> = {
  supervisor: 'Supervisor',
  part_identifier: 'Part Identifier',
  serial_resolver: 'Serial Resolver',
  router: 'Router',
  action_recommender: 'Action Plan',
  escalation: 'Escalation',
  supply_chain: 'Supply Chain',
  finance: 'Finance',
  synthesizer: 'Synthesizer',
};

function agentSummary(agent: string, update: Record<string, unknown>): string {
  switch (agent) {
    case 'supervisor':
      return `${String(update.query_type ?? 'unknown')} query`;
    case 'part_identifier': {
      const part = update.identified_part as Record<string, string> | null;
      if (part?.part_number) return `${part.part_number} — ${Math.round(Number(update.identification_confidence ?? 0) * 100)}%`;
      return 'no catalog match';
    }
    case 'serial_resolver':
      return update.recovered_serial ? String(update.recovered_serial) : 'serial not recovered';
    case 'router':
      return update.target_business_unit ? String(update.target_business_unit) : 'routing complete';
    case 'action_recommender':
      return 'instructions generated';
    case 'escalation':
      return 'escalated — human review required';
    case 'supply_chain':
    case 'finance':
      return 'analysis complete';
    case 'synthesizer':
      return 'combined answer ready';
    default:
      return 'complete';
  }
}

function Pct({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const cls = pct >= 70 ? 'text-green-600' : pct >= 50 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`font-mono font-semibold ${cls}`}>{pct}%</span>;
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-2">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">{title}</p>
      </div>
      <div className="px-4 py-4">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-0.5">{label}</p>
      <div className="text-sm text-gray-900">{value}</div>
    </div>
  );
}

function StatusBadge({ label, color }: { label: string; color: 'green' | 'red' | 'blue' }) {
  const cls = {
    green: 'bg-green-100 text-green-700 border-green-200',
    red: 'bg-red-100 text-red-700 border-red-200',
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
  }[color];
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${cls}`}>
      {label}
    </span>
  );
}

function AgentTrace({ events, loading }: { events: AgentEvent[]; loading: boolean }) {
  if (events.length === 0 && !loading) return null;
  return (
    <div className="mt-4 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">Agent Trace</p>
      <div className="space-y-2.5">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3 text-sm">
            <span className="text-green-500 text-base leading-none mt-px">✓</span>
            <span className="font-medium text-gray-700 w-36 shrink-0">{AGENT_LABELS[e.agent] ?? e.agent}</span>
            <span className="text-gray-400 text-xs mt-0.5">{agentSummary(e.agent, e.update)}</span>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-3">
            <span className="inline-block w-3.5 h-3.5 rounded-full border-2 border-gray-200 border-t-gray-500 animate-spin" />
            <span className="text-gray-400 text-xs">Running next agent…</span>
          </div>
        )}
      </div>
    </div>
  );
}

function PartsResult({ r }: { r: WorkflowResult }) {
  const part = (r.identified_part ?? {}) as Record<string, string>;
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <StatusBadge label="Identified & Routed" color="green" />
        <span className="text-xs text-gray-400">Parts workflow complete</span>
      </div>

      <Card title="Identified Part">
        <div className="grid grid-cols-2 gap-4">
          <Row label="Part number" value={<span className="font-mono">{String(part.part_number ?? '—')}</span>} />
          <Row label="Name" value={String(part.part_name ?? part.name ?? '—')} />
          <Row label="Category" value={String(part.category ?? '—')} />
          <Row label="ID confidence" value={<Pct value={r.identification_confidence} />} />
        </div>
      </Card>

      <Card title="Serial Recovery">
        <div className="grid grid-cols-2 gap-4">
          <Row label="Serial number" value={<span className="font-mono">{r.recovered_serial ?? '—'}</span>} />
          <Row label="Part number" value={<span className="font-mono">{r.recovered_part_number ?? '—'}</span>} />
        </div>
      </Card>

      <Card title="Routing">
        <div className="grid grid-cols-2 gap-4">
          <Row label="Business unit" value={<span className="font-medium">{r.target_business_unit ?? '—'}</span>} />
          <Row
            label="Priority"
            value={
              <span className={`inline-block mt-0.5 px-2 py-0.5 rounded text-xs font-medium border ${PRIORITY_BADGE[r.priority] ?? PRIORITY_BADGE.normal}`}>
                {r.priority}
              </span>
            }
          />
          <Row label="Contact" value={r.contact_person ?? '—'} />
          <Row label="Storage" value={<span className="font-mono text-xs">{r.storage_location ?? '—'}</span>} />
          <Row
            label="QC required"
            value={
              <span className={r.qc_required ? 'text-orange-600 font-medium' : 'text-green-600 font-medium'}>
                {r.qc_required ? 'Yes' : 'No'}
              </span>
            }
          />
        </div>
      </Card>

      {r.action_plan && (
        <Card title="Action Plan">
          <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{r.action_plan}</p>
        </Card>
      )}
    </div>
  );
}

function EscalationResult({ r }: { r: WorkflowResult }) {
  const pkg = (r.investigation_package ?? {}) as Record<string, string>;
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <StatusBadge label="Escalated" color="red" />
        <span className="text-xs text-gray-400">Human review required</span>
      </div>

      <Card title="Reason">
        <p className="text-sm text-gray-700">{r.escalation_reason}</p>
      </Card>

      {Object.keys(pkg).length > 0 && (
        <Card title="Investigation Package">
          <div className="grid grid-cols-2 gap-4">
            {pkg.best_guess && (
              <Row
                label="Best guess"
                value={`${pkg.best_guess} (${Math.round(Number(pkg.best_guess_confidence ?? 0) * 100)}%)`}
              />
            )}
            {pkg.quarantine_location && (
              <Row label="Quarantine location" value={<span className="font-mono text-xs">{String(pkg.quarantine_location)}</span>} />
            )}
            {pkg.temp_label && (
              <Row label="Temp label" value={<span className="font-mono text-xs">{String(pkg.temp_label)}</span>} />
            )}
            {pkg.recommended_specialist && (
              <Row label="Specialist needed" value={String(pkg.recommended_specialist)} />
            )}
          </div>
        </Card>
      )}
    </div>
  );
}

function AnalysisResult({ r }: { r: WorkflowResult }) {
  const content = r.final_answer ?? r.supply_chain_answer ?? r.finance_answer ?? '';
  const label =
    r.query_type === 'finance' ? 'Finance Analysis'
    : r.query_type === 'supply_chain' ? 'Supply Chain Analysis'
    : 'Analysis';
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <StatusBadge label={label} color="blue" />
      </div>
      <Card title="Findings">
        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{content}</p>
      </Card>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trace, setTrace] = useState<AgentEvent[]>([]);

  async function submit() {
    if (!query.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setTrace([]);
    try {
      const res = await fetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      });
      if (!res.body) throw new Error('No response body');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';
        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const text = line.slice(6).trim();
            if (!text) continue;
            try {
              const data = JSON.parse(text);
              if (data.type === 'agent') {
                setTrace(prev => [...prev, { agent: data.agent, update: data.update }]);
              } else if (data.type === 'complete') {
                setResult(data.result as WorkflowResult);
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (e) {
              if (e instanceof SyntaxError) continue;
              throw e;
            }
          }
        }
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Parts Intelligence</h1>
          <p className="mt-1 text-sm text-gray-400">
            Identify untagged parts · Recover serial numbers · Route to business units · Supply chain &amp; finance analysis
          </p>
        </div>

        {/* Input */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <textarea
            className="w-full resize-none border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"
            rows={3}
            placeholder="Describe a part or ask a supply chain / finance question…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit(); }}
          />

          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map(q => (
              <button
                key={q}
                onClick={() => setQuery(q)}
                className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-500 rounded-full transition-colors"
              >
                {q.length > 52 ? q.slice(0, 52) + '…' : q}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-300">⌘ + Enter to run</p>
            <button
              onClick={submit}
              disabled={loading || !query.trim()}
              className="px-5 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Running…' : 'Run workflow'}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Live agent trace */}
        <AgentTrace events={trace} loading={loading} />

        {/* Result */}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            {result.escalated
              ? <EscalationResult r={result} />
              : result.action_plan
              ? <PartsResult r={result} />
              : <AnalysisResult r={result} />
            }
          </div>
        )}
      </div>
    </main>
  );
}
