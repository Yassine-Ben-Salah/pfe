import styles from './Footer.module.css';
import comarLogo from '../assets/comar.png';
import { useTranslation } from '../i18n';

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.content}>
          {/* Logo Section */}
          <div className={styles.section}>
            <div className={styles.logo}>
              <img className={styles.logoIcon} src={comarLogo} alt="COMAR Assurances" />
              <span className={styles.logoText}>{t('brand.name')}</span>
            </div>
            <p className={styles.tagline}>{t('footer.tagline')}</p>
          </div>

          {/* Links Sections */}
          <div className={styles.linksGrid}>
            <div className={styles.linkSection}>
              <h4>{t('footer.product')}</h4>
              <nav>
                <a href="#features">{t('footer.links.features')}</a>
                <a href="#how-it-works">{t('footer.links.howItWorks')}</a>
                <a href="#benefits">{t('footer.links.benefits')}</a>
                <a href="#pricing">{t('footer.links.pricing')}</a>
              </nav>
            </div>

            <div className={styles.linkSection}>
              <h4>{t('footer.company')}</h4>
              <nav>
                <a href="#about">{t('footer.links.about')}</a>
                <a href="#blog">{t('footer.links.blog')}</a>
                <a href="#careers">{t('footer.links.careers')}</a>
                <a href="#contact">{t('footer.links.contact')}</a>
              </nav>
            </div>

            <div className={styles.linkSection}>
              <h4>{t('footer.legal')}</h4>
              <nav>
                <a href="#privacy">{t('footer.links.privacy')}</a>
                <a href="#terms">{t('footer.links.terms')}</a>
                <a href="#security">{t('footer.links.security')}</a>
                <a href="#compliance">{t('footer.links.compliance')}</a>
              </nav>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className={styles.bottom}>
          <p className={styles.copyright}>{t('footer.copyright')}</p>
          
          <div className={styles.social}>
            <a href="#twitter" aria-label="Twitter" className={styles.socialLink}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M19 0h-1a1 1 0 00-1 1v1h-1V1a1 1 0 00-1-1h-1a1 1 0 00-1 1v1h-1V1a1 1 0 00-1-1h-1a1 1 0 00-1 1v1h-1V1a1 1 0 00-1-1H2a2 2 0 00-2 2v16a2 2 0 002 2h16a2 2 0 002-2V2a2 2 0 00-2-2zm-1 2v1a1 1 0 001 1h1v1h-1a1 1 0 00-1 1v1h1a1 1 0 001 1v1h-1a1 1 0 00-1-1h-1v-1h1a1 1 0 001-1v-1h-1a1 1 0 00-1-1v-1h1a1 1 0 001-1z"/>
              </svg>
            </a>
            <a href="#linkedin" aria-label="LinkedIn" className={styles.socialLink}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M0 2a2 2 0 012-2h16a2 2 0 012 2v16a2 2 0 01-2 2H2a2 2 0 01-2-2V2z"/>
              </svg>
            </a>
            <a href="#github" aria-label="GitHub" className={styles.socialLink}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 0a10 10 0 00-3.16 19.5c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.9.83.09-.64.35-1.08.64-1.33-2.22-.25-4.56-1.11-4.56-4.93 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0110 3.9c.85 0 1.7.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.82-2.34 4.68-4.57 4.93.36.3.68.92.68 1.85v2.75c0 .26.18.58.69.48A10 10 0 0010 0z"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
