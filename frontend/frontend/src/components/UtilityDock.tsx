import styles from './UtilityDock.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleQuestion, faEnvelope, faFileLines, faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from '../i18n';

export function UtilityDock() {
  const { t } = useTranslation();
  const actions = [
    { key: 'utility.contact', icon: faEnvelope },
    { key: 'utility.quote', icon: faFileLines },
    { key: 'utility.search', icon: faMagnifyingGlass },
    { key: 'utility.help', icon: faCircleQuestion },
  ];

  return (
    <aside className={styles.dock} aria-label={t('utility.quickActions')}>
      {actions.map((action) => (
        <button key={action.key} className={styles.action} type="button" title={t(action.key)}>
          <FontAwesomeIcon className={styles.icon} icon={action.icon} aria-hidden="true" />
        </button>
      ))}
    </aside>
  );
}
