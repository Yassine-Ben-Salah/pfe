import styles from './CTASection.module.css';
import { useTranslation } from '../i18n';

interface CTASectionProps {
  onLoginClick?: () => void;
}

export function CTASection({ onLoginClick }: CTASectionProps) {
  const { t } = useTranslation();
  return (
    <section className={styles.cta}>
      <div className={styles.container}>
        <div className={styles.content}>
          <h2>{t('cta.title')}</h2>
          <p>{t('cta.subtitle')}</p>
          
          <button 
            className={styles.button}
            onClick={onLoginClick}
          >
            {t('cta.login')}
            <span className={styles.arrow}>→</span>
          </button>
        </div>

        {/* Decorative Elements */}
        <div className={styles.decorative}>
          <div className={styles.circle1}></div>
          <div className={styles.circle2}></div>
        </div>
      </div>
    </section>
  );
}
