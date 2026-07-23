import { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartColumn, faKey, faMagnifyingGlass, faSpinner, faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons';
import styles from "./ResultViewer.module.css";
import ReactMarkdown from "react-markdown";
import { useTranslation } from '../i18n';
import { extractFieldsWithGroq, analyzeConstat, saveConstat, saveConstatReport } from "../api/client";

interface Props {
  data: any;
  onSearchFromConstat: (marque: string, type: string, damage: string, assurance: string) => void;
}

const OUR_ASSURANCE = "comar";

function getSearchParamsForOurVehicle(result: any) {
  const assurance_a = (result.assurance_a || "").toLowerCase();
  const assurance_b = (result.assurance_b || "").toLowerCase();

  if (assurance_a.includes(OUR_ASSURANCE)) {
    return {
      marque:    result.vehicule_a_marque || "",
      type:      result.vehicule_a_type   || "",
      damage:    result.degats_vehicule_a || "",
      assurance: result.assurance_a       || "",
    };
  }
  if (assurance_b.includes(OUR_ASSURANCE)) {
    return {
      marque:    result.vehicule_b_marque || "",
      type:      result.vehicule_b_type   || "",
      damage:    result.degats_vehicule_b || "",
      assurance: result.assurance_b       || "",
    };
  }
  return {
    marque:    result.vehicule_a_marque || "",
    type:      result.vehicule_a_type   || "",
    damage:    result.degats_vehicule_a || "",
    assurance: "",
  };
}

export default function ResultViewer({ data, onSearchFromConstat }: Props) {
  if (!data) return null;
  const { t } = useTranslation();

  const [extracting, setExtracting]   = useState(false);
  const [extracted, setExtracted]     = useState<any>(null);
  const [analyzing, setAnalyzing]     = useState(false);
  const [isSavingConstat, setIsSavingConstat] = useState(false);
  const [agentReport, setAgentReport] = useState<any>(null);
  const [savedConstatId, setSavedConstatId] = useState<number | null>(null);

  const fullText = data.full_text;

  const persistConstat = async (result?: any) => {
    setIsSavingConstat(true);
    try {
      const savedConstat = await saveConstat({
        file_id: data.file_id,
        full_text: data.full_text,
        page_count: data.page_count,
        blurred_pdf_url: data.blurred_pdf_url,
        ...(result ? {
          date_accident: result.date_accident,
          heure: result.heure,
          lieu: result.lieu,
          blesses: result.blesses,
          vehicule_a_marque: result.vehicule_a_marque,
          vehicule_a_type: result.vehicule_a_type,
          vehicule_a_immatriculation: result.vehicule_a_immatriculation,
          assurance_a: result.assurance_a,
          degats_vehicule_a: result.degats_vehicule_a,
          vehicule_b_marque: result.vehicule_b_marque,
          vehicule_b_type: result.vehicule_b_type,
          vehicule_b_immatriculation: result.vehicule_b_immatriculation,
          assurance_b: result.assurance_b,
          degats_vehicule_b: result.degats_vehicule_b,
          observations: result.observations,
        } : {}),
      });

      if (savedConstat?.id) {
        setSavedConstatId(savedConstat.id);
        return savedConstat.id;
      }

      return null;
    } catch (saveErr) {
      console.error("Failed to save constat", saveErr);
      return null;
    } finally {
      setIsSavingConstat(false);
    }
  };

  const handleExtract = async () => {
    setExtracting(true);
    try {
      const result = await extractFieldsWithGroq(fullText);
      setExtracted(result);
      await persistConstat(result);

      const p = getSearchParamsForOurVehicle(result);
      if (p.marque || p.damage) onSearchFromConstat(p.marque, p.type, p.damage, p.assurance);
    } catch (err) {
      console.error("Extraction failed", err);
      alert(t('result.extractionFailed'));
    } finally {
      setExtracting(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const currentConstatId = savedConstatId ?? await persistConstat(extracted ?? null);
      if (!currentConstatId) {
        throw new Error('Constat save not available');
      }

      const report = await analyzeConstat(fullText);
      setAgentReport(report);

      try {
        await saveConstatReport(currentConstatId, report);
        console.log("Constat report saved to database");
      } catch (saveErr) {
        console.error("Failed to save constat report", saveErr);
      }
    } catch (err) {
      console.error("Analysis failed", err);
      alert(t('result.analysisFailed'));
    } finally {
      setAnalyzing(false);
    }
  };
  const extractedFields = extracted
    ? Object.entries(extracted).filter(([_, v]) => v)
    : [];

  return (
    <div>
      <div className={styles.card}>

        {/* ── Header ── */}
        <div className={styles.cardTop}>
          <div>
            <span className={styles.rank}>{t('result.title')}</span>
            <div className={styles.filename}>{t('result.constatExtracted')}</div>
          </div>
          <div className={styles.pageBadge}>
            {extracted
              ? `${extractedFields.length} champs`
              : `${data.page_count ?? 1} page(s)`}
          </div>
        </div>

        {/* ── Content ── */}
        <div className={styles.markdownBox}>
          {extracted ? (
            <pre className={styles.markdownText}>
              {extractedFields.map(([label, value]) =>
                `${(label as string).padEnd(20)} ${value}`
              ).join("\n")}
            </pre>
          ) : (
            <div className={styles.markdownText}>
              <ReactMarkdown>{fullText}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* ── Extract button ── */}
        {fullText && !extracted && (
          <button
            className={styles.btnSearch}
            onClick={handleExtract}
            disabled={extracting}
            style={{ marginTop: "1rem" }}
          >
            {extracting ? <><FontAwesomeIcon icon={faSpinner} spin aria-hidden="true" /> Extraction en cours...</> : <><FontAwesomeIcon icon={faWandMagicSparkles} aria-hidden="true" /> Extraire les champs & Rechercher</>}
          </button>
        )}

        {/* ── Re-search button ── */}
        {extracted && (
          <button
            className={styles.btnSearch}
            onClick={() => {
              const p = getSearchParamsForOurVehicle(extracted);
              onSearchFromConstat(p.marque, p.type, p.damage, p.assurance);
            }}
            style={{ marginTop: "1rem" }}
          >
            <><FontAwesomeIcon icon={faMagnifyingGlass} aria-hidden="true" /> Rechercher des rapports similaires</>
          </button>
        )}

        {/* ── Analyze button ── */}
        {fullText && !agentReport && (
          <button
            className={styles.btnSearch}
            onClick={handleAnalyze}
            disabled={analyzing || extracting || isSavingConstat}
            style={{ marginTop: "0.5rem" }}
          >
            {analyzing ? <><FontAwesomeIcon icon={faSpinner} spin aria-hidden="true" /> Analyse en cours...</> : <><FontAwesomeIcon icon={faChartColumn} aria-hidden="true" /> Estimer le coût de réparation</>}
          </button>
        )}

        {/* ── Agent report ── */}
        {agentReport && (
          <div style={{
            marginTop: "1rem",
            background: "var(--bg3)",
            borderRadius: 12,
            padding: "1rem",
            border: "1px solid var(--border)",
          }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: "var(--accent2, #7c3aed)" }}>
              <><FontAwesomeIcon icon={faChartColumn} aria-hidden="true" /> ESTIMATION DES COÛTS</>
            </div>

            {/* Severity + cost badges */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
              <span style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "4px 10px", fontSize: 12 }}>
                Sévérité: <strong>{agentReport.severity ?? "—"}</strong>
              </span>

                {agentReport.matched_keywords?.length > 0 && (
                  <span style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "4px 10px", fontSize: 12, color: "var(--text3)" }}>
                    <><FontAwesomeIcon icon={faKey} aria-hidden="true" /> {agentReport.matched_keywords.join(", ")}</>
                  </span>
                )}
                {agentReport.cost_median != null && (
                <span style={{
                  background: "#f0fdf4", border: "1px solid #22c55e",
                  borderRadius: 8, padding: "4px 10px", fontSize: 12,
                  fontWeight: 700, color: "#16a34a",
                }}>
                  ~{agentReport.cost_median} DT
                </span>
              )}

              {agentReport.cost_min != null && agentReport.cost_max != null && (
                <span style={{
                  background: "var(--bg2)", border: "1px solid var(--border)",
                  borderRadius: 8, padding: "4px 10px", fontSize: 12, color: "var(--text2)",
                }}>
                  {agentReport.cost_min} – {agentReport.cost_max} DT
                </span>
              )}

              {agentReport.keywords?.length > 0 && (
                <span style={{
                  background: "var(--bg2)", border: "1px solid var(--border)",
                  borderRadius: 8, padding: "4px 10px", fontSize: 12, color: "var(--text3)",
                }}>
                  {agentReport.keywords.join(", ")}
                </span>
              )}
            </div>

            {agentReport.review && (
              <div style={{ display: "grid", gap: 6, marginBottom: 10 }}>
                <span style={{ fontSize: 12, color: "var(--text2)" }}>Confidence: {agentReport.review.confidence}</span>
                <span style={{ fontSize: 12, color: "var(--text2)" }}>Comparable cases: {agentReport.review.sample_size}</span>

                {agentReport.review.requires_manual_review && (
                  <div style={{ color: "#b45309", fontWeight: 700, fontSize: 12 }}>
                    Expert review required
                  </div>
                )}

                {agentReport.review.warnings?.map((warning: string) => (
                  <p key={warning} style={{ margin: 0, fontSize: 12, color: "var(--text2)" }}>{warning}</p>
                ))}
              </div>
            )}

            {agentReport.estimate_disclaimer && (
              <p style={{ margin: "0 0 8px", fontSize: 12, color: "var(--text3)" }}>{agentReport.estimate_disclaimer}</p>
            )}

            {/* Similar cases */}
            {agentReport.similar_cases?.length > 0 && (
              <div>
                <div style={{
                  fontSize: 11, fontWeight: 700, textTransform: "uppercase",
                  color: "var(--text3)", marginBottom: 6, letterSpacing: "0.05em",
                }}>
                  Cas similaires
                </div>
                {agentReport.similar_cases.map((c: any, i: number) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between",
                    fontSize: 12, padding: "5px 0",
                    borderBottom: "1px solid var(--border)",
                    color: "var(--text2)",
                  }}>
                    <span>{c.marque} — {(c.damage || "").slice(0, 45)}{(c.damage || "").length > 45 ? "…" : ""}</span>
                    <strong style={{ color: "var(--text)" }}>{c.total_ttc ? `${c.total_ttc} DT` : "—"}</strong>
                  </div>
                ))}
              </div>
            )}

            {/* No cost data fallback */}
            {agentReport.cost_median == null && (
              <div style={{ fontSize: 13, color: "var(--text3)", marginTop: 8 }}>
                Pas assez de données pour estimer le coût.
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
