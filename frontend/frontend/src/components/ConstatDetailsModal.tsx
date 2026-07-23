import styles from './ConstatDetailsModal.module.css';
import { useTranslation } from '../i18n';

interface ConstatDetailsModalProps {
  item: {
    date_accident?: string;
    vehicule_a_marque?: string;
    vehicule_a_type?: string;
    vehicule_b_marque?: string;
    vehicule_b_type?: string;
    assurance_a?: string;
    assurance_b?: string;
    observations?: string;
    full_text?: string;
  } | null;
  onClose: () => void;
}

export function ConstatDetailsModal({ item, onClose }: ConstatDetailsModalProps) {
  const { t } = useTranslation();
  if (!item) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
        <div className={styles.header}>
          <h2>{t('admin.history.detailsTitle')}</h2>
          <button className={styles.closeButton} onClick={onClose}>×</button>
        </div>

        <div className={styles.body}>
          <p><strong>{t('admin.history.label.date')}</strong> {item.date_accident ?? '—'}</p>
          <p><strong>{t('admin.history.label.vehicleA')}</strong> {item.vehicule_a_marque ?? '—'} {item.vehicule_a_type ?? ''}</p>
          <p><strong>{t('admin.history.label.vehicleB')}</strong> {item.vehicule_b_marque ?? '—'} {item.vehicule_b_type ?? ''}</p>
          <p><strong>{t('admin.history.label.insurerA')}</strong> {item.assurance_a ?? '—'}</p>
          <p><strong>{t('admin.history.label.insurerB')}</strong> {item.assurance_b ?? '—'}</p>
          <p><strong>{t('admin.history.label.observations')}</strong> {item.observations ?? '—'}</p>
          {item.full_text && <pre className={styles.textBox}>{item.full_text}</pre>}
        </div>
      </div>
    </div>
  );
}
