import styles from './FeaturesSection.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalculator, faCamera, faFileLines } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from '../i18n';

export function FeaturesSection() {
  const { t } = useTranslation();
  const features = [
    {
      id: 1,
      title: t('features.step1.title'),
      description: t('features.step1.desc'),
      icon: faFileLines,
      color: 'primary',
    },
    {
      id: 2,
      title: t('features.step2.title'),
      description: t('features.step2.desc'),
      icon: faCamera,
      color: 'accent',
    },
    {
      id: 3,
      title: t('features.step3.title'),
      description: t('features.step3.desc'),
      icon: faCalculator,
      color: 'primary',
    },
  ];

  return (
    <section className={styles.features}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h2>{t('features.title')}</h2>
          <p>{t('features.subtitle')}</p>
        </div>

        <div className={styles.grid}>
          {features.map((feature, index) => (
            <div key={feature.id} className={styles.card}>
              <div className={`${styles.iconContainer} ${styles[feature.color]}`}>
                <FontAwesomeIcon className={styles.icon} icon={feature.icon} aria-hidden="true" />
                {index < features.length - 1 && <div className={styles.connector}></div>}
              </div>
              
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
