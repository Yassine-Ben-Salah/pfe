import type { RapportResult } from '../types/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileLines } from '@fortawesome/free-solid-svg-icons';
import styles from './RapportCard.module.css';
import { useTranslation } from '../i18n';

interface Props {
  result: RapportResult;
  rank: number;
}

function scoreClass(score: number): string {
  if (score >= 0.7) return styles.scoreHigh;
  if (score >= 0.4) return styles.scoreMid;
  return styles.scoreLow;
}

export function RapportCard({ result: r, rank }: Props) {
  const { t } = useTranslation();
  const score = r.score ?? 0;
  const hasTotals = r.total_ht || r.tva || r.total_net || r.total_ttc;

  return (
    <article className={styles.card} style={{ animationDelay: `${rank * 0.05}s` }}>

      {/* Header */}
      <div className={styles.cardTop}>
        <div>
          <span className={styles.rank}>#{rank}</span>
          <span className={styles.filename}><FontAwesomeIcon icon={faFileLines} aria-hidden="true" /> {r.filename ?? '—'}</span>
        </div>
        <span className={`${styles.scoreBadge} ${scoreClass(score)}`}>
          {score.toFixed(3)}
        </span>
      </div>

      {/* Meta grid */}
      <div className={styles.metaGrid}>
        {[
          { label: t('card.label.brand'), value: `${r.marque ?? '—'} ${r.type ?? ''}`.trim() },
          { label: t('card.label.plate'), value: r.immatriculation ?? '—' },
          { label: t('card.label.accidentDate'), value: r.date_accident ?? '—' },
          { label: t('card.label.insured'), value: r.assure ?? '—' },
          { label: t('card.label.file'), value: r.numero_dossier ?? '—' },
        ].map(({ label, value }) => (
          <div key={label} className={styles.metaItem}>
            <div className={styles.metaLabel}>{label}</div>
            <div className={styles.metaValue} title={value}>{value}</div>
          </div>
        ))}
      </div>

      {/* Damage text */}
      {r.damage_text && (
        <p className={styles.damageText}>{r.damage_text}</p>
      )}

      {/* Price table */}
      {r.price_items && r.price_items.length > 0 && (
        <div className={styles.priceSection}>
          <table className={styles.priceTable}>
            <thead>
              <tr>
                <th>{t('price.header.designation')}</th>
                <th>{t('price.header.unit')}</th>
                <th>{t('price.header.amount')}</th>
              </tr>
            </thead>
            <tbody>
              {r.price_items.map((item, i) => (
                <tr key={i}>
                  <td>{item.designation ?? '—'}</td>
                  <td>{item.prix_unitaire ?? '—'}</td>
                  <td>{item.montant ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Totals */}
      {hasTotals && (
        <div className={styles.totalsRow}>
          {r.total_ht  && <Chip label={t('totals.total_ht')}  value={`${r.total_ht} DT`} />}
          {r.tva       && <Chip label={t('totals.tva')}        value={`${r.tva} DT`} />}
          {r.total_net && <Chip label={t('totals.net')}        value={`${r.total_net} DT`} />}
          {r.total_ttc && <Chip label={t('totals.ttc')}        value={`${r.total_ttc} DT`} />}
        </div>
      )}

    </article>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.chip}>
      <span className={styles.chipLabel}>{label}</span>
      <span className={styles.chipValue}>{value}</span>
    </div>
  );
}
