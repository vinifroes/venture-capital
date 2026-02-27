import { useEffect, useMemo, useState } from "react";
import documentsIndex from "./documents_json/index.json";
import "./App.css";

const documentModules = import.meta.glob("./documents_json/**/*.json", { eager: true });

const EXECUTION_STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "awaiting_signatures", label: "Awaiting Signatures" },
  { value: "signed", label: "Signed" },
  { value: "registered", label: "Registered" },
];

const EXECUTION_STATUS_LABELS = {
  draft: "Draft",
  awaiting_signatures: "Awaiting Signatures",
  signed: "Signed",
  registered: "Registered",
};

const STAGE_CONTEXT = {
  "2021-12-16": {
    title: "Foundation",
    headline: "CTO Eliel Oliveira started the company.",
    overview:
      "This stage formalizes the company constitution, initial capitalization, and baseline corporate records.",
    stakeholders: ["Eliel Oliveira", "Hage Sistemas"],
  },
  "2022-08-21": {
    title: "Foundation Realignment",
    headline: "CSO Rogério Diniz bought 25% from Eliel.",
    overview:
      "This stage records the first ownership transfer and the corporate updates required after the transaction.",
    stakeholders: ["Eliel Oliveira", "Rogério Diniz", "Hage Sistemas"],
  },
  "2025-01-01": {
    title: "Founders Agreement and CEO Appointment",
    headline: "Founders Agreement executed and Eliel also became CEO.",
    overview:
      "This stage consolidates founder governance rights, executive roles, and key corporate decision rules.",
    stakeholders: ["Eliel Oliveira", "Rogério Diniz", "Hage Sistemas"],
  },
  "2026-02-01": {
    title: "Pool Formation",
    headline: "Pools created: 10% performance, 5% talents, and 3% advisors.",
    overview:
      "This stage defines pool reserves, reversion rules, and integration with purchase and performance agreements.",
    stakeholders: ["Eliel Oliveira", "Rogério Diniz", "Vinicyus Froes", "Hage Sistemas"],
  },
  "2026-02-10": {
    title: "Foundation Realignment",
    headline:
      "Vinicyus Froes acquired 5% pro-rata and executed the Performance Equity Agreement.",
    overview:
      "This stage closes the secondary transfers and the performance-based equity framework implementation.",
    stakeholders: ["Vinicyus Froes", "Eliel Oliveira", "Rogério Diniz", "Hage Sistemas"],
  },
};

