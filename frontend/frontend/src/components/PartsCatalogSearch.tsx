import { useState, type FormEvent } from 'react';
import { listParts } from '../api/client';
import type { PartItem, PartsListResponse } from '../types/api';
import styles from './PartsCatalogSearch.module.css';

const DEFAULT_LIMIT = 24;

function normalizeText(value?: string | null) {
  return (value ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function matchesQuery(item: PartItem, query: string) {
  const queryTokens = normalizeText(query)
    .split(/\s+/)
    .filter(Boolean);

  if (queryTokens.length === 0) {
    return true;
  }

  const haystack = normalizeText(
    [item.piece_name, item.piece_brand, item.brand, item.car_name]
      .filter(Boolean)
      .join(' ')
  );

  if (queryTokens.every((token) => haystack.includes(token))) {
    return true;
  }

  const tokenSet = new Set(queryTokens);
  const haystackTokens = new Set(haystack.split(/\s+/).filter(Boolean));

  return [...tokenSet].some((token) => haystackTokens.has(token));
}

function getHyphenatedQueryVariants(query: string) {
  const words = query.trim().split(/\s+/).filter(Boolean);

  if (words.length < 2) {
    return [];
  }

  const variants = new Set<string>();

  // Try each adjacent pair as a compound word: "pare choc avant" becomes
  // "pare-choc avant" and "pare choc-avant". This preserves the other words
  // that the API may also use to narrow the search.
  for (let index = 0; index < words.length - 1; index += 1) {
    variants.add([
      ...words.slice(0, index),
      `${words[index]}-${words[index + 1]}`,
      ...words.slice(index + 2),
    ].join(' '));
  }

  variants.add(words.join('-'));
  variants.delete(query.trim());

  return [...variants];
}

export function PartsCatalogSearch() {
  const [q, setQ] = useState('');
  const [brand, setBrand] = useState('');
  const [carName, setCarName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PartsListResponse | null>(null);
  const [page, setPage] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);

  const loadParts = async (nextPage = 0) => {
    if (!q.trim() && !brand.trim() && !carName.trim()) {
      setError('Veuillez saisir au moins un critère de recherche.');
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = {
        q: q.trim() || undefined,
        brand: brand.trim() || undefined,
        car_name: carName.trim() || undefined,
        limit: DEFAULT_LIMIT,
        offset: nextPage * DEFAULT_LIMIT,
      };

      let data = await listParts(params);
      let normalizedItems = (data.items ?? []).filter((item) =>
        matchesQuery(item, `${q} ${brand} ${carName}`)
      );

      // Some catalog entries contain compound words joined by a hyphen while
      // the API performs an exact text search. Retry common hyphenated forms
      // only if the user's original wording did not find anything.
      if (normalizedItems.length === 0 && q.trim()) {
        for (const qVariant of getHyphenatedQueryVariants(q)) {
          const variantData = await listParts({ ...params, q: qVariant });
          const variantItems = (variantData.items ?? []).filter((item) =>
            matchesQuery(item, `${q} ${brand} ${carName}`)
          );

          if (variantItems.length > 0) {
            data = variantData;
            normalizedItems = variantItems;
            break;
          }
        }
      }

      setResult({
        ...data,
        items: normalizedItems,
        count: normalizedItems.length,
      });
      setPage(nextPage);
      setHasSearched(true);
    } catch (err) {
      setError('Impossible de charger les pièces pour le moment.');
      setResult(null);
      setHasSearched(false);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    await loadParts(0);
  };

  const handleLoadMore = async () => {
    if (!result || loading) return;
    await loadParts(page + 1);
  };

  return (
    <div className={styles.container}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label}>Mot-clé</label>
        <input
          className={styles.input}
          type="text"
          placeholder="Nom de pièce, marque, modèle…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />

        <div className={styles.row}>
          <div className={styles.field}>
            <label className={styles.label}>Marque</label>
            <input
              className={styles.input}
              type="text"
              placeholder="ex: Renault"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Véhicule</label>
            <input
              className={styles.input}
              type="text"
              placeholder="ex: Clio"
              value={carName}
              onChange={(e) => setCarName(e.target.value)}
            />
          </div>
        </div>

        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? 'Recherche…' : 'Rechercher des pièces'}
        </button>
      </form>

      {error ? <div className={styles.error}>{error}</div> : null}

      {hasSearched && result ? (
        <div className={styles.summary}>
          {result.count > 0
            ? `Affichage de ${result.items.length} pièce(s) sur ${result.count}`
            : 'Aucune pièce trouvée pour ces critères.'}
        </div>
      ) : null}

      {loading ? (
        <div className={styles.emptyState}>Chargement des pièces…</div>
      ) : result?.items.length ? (
        <>
          <div className={styles.list}>
            {result.items.map((item: PartItem) => (
              <article key={item.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <h3 className={styles.cardTitle}>{item.piece_name || 'Pièce'}</h3>
                  <span className={styles.price}>{formatPrice(item.piece_price)}</span>
                </div>
                <p className={styles.meta}>{item.piece_brand || 'Marque non renseignée'}</p>
                <div className={styles.details}>
                  <span>{item.brand || 'Marque voiture inconnue'}</span>
                  <span>{item.car_name || 'Modèle inconnu'}</span>
                </div>
              </article>
            ))}
          </div>
          {result.count > result.items.length && (
            <button className={styles.loadMoreButton} type="button" onClick={handleLoadMore}>
              Charger plus de résultats
            </button>
          )}
        </>
      ) : (
        <div className={styles.emptyState}>
          Recherchez des pièces par mot-clé, marque ou modèle de véhicule.
        </div>
      )}
    </div>
  );
}

function formatPrice(value?: string | number | null) {
  if (value === null || value === undefined || value === '') {
    return 'Prix non défini';
  }

  return `Prix: ${value}`;
}
