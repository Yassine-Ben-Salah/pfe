import { useState } from 'react';
import { useSearch } from '../hooks/useSearch';
import { RapportCard } from '../components/RapportCard';
import UploadConstat from '../components/UploadConstat';
import ResultViewer from '../components/ResultViewer';
import { SearchForm } from '../components/SearchForm';
import { PartsCatalogSearch } from '../components/PartsCatalogSearch';
import type { SearchRequest } from '../types/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons';
import styles from './Home.module.css';

interface SearchPrefill {
  marque: string;
  type: string;
  damage: string;
  assurance: string;
}

const DEFAULT_SEARCH_PREFILL: SearchPrefill = {
  marque: '',
  type: '',
  damage: '',
  assurance: '',
};

export default function Home() {
  const [result, setResult] = useState<any>(null);
  const [prefill, setPrefill] = useState<SearchPrefill>(DEFAULT_SEARCH_PREFILL);
  const { results, loading, error, search } = useSearch();

  const handleSearch = (req: SearchRequest) => {
    setPrefill({
      marque: req.marque ?? '',
      type: req.type ?? '',
      damage: req.damage_query ?? '',
      assurance: req.assurance ?? '',
    });
    search(req);
  };

  const handleSearchFromConstat = (
    marque: string,
    type: string,
    damage: string,
    assurance: string
  ) => {
    const request: SearchRequest = {
      marque: marque || null,
      type: type || null,
      damage_query: damage || null,
      assurance: assurance || null,
      top_k: 5,
      semantic_weight: 0.6,
      bm25_weight: 0.4,
      rerank: true,
      score_threshold: null,
    };

    setPrefill({ marque, type, damage, assurance });
    search(request);
  };

  return (
    <div className={styles.page}>
      <section className={styles.heroCard}>
        <div className={styles.headerRow}>
          <div className={styles.heroContent}>
            <div className={styles.eyebrow}>
              <FontAwesomeIcon icon={faWandMagicSparkles} aria-hidden="true" />
              Intelligent claims workspace
            </div>
            <h1 className={styles.title}>AI Constat Analyzer</h1>
            <p className={styles.subtitle}>Turn accident reports into clear case data and comparable repair insights in minutes.</p>
            <div className={styles.heroHighlights}>
              <span>Secure document processing</span>
              <span>Repair case matching</span>
            </div>
          </div>
        </div>
      </section>

      <div className={styles.grid}>
        <UploadConstat onResult={setResult} />
        <div className={styles.resultsCard}>
          <div className={styles.resultsHeader}>
            <div>
              <div className={styles.resultsTitle}>Processed report preview</div>
              <div className={styles.resultsMeta}>Use the results to trigger a targeted repair search.</div>
            </div>
          </div>

          {result ? (
            <div className={styles.resultsList}>
              <ResultViewer data={result} onSearchFromConstat={handleSearchFromConstat} />
            </div>
          ) : (
            <div className={styles.emptyState}>Upload a constat PDF to begin the analysis flow.</div>
          )}
        </div>

        <div className={styles.resultsCard}>
          <div className={styles.resultsHeader}>
            <div>
              <div className={styles.resultsTitle}>Search vehicle repair cases</div>
              <div className={styles.resultsMeta}>Refine part and cost matching by vehicle, damage, or insurer.</div>
            </div>
          </div>
          <SearchForm
            onSearch={handleSearch}
            loading={loading}
            prefillMarque={prefill.marque}
            prefillType={prefill.type}
            prefillDamage={prefill.damage}
            prefillAssurance={prefill.assurance}
          />
          {error && <div className={styles.error}>{error}</div>}
          {results ? (
            results.results.length > 0 ? (
              <div className={styles.resultsList}>
                {results.results.map((item, index) => (
                  <RapportCard
                    key={`${item.filename ?? 'rapport'}-${index}`}
                    result={item}
                    rank={index + 1}
                  />
                ))}
              </div>
            ) : (
              <div className={styles.emptyState}>Aucun résultat trouvé pour cette recherche.</div>
            )
          ) : null}
        </div>

        <div className={styles.resultsCard}>
          <div className={styles.resultsHeader}>
            <div>
              <div className={styles.resultsTitle}>Parts catalog</div>
              <div className={styles.resultsMeta}>Search for spare parts by keyword, brand, or vehicle name.</div>
            </div>
          </div>
          <PartsCatalogSearch />
        </div>
      </div>
    </div>
  );
}
