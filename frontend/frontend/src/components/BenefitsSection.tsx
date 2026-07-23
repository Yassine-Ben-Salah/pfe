import styles from './BenefitsSection.module.css';
import { useTranslation } from '../i18n';

export function BenefitsSection() {
  const { t } = useTranslation();
  const benefits = [
    t('benefits.item1'),
    t('benefits.item2'),
    t('benefits.item3'),
    t('benefits.item4'),
    t('benefits.item5'),
    t('benefits.item6'),
  ];

  return (
    <section className={styles.benefits}>
      <div className={styles.container}>
        <div className={styles.grid}>
          {/* Left - Illustration */}
          <div className={styles.illustration}>
            <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" className={styles.illustrationSvg}>
              <defs>
                <linearGradient id="gradBenefits" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#2563EB', stopOpacity: 0.1 }} />
                  <stop offset="100%" style={{ stopColor: '#10B981', stopOpacity: 0.1 }} />
                </linearGradient>
              </defs>

              {/* Background Circles */}
              <circle cx="200" cy="200" r="180" fill="url(#gradBenefits)" />
              <circle cx="200" cy="200" r="160" fill="none" stroke="#2563EB" strokeWidth="1" opacity="0.2" />
              <circle cx="200" cy="200" r="140" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.2" />

              {/* Central Document */}
              <g className={styles.pulse}>
                <rect x="120" y="100" width="160" height="200" rx="12" fill="var(--white)" stroke="#2563EB" strokeWidth="2" filter="drop-shadow(0 10px 20px rgba(37, 99, 235, 0.2))" />
                
                {/* Document Lines */}
                <line x1="140" y1="130" x2="260" y2="130" stroke="#E5E7EB" strokeWidth="2" />
                <line x1="140" y1="150" x2="260" y2="150" stroke="#E5E7EB" strokeWidth="2" />
                <line x1="140" y1="170" x2="260" y2="170" stroke="#E5E7EB" strokeWidth="2" />
                
                {/* AI Badge */}
                <circle cx="200" cy="220" r="25" fill="#10B981" />
                <text x="200" y="225" textAnchor="middle" fontSize="16" fontWeight="700" fill="var(--white)">AI</text>
              </g>

              {/* Checkmarks around */}
              <g className={styles.float} style={{ animationDelay: '0s' }}>
                <circle cx="80" cy="80" r="30" fill="var(--white)" stroke="#10B981" strokeWidth="2" filter="drop-shadow(0 4px 8px rgba(0,0,0,0.1))" />
                <text x="80" y="95" textAnchor="middle" fontSize="20" fill="#10B981">✓</text>
              </g>

              <g className={styles.float} style={{ animationDelay: '0.2s' }}>
                <circle cx="320" cy="80" r="30" fill="var(--white)" stroke="#10B981" strokeWidth="2" filter="drop-shadow(0 4px 8px rgba(0,0,0,0.1))" />
                <text x="320" y="95" textAnchor="middle" fontSize="20" fill="#10B981">✓</text>
              </g>

              <g className={styles.float} style={{ animationDelay: '0.4s' }}>
                <circle cx="320" cy="320" r="30" fill="var(--white)" stroke="#2563EB" strokeWidth="2" filter="drop-shadow(0 4px 8px rgba(0,0,0,0.1))" />
                <text x="320" y="335" textAnchor="middle" fontSize="20" fill="#2563EB">✓</text>
              </g>
            </svg>
          </div>

          {/* Right - Benefits List */}
          <div className={styles.content}>
            <div className={styles.header}>
              <h2>{t('benefits.title')}</h2>
              <p>{t('benefits.subtitle')}</p>
            </div>

            <div className={styles.checklistContainer}>
              {benefits.map((benefit, index) => (
                <div key={index} className={styles.checklistItem}>
                  <div className={styles.checkbox}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fill="currentColor"/>
                    </svg>
                  </div>
                  <span>{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