function slugify(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function parseHashRoute() {
  const raw = window.location.hash.replace(/^#\/?/, "").trim();

  if (!raw) {
    return { view: "timeline" };
  }

  const parts = raw.split("/");

  if (parts[0] === "stage" && parts[1]) {
    if (parts[2] === "doc" && parts[3]) {
      return {
        view: "document",
        stageSlug: decodeURIComponent(parts[1]),
        docSlug: decodeURIComponent(parts[3]),
      };
    }

    return {
      view: "stage",
      stageSlug: decodeURIComponent(parts[1]),
    };
  }

  return { view: "not-found" };
}

function formatDate(isoDate) {
  const date = new Date(`${isoDate}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

function formatType(type) {
  return (type || "legal_document")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function buildStageHref(stageSlug) {
  return `#/stage/${encodeURIComponent(stageSlug)}`;
}

function buildDocumentHref(stageSlug, docSlug) {
  return `#/stage/${encodeURIComponent(stageSlug)}/doc/${encodeURIComponent(docSlug)}`;
}

function toModulePath(indexPath) {
  return `./${indexPath.replace(/^src\//, "")}`;
}

function getDocumentPayload(indexEntryPath) {
  const modulePath = toModulePath(indexEntryPath);
  const moduleValue = documentModules[modulePath];
  return moduleValue?.default ?? moduleValue ?? null;
}

function normalizeExecution(execution, fallbackStatus) {
  const allowedStatuses = new Set(["draft", "awaiting_signatures", "signed", "registered"]);
  const status = allowedStatuses.has(execution?.status)
    ? execution.status
    : allowedStatuses.has(fallbackStatus)
      ? fallbackStatus
      : "draft";

  return {
    status,
    signature_standard: execution?.signature_standard ?? "icp_brasil_qualified",
    signed_at: execution?.signed_at ?? null,
    provider: execution?.provider ?? null,
    evidence: {
      sha256: execution?.evidence?.sha256 ?? null,
      validation_report: execution?.evidence?.validation_report ?? null,
      registry_protocol: execution?.evidence?.registry_protocol ?? null,
    },
  };
}

function buildStagesFromJson() {
  const groupedStages = new Map();

  for (const indexEntry of documentsIndex.documents) {
    if (indexEntry.status === "legacy-model") {
      continue;
    }

    const payload = getDocumentPayload(indexEntry.path);
    if (!payload) {
      continue;
    }

    const stageDate = payload.timeline?.stage_date ?? indexEntry.stage_date;
    const stageName = payload.timeline?.stage_name ?? indexEntry.stage_name ?? "Unclassified Stage";
    const stageKey = `${stageDate}::${stageName}`;

    if (!groupedStages.has(stageKey)) {
      const context = STAGE_CONTEXT[stageDate] ?? {};
      groupedStages.set(stageKey, {
        key: stageKey,
        slug: `${stageDate}-${slugify(stageName)}`,
        date: stageDate,
        title: context.title ?? stageName,
        stageName,
        headline: context.headline ?? `${stageName} legal documentation stage.`,
        overview:
          context.overview ??
          "This stage groups the legal documents and corporate records available in the repository.",
        stakeholders: context.stakeholders ?? [],
        documents: [],
      });
    }

    const stage = groupedStages.get(stageKey);
    const titlePt = payload.document?.title?.pt ?? indexEntry.id;
    const titleEn = payload.document?.title?.en ?? "";
    const firstIntroClause = payload.intro?.[0]?.pt ?? "";
    const execution = normalizeExecution(payload.execution, indexEntry.status);

    stage.documents.push({
      slug: indexEntry.id,
      id: indexEntry.id,
      type: payload.document?.type ?? indexEntry.type,
      status: indexEntry.status,
      source: indexEntry.source,
      path: indexEntry.path,
      titlePt,
      titleEn,
      summary: firstIntroClause || "Structured bilingual legal document.",
      executionDate: payload.timeline?.execution_date ?? stageDate,
      payload: {
        ...payload,
        execution,
      },
      execution,
    });
  }

  return Array.from(groupedStages.values())
    .map((stage) => ({
      ...stage,
      documents: stage.documents.sort((a, b) => a.id.localeCompare(b.id)),
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function renderPartyDetails(party) {
  const details = [party.tax_id, party.email, party.phone].filter(Boolean).join(" · ");
  const labels = (party.labels || [])
    .map((label) => [label.pt, label.en].filter(Boolean).join(" / "))
    .join("; ");
  const notes = (party.notes || []).join(" ");

  return { details, labels, notes };
}

function isHttpUrl(value) {
  if (!value) {
    return false;
  }

  return /^https?:\/\//i.test(value);
}

function filterDocumentsByStatus(documents, statusFilter) {
  if (statusFilter === "all") {
    return documents;
  }
  return documents.filter((document) => document.execution.status === statusFilter);
}

function getStatusLabel(status) {
  return EXECUTION_STATUS_LABELS[status] ?? "Unknown";
}

function StatusBadge({ status }) {
  return (
    <span className={`status-badge status-${status}`}>
      {getStatusLabel(status)}
    </span>
  );
}

function AppHeader({ dateRange, statusFilter, onStatusFilterChange, visibleCount, totalCount }) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">Hage Legal Workspace</p>
        <h1>Stakeholder Legal Documentation</h1>
        <p className="subtitle">
          MD drafts converted to JSON and organized by stage for interface navigation ({dateRange}).
        </p>
      </div>
      <div className="header-actions">
        <div className="status-filter">
          <label htmlFor="status-filter">Execution Status</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(event) => onStatusFilterChange(event.target.value)}
          >
            {EXECUTION_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="filter-meta">
            {visibleCount} of {totalCount} documents
          </p>
        </div>
        <a className="home-link" href="#/">
          Timeline Home
        </a>
      </div>
    </header>
  );
}

function Breadcrumbs({ stage, document }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <a href="#/">Timeline</a>
      {stage && (
        <>
          <span>/</span>
          <a href={buildStageHref(stage.slug)}>{stage.title}</a>
        </>
      )}
      {document && (
        <>
          <span>/</span>
          <span>{document.titlePt}</span>
        </>
      )}
    </nav>
  );
}

function TimelinePage({ stages, statusFilter }) {
  if (!stages.length) {
    return (
      <section className="panel">
        <h2>No Documents Found</h2>
        <p>
          {statusFilter === "all"
            ? "Generate documents with `npm run documents:build` and refresh this page."
            : "No documents match the selected execution status filter."}
        </p>
      </section>
    );
  }

  return (
    <section>
      <div className="page-intro">
        <h2>Company Stages</h2>
        <p>Select a stage to access its generated legal documents.</p>
      </div>

      <div className="timeline-grid">
        {stages.map((stage) => (
          <article className="timeline-card" key={stage.key}>
            <p className="timeline-date">{formatDate(stage.date)}</p>
            <h3>{stage.title}</h3>
            <p className="timeline-headline">{stage.headline}</p>
            <p className="timeline-overview">{stage.overview}</p>
            <p className="timeline-meta">
              Documents: {stage.filteredDocuments.length} / {stage.documents.length}
            </p>
            <a className="button-link" href={buildStageHref(stage.slug)}>
              Open Stage
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

function StagePage({ stage, filteredDocuments, statusFilter }) {
  return (
    <section>
      <div className="page-intro">
        <h2>{stage.title}</h2>
        <p>{stage.headline}</p>
      </div>

      <div className="stage-meta">
        <div>
          <h3>Effective Date</h3>
          <p>{formatDate(stage.date)}</p>
        </div>
        <div>
          <h3>Stage Scope</h3>
          <p>{stage.overview}</p>
        </div>
      </div>

      <section className="panel">
        <h3>Stakeholders in this stage</h3>
        <ul>
          {stage.stakeholders.length ? (
            stage.stakeholders.map((stakeholder) => <li key={stakeholder}>{stakeholder}</li>)
          ) : (
            <li>No stakeholder metadata defined for this stage yet.</li>
          )}
        </ul>
      </section>

      <section className="panel">
        <h3>Documents</h3>
        {filteredDocuments.length ? (
          <div className="documents-grid">
            {filteredDocuments.map((document) => (
              <article className="document-card" key={document.id}>
                <div className="document-header">
                  <p className="document-type">{formatType(document.type)}</p>
                  <StatusBadge status={document.execution.status} />
                </div>
                <h4>{document.titlePt}</h4>
                <p>{document.summary}</p>
                <a className="button-link" href={buildDocumentHref(stage.slug, document.slug)}>
                  Open Document
                </a>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty-message">
            No documents in this stage match filter <code>{statusFilter}</code>.
          </p>
        )}
      </section>
    </section>
  );
}

function EvidenceValue({ value }) {
  if (!value) {
    return <span>Not available</span>;
  }

  if (isHttpUrl(value)) {
    return (
      <a href={value} target="_blank" rel="noreferrer">
        {value}
      </a>
    );
  }

  return <code>{value}</code>;
}

function DocumentPage({ stage, document }) {
  const payload = document.payload;
  const sourcePath = payload.meta?.source?.path ?? document.source;
  const execution = document.execution;
  const shouldRenderEvidence = ["signed", "registered"].includes(execution.status);
  const evidence = execution.evidence ?? {};

  return (
    <section>
      <div className="page-intro">
        <h2>{document.titlePt}</h2>
        <p>{document.titleEn || "Bilingual legal document (pt-BR / en-US)."}</p>
      </div>

      <div className="stage-meta">
        <div>
          <h3>Stage</h3>
          <p>
            {stage.title} ({formatDate(stage.date)})
          </p>
        </div>
        <div>
          <h3>Document Type</h3>
          <p>{formatType(document.type)}</p>
        </div>
      </div>

      <section className="panel">
        <h3>Legal Execution</h3>
        <div className="execution-meta">
          <p>
            Status: <StatusBadge status={execution.status} />
          </p>
          <p>
            Signature standard: <code>{execution.signature_standard}</code>
          </p>
          <p>
            Signed at: <code>{execution.signed_at ?? "N/A"}</code>
          </p>
          <p>
            Provider: <code>{execution.provider ?? "to-be-defined"}</code>
          </p>
        </div>
      </section>

      {shouldRenderEvidence ? (
        <section className="panel">
          <h3>Execution Evidence</h3>
          <ul>
            <li>
              SHA-256: <EvidenceValue value={evidence.sha256} />
            </li>
            <li>
              Validation report: <EvidenceValue value={evidence.validation_report} />
            </li>
            <li>
              Registry protocol: <EvidenceValue value={evidence.registry_protocol} />
            </li>
          </ul>
        </section>
      ) : null}

      <section className="panel">
        <h3>Parties</h3>
        <ul>
          {(payload.parties ?? []).map((party, index) => {
            const { details, labels, notes } = renderPartyDetails(party);
            return (
              <li key={`${party.name}-${index}`}>
                <strong>{party.name}</strong>
                {details ? <div className="party-meta">{details}</div> : null}
                {labels ? <div className="party-meta">{labels}</div> : null}
                {notes ? <div className="party-meta">{notes}</div> : null}
              </li>
            );
          })}
        </ul>
      </section>

      {(payload.intro ?? []).length ? (
        <section className="panel">
          <h3>Opening Clauses</h3>
          <ul>
            {(payload.intro ?? []).map((clause, index) => (
              <li key={`intro-${index}`}>
                <span>
                  {clause.ref ? `${clause.ref} ` : ""}
                  {clause.pt}
                </span>
                {clause.en ? <div className="clause-translation">{clause.en}</div> : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="panel">
        <h3>Sections and Clauses</h3>
        <div className="clauses">
          {(payload.sections ?? []).map((section, sectionIndex) => (
            <article className="clause-block" key={`section-${section.ref || sectionIndex}`}>
              <h4>{[section.ref, section.title?.pt].filter(Boolean).join(". ")}</h4>
              {section.title?.en ? <p className="clause-subtitle">{section.title.en}</p> : null}
              <ul>
                {(section.clauses ?? []).map((clause, clauseIndex) => (
                  <li key={`clause-${sectionIndex}-${clauseIndex}`}>
                    <span>
                      {clause.ref ? `${clause.ref} ` : ""}
                      {clause.pt}
                    </span>
                    {clause.en ? <div className="clause-translation">{clause.en}</div> : null}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      {payload.language_rule?.pt ? (
        <section className="panel note-panel">
          <h3>Language Rule</h3>
          <p>{payload.language_rule.pt}</p>
        </section>
      ) : null}

      <section className="panel note-panel">
        <h3>Implementation Note</h3>
        <p>
          Source: <code>{sourcePath}</code>
        </p>
        <p>
          Meta status: <code>{document.status}</code> | Generated on: <code>{payload.meta?.generated_on}</code>
        </p>
      </section>
    </section>
  );
}

function NotFound() {
  return (
    <section className="panel">
      <h2>Page Not Found</h2>
      <p>The requested route does not match a stage or document page.</p>
      <a className="button-link" href="#/">
        Return to Timeline
      </a>
    </section>
  );
}

const STAGES = buildStagesFromJson();
const STAGE_BY_SLUG = Object.fromEntries(STAGES.map((stage) => [stage.slug, stage]));

export default function App() {
  const [route, setRoute] = useState(() => parseHashRoute());
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    const handleHashChange = () => setRoute(parseHashRoute());

    window.addEventListener("hashchange", handleHashChange);

    if (!window.location.hash) {
      window.location.hash = "#/";
    } else {
      handleHashChange();
    }

    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const filteredStages = useMemo(() => {
    return STAGES.map((stage) => ({
      ...stage,
      filteredDocuments: filterDocumentsByStatus(stage.documents, statusFilter),
    }));
  }, [statusFilter]);

  const filteredStagesBySlug = useMemo(() => {
    return Object.fromEntries(filteredStages.map((stage) => [stage.slug, stage]));
  }, [filteredStages]);

  const timelineStages = useMemo(() => {
    if (statusFilter === "all") {
      return filteredStages;
    }
    return filteredStages.filter((stage) => stage.filteredDocuments.length > 0);
  }, [filteredStages, statusFilter]);

  const stage = useMemo(() => {
    if (!route.stageSlug) {
      return null;
    }

    return STAGE_BY_SLUG[route.stageSlug] ?? null;
  }, [route.stageSlug]);

  const filteredStage = useMemo(() => {
    if (!route.stageSlug) {
      return null;
    }

    return filteredStagesBySlug[route.stageSlug] ?? null;
  }, [filteredStagesBySlug, route.stageSlug]);

  const document = useMemo(() => {
    if (!stage || !route.docSlug) {
      return null;
    }

    return stage.documents.find((entry) => entry.slug === route.docSlug) ?? null;
  }, [stage, route.docSlug]);

  const dateRange = useMemo(() => {
    if (!STAGES.length) {
      return "no generated stages";
    }
    return `${STAGES[0].date} to ${STAGES[STAGES.length - 1].date}`;
  }, []);

  const totalDocumentCount = useMemo(() => {
    return STAGES.reduce((accumulator, stageEntry) => accumulator + stageEntry.documents.length, 0);
  }, []);

  const visibleDocumentCount = useMemo(() => {
    return filteredStages.reduce(
      (accumulator, stageEntry) => accumulator + stageEntry.filteredDocuments.length,
      0,
    );
  }, [filteredStages]);

  let content = <TimelinePage stages={timelineStages} statusFilter={statusFilter} />;

  if (route.view === "stage") {
    content =
      stage && filteredStage ? (
        <StagePage
          stage={stage}
          filteredDocuments={filteredStage.filteredDocuments}
          statusFilter={statusFilter}
        />
      ) : (
        <NotFound />
      );
  }

  if (route.view === "document") {
    content = stage && document ? <DocumentPage stage={stage} document={document} /> : <NotFound />;
  }

  if (route.view === "not-found") {
    content = <NotFound />;
  }

  return (
    <div className="app-shell">
      <div className="ambient-bg" aria-hidden="true" />
      <main className="layout">
        <AppHeader
          dateRange={dateRange}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          visibleCount={visibleDocumentCount}
          totalCount={totalDocumentCount}
        />
        <Breadcrumbs stage={stage} document={document} />
        {content}
      </main>
    </div>
  );
}
