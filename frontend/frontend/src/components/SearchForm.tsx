import { useState, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import type { SearchRequest } from '../types/api';
import styles from './SearchForm.module.css';

interface Props {
  onSearch: (req: SearchRequest) => void;
  loading: boolean;
  prefillMarque?: string;
  prefillDamage?: string;
  prefillType?: string;   
  prefillAssurance?: string;  
}

export function SearchForm({ onSearch, loading, prefillMarque = '', prefillType = '', prefillDamage = '', prefillAssurance = '' }: Props) {
  const [marque, setMarque] = useState('');
  const [type, setType] = useState('');       
  const [damageQuery, setDamageQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [scoreThreshold, setScoreThreshold] = useState('');
  const [rerank, setRerank] = useState(false);
  const [semWeight, setSemWeight] = useState(0.6);
  const [bm25Weight, setBm25Weight] = useState(0.4);
  const [assurance, setAssurance] = useState('');

  // When prefill values arrive from constat extraction, update the fields
  useEffect(() => {
    setMarque(prefillMarque);
  }, [prefillMarque]);

  useEffect(() => {
    setAssurance(prefillAssurance);
  }, [prefillAssurance]);

  useEffect(() => {
    setType(prefillType);
  }, [prefillType]);

  useEffect(() => {
    setDamageQuery(prefillDamage);
  }, [prefillDamage]);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!marque.trim() && !damageQuery.trim()) return;
    onSearch({
      marque: marque.trim() || null,
      type: type.trim() || null, 
      assurance: assurance.trim() || null,
      damage_query: damageQuery.trim() || null,
      top_k: topK,
      semantic_weight: semWeight,
      bm25_weight: bm25Weight,
      rerank,
      score_threshold: scoreThreshold !== '' ? parseFloat(scoreThreshold) : null,
    });
  };

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit();
  };

  const canSearch = marque.trim() || type.trim() || damageQuery.trim();
  return (
    <form className={styles.form} onSubmit={handleSubmit}>

      <section className={styles.panel}>
        <p className={styles.sectionTitle}>Recherche</p>

        <label className={styles.label}>Marque du véhicule</label>
        <input
          className={styles.input}
          type="text"
          placeholder="ex: Peugeot, Renault…"
          value={marque}
          onChange={e => setMarque(e.target.value)}
          onKeyDown={handleKey}
        />
        <label className={styles.label}>Type / Modèle</label>
            <input
              className={styles.input}
              type="text"
              placeholder="ex: Passat, 308, Clio…"
              value={type}
              onChange={e => setType(e.target.value)}
              onKeyDown={handleKey}
            />

        <label className={styles.label}>Société d'assurance</label>
              <input
                    className={styles.input}
                    type="text"
                    placeholder="ex: Comar, GAT, STAR…"
                    value={assurance}
                    onChange={e => setAssurance(e.target.value)}
                    onKeyDown={handleKey}
                  />

        <label className={styles.label}>Description des dégâts</label>
        <textarea
          className={styles.textarea}
          placeholder="ex: pare choc avant gauche, aile arrière droite…"
          value={damageQuery}
          onChange={e => setDamageQuery(e.target.value)}
          rows={4}
        />

        <div className={styles.row2}>
          <div>
            <label className={styles.label}>Résultats (top_k)</label>
            <input
              className={styles.input}
              type="number"
              min={1}
              max={50}
              value={topK}
              onChange={e => setTopK(parseInt(e.target.value) || 5)}
            />
          </div>
          <div>
            <label className={styles.label}>Score min.</label>
            <input
              className={styles.input}
              type="number"
              step={0.01}
              min={0}
              max={1}
              placeholder="aucun"
              value={scoreThreshold}
              onChange={e => setScoreThreshold(e.target.value)}
            />
          </div>
        </div>
      </section>

      <section className={styles.panel}>
        <p className={styles.sectionTitle}>Paramètres avancés</p>

        <div className={styles.toggleRow}>
          <span className={styles.toggleLabel}>Re-ranking cross-encoder</span>
          <button
            type="button"
            role="switch"
            aria-checked={rerank}
            className={`${styles.toggle} ${rerank ? styles.toggleOn : ''}`}
            onClick={() => setRerank(v => !v)}
          />
        </div>

        <label className={styles.label}>
          Poids sémantique
          <span className={styles.weightVal}>{semWeight.toFixed(2)}</span>
        </label>
        <input
          className={styles.range}
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={semWeight}
          onChange={e => setSemWeight(parseFloat(e.target.value))}
        />

        <label className={styles.label} style={{ marginTop: '0.75rem' }}>
          Poids BM25
          <span className={styles.weightVal}>{bm25Weight.toFixed(2)}</span>
        </label>
        <input
          className={styles.range}
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={bm25Weight}
          onChange={e => setBm25Weight(parseFloat(e.target.value))}
        />
      </section>

      <button
        className={styles.btnSearch}
        type="submit"
        disabled={loading || !canSearch}
      >
        {loading ? 'Recherche…' : 'Lancer la recherche'}
      </button>

    </form>
  );
}