import type { HealthStatus } from '../hooks/useHealthCheck';
import styles from './StatusPill.module.css';
import { useTranslation } from '../i18n';

interface Props {
  status: HealthStatus;
}

export function StatusPill({ status }: Props) {
  const { t } = useTranslation();
  const labels: Record<HealthStatus, string> = {
    checking: t('status.checking'),
    online: t('status.online'),
    offline: t('status.offline'),
  };

  return (
    <span className={`${styles.pill} ${styles[status]}`}>
      <span className={styles.dot} />
      {labels[status]}
    </span>
  );
}
