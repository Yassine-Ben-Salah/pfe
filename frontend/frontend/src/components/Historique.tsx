import { useEffect, useState } from 'react';
import { listConstats, listUsers } from '../api/client';
import styles from './Historique.module.css';
import { useTranslation } from '../i18n';

interface ConstatItem {
  id?: number;
  user_id?: number;
  user?: {
    username?: string;
    email?: string;
  } | null;
  file_id?: string;
  date_accident?: string;
  heure?: string;
  lieu?: string;
  blesses?: string;
  vehicule_a_marque?: string;
  vehicule_a_type?: string;
  vehicule_a_immatriculation?: string;
  assurance_a?: string;
  degats_vehicule_a?: string;
  vehicule_b_marque?: string;
  vehicule_b_type?: string;
  vehicule_b_immatriculation?: string;
  assurance_b?: string;
  degats_vehicule_b?: string;
  observations?: string;
  full_text?: string;
  analysis_report?: any;
  analysisReport?: any;
  report?: any;
}

interface UserOption {
  id: number;
  username: string;
  role?: string;
}

export function Historique() {
  const { t } = useTranslation();
  const [constats, setConstats] = useState<ConstatItem[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<ConstatItem | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<number | 'all'>('all');
  const [reportData, setReportData] = useState<any>(null);
  const isAdmin = typeof window !== 'undefined' && localStorage.getItem('userRole') === 'admin';

  const filteredConstats = selectedUserId === 'all'
    ? constats
    : constats.filter((item) => item.user_id === selectedUserId);

  const selectedReport = selected
    ? (
        selected.analysis_report ??
        (selected as any).analysisReport ??
        (selected as any).report ??
        reportData ??
        null
      )
    : null;

  useEffect(() => {
    if (!selected) {
      setReportData(null);
      return;
    }

    if (selected.analysis_report || (selected as any).analysisReport || (selected as any).report) {
      setReportData(selected.analysis_report ?? (selected as any).analysisReport ?? (selected as any).report ?? null);
      return;
    }

    setReportData(null);
  }, [selected]);

  useEffect(() => {
    const load = async () => {
      try {
        const [constatData, userData] = await Promise.all([
          listConstats(),
          isAdmin ? listUsers() : Promise.resolve([]),
        ]);

        setConstats(constatData);
        if (isAdmin) {
          setUsers(userData.filter((user) => user.role !== 'admin'));
        }
      } catch {
        setError(t('history.loading'));
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [isAdmin]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{t('history.title')}</h1>
          <p className={styles.subtitle}>
            {isAdmin ? t('history.subtitle.admin') : t('history.subtitle.user')}
          </p>
        </div>
      </div>

      {isAdmin && (
        <div className={styles.controls}>
          <label className={styles.selectLabel} htmlFor="user-history-select">
            {t('history.chooseUser')}
          </label>
          <select
            id="user-history-select"
            className={styles.select}
            value={selectedUserId}
            onChange={(event) => setSelectedUserId(event.target.value === 'all' ? 'all' : Number(event.target.value))}
          >
            <option value="all">{t('history.allUsers')}</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.username}</option>
            ))}
          </select>
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.emptyState}>{t('history.loading')}</div>
      ) : filteredConstats.length === 0 ? (
        <div className={styles.emptyState}>
          {isAdmin && selectedUserId !== 'all'
            ? t('history.noConstatsForUser')
            : t('history.noConstats')}
        </div>
      ) : (
        <div className={styles.list}>
          {filteredConstats.map((item, index) => (
            <button key={item.file_id ?? index} className={styles.cardButton} onClick={() => setSelected(item)}>
              <div className={styles.cardTop}>
                <div>
                  <div className={styles.cardTitle}>{t('history.constatTitle').replace('{{index}}', String(index + 1))}</div>
                  <div className={styles.cardMeta}>
                    {item.date_accident ?? t('history.dateNotAvailable')}
                    {isAdmin && (item.user?.username || item.user_id) ? ` • ${item.user?.username ?? `User #${item.user_id}`}` : ''}
                  </div>
                </div>
                <span className={styles.badge}>Open details</span>
              </div>
              <div className={styles.cardBody}>
                <span>{item.vehicule_a_marque ?? t('history.vehicle')} {item.vehicule_a_type ?? ''}</span>
                <span>{item.assurance_a ?? t('history.insurerNotAvailable')}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className={styles.modalOverlay} onClick={() => setSelected(null)}>
          <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>{t('history.detailsTitle')}</h2>
              <button className={styles.closeButton} onClick={() => setSelected(null)}>×</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.outputSection}>
                <h3 className={styles.outputTitle}>Uploaded output</h3>
                <div className={styles.outputGrid}>
                  <p><strong>Date:</strong> {selected.date_accident ?? '—'}</p>
                  <p><strong>Hour:</strong> {selected.heure ?? '—'}</p>
                  <p><strong>Location:</strong> {selected.lieu ?? '—'}</p>
                  <p><strong>Injured:</strong> {selected.blesses ?? '—'}</p>
                  <p><strong>Vehicle A:</strong> {selected.vehicule_a_marque ?? '—'} {selected.vehicule_a_type ?? ''}</p>
                  <p><strong>Plate A:</strong> {selected.vehicule_a_immatriculation ?? '—'}</p>
                  <p><strong>Damage A:</strong> {selected.degats_vehicule_a ?? '—'}</p>
                  <p><strong>Insurer A:</strong> {selected.assurance_a ?? '—'}</p>
                  <p><strong>Vehicle B:</strong> {selected.vehicule_b_marque ?? '—'} {selected.vehicule_b_type ?? ''}</p>
                  <p><strong>Plate B:</strong> {selected.vehicule_b_immatriculation ?? '—'}</p>
                  <p><strong>Damage B:</strong> {selected.degats_vehicule_b ?? '—'}</p>
                  <p><strong>Insurer B:</strong> {selected.assurance_b ?? '—'}</p>
                  <p><strong>Observations:</strong> {selected.observations ?? '—'}</p>
                </div>
              </div>
              {selectedReport && (
                <>
                  <h4 className={styles.outputSubtitle}>Generated report</h4>
                  <div className={styles.reportBox}>
                    <div className={styles.reportBadges}>
                      <span className={styles.reportBadge}>Severity: <strong>{selectedReport.severity ?? '—'}</strong></span>
                      {selectedReport.cost_median != null && (
                        <span className={styles.reportBadge}>~{selectedReport.cost_median} DT</span>
                      )}
                      {selectedReport.cost_min != null && selectedReport.cost_max != null && (
                        <span className={styles.reportBadge}>{selectedReport.cost_min} – {selectedReport.cost_max} DT</span>
                      )}
                    </div>
                    {selectedReport.matched_keywords?.length > 0 && (
                      <p><strong>Keywords:</strong> {selectedReport.matched_keywords.join(', ')}</p>
                    )}
                    {selectedReport.keywords?.length > 0 && (
                      <p><strong>Key terms:</strong> {selectedReport.keywords.join(', ')}</p>
                    )}
                    {selectedReport.similar_cases?.length > 0 && (
                      <div>
                        <strong>Similar cases:</strong>
                        <ul className={styles.reportList}>
                          {selectedReport.similar_cases.map((item: any, index: number) => (
                            <li key={`${item.marque ?? 'case'}-${index}`}>
                              {item.marque ?? 'Case'} — {item.damage ? String(item.damage).slice(0, 80) : '—'}
                              {item.total_ttc ? ` (${item.total_ttc} DT)` : ''}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </>
              )}
              {selected.full_text && (
                <>
                  <h4 className={styles.outputSubtitle}>Original text</h4>
                  <pre className={styles.textBox}>{selected.full_text}</pre>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
