import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMoon, faSun } from '@fortawesome/free-solid-svg-icons';
import styles from './NavBar.module.css';
import comarLogo from '../assets/comar.png';
import { useTranslation } from '../i18n';

export function NavBar() {
  const navigate = useNavigate();
  const role = localStorage.getItem('userRole');
  const username = localStorage.getItem('username');
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme ? savedTheme === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const { t, locale, setLocale } = useTranslation();

  useEffect(() => {
    document.documentElement.dataset.theme = isDarkMode ? 'dark' : 'light';
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  return (
    <nav className={styles.nav}>
      <div className={styles.left}>
        <div className={styles.logoWrap}>
          <img className={styles.logoMark} src={comarLogo} alt="COMAR Assurances" />
          <div className={styles.brand}>
            <span className={styles.brandName}>{t('brand.name')}</span>
            <span className={styles.brandSubtitle}>{t('brand.subtitle')}</span>
          </div>
        </div>
        <button onClick={() => navigate('/dashboard')} className={styles.link}>
          {t('nav.dashboard')}
        </button>
        <button onClick={() => navigate('/historique')} className={styles.link}>
          {t('nav.history')}
        </button>
        <button onClick={() => navigate('/parts-catalog')} className={styles.link}>
          Catalogue pièces
        </button>
        <button onClick={() => navigate('/login')} className={`${styles.link} ${styles.portalLink}`}>
          {t('nav.portal')}
        </button>
        {role === 'admin' && (
          <>
            <button onClick={() => navigate('/admin')} className={styles.link}>
              {t('nav.adminPanel')}
            </button>
            <button onClick={() => navigate('/admin/create-account')} className={styles.link}>
              {t('nav.createAccount')}
            </button>
          </>
        )}
      </div>
      <div className={styles.right}>
        <button
          type="button"
          className={styles.themeToggle}
          onClick={() => setIsDarkMode((current) => !current)}
          aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-pressed={isDarkMode}
          title={isDarkMode ? 'Light mode' : 'Dark mode'}
        >
          <FontAwesomeIcon icon={isDarkMode ? faSun : faMoon} aria-hidden="true" />
        </button>
        <div className={styles.langSwitch} aria-label="Select language">
          <button
            type="button"
            className={`${styles.langOption} ${locale === 'fr' ? styles.langOptionActive : ''}`}
            onClick={() => setLocale('fr')}
            aria-pressed={locale === 'fr'}
          >
            FR
          </button>
          <button
            type="button"
            className={`${styles.langOption} ${locale === 'en' ? styles.langOptionActive : ''}`}
            onClick={() => setLocale('en')}
            aria-pressed={locale === 'en'}
          >
            EN
          </button>
        </div>
        {isAuthenticated && (
          <>
            <span className={styles.username}>{username}</span>
            <button onClick={handleLogout} className={styles.logout}>
              {t('nav.logout')}
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
