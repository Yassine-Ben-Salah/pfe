import { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEnvelope, faLock, faArrowRight, faShieldAlt } from '@fortawesome/free-solid-svg-icons';
import styles from './LoginPage.module.css';
import { getCurrentUser, loginUser } from '../api/client';
import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
import { faEyeSlash } from '@fortawesome/free-solid-svg-icons/faEyeSlash';
import { faEye } from '@fortawesome/free-solid-svg-icons/faEye';
import comarLogo from '../assets/logo.png';
import { useTranslation } from '../i18n';

interface LoginPageProps {
  onLoginSuccess?: () => void;
  onNavigateToLanding?: () => void;
  onClose?: () => void;
}

export function LoginPage({ onLoginSuccess, onNavigateToLanding , onClose}: LoginPageProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const { t } = useTranslation();

  const handleClose = () => {
    if (onClose) {
      onClose();
      return;
    }

    onNavigateToLanding?.();
  };




 
// ...inside the component, replace handleSubmit:
useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [onClose, onNavigateToLanding]);

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setError('');

  if (!email || !password) {
    setError(t('login.fillFields'));
    setLoading(false);
    return;
  }

  try {
    const data = await loginUser(email, password);

    localStorage.setItem('authToken', data.access_token);
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('userEmail', email);

    // fetch full user info (role, username, etc.) and store it
    const user = await getCurrentUser();
    localStorage.setItem('userRole', user.role);
    localStorage.setItem('username', user.username);

    if (onLoginSuccess) {
      onLoginSuccess();
    }
  } catch (err: any) {
    if (err.response?.status === 401) {
      setError(t('login.incorrect'));
    } else {
      setError(t('login.failed'));
    }
  } finally {
    setLoading(false);
  }
};
  
      

   return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-title"
      onClick={handleClose}
    >
      <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
        <button type="button" className={styles.closeButton} onClick={handleClose} aria-label="Close login">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6L6 18" />
            <path d="M6 6l12 12" />
          </svg>
        </button>

        <div className={styles.container}>
          {/* Left Side - Illustration (Desktop Only) */}
          <div className={styles.illustration}>
            <div className={styles.illustrationContent}>
              <div className={styles.brandRow}>
                <img className={styles.brandIcon} src={comarLogo} alt="COMAR Assurances" />
                <span className={styles.brandName}>COMAR Assurances</span>
              </div>

              <h2>{t('login.welcome')}</h2>
              <p>{t('login.subtitle')}</p>

              <svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg" className={styles.illustrationSvg}>
                <defs>
                  <linearGradient id="gradLogin" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style={{ stopColor: '#2563EB', stopOpacity: 0.15 }} />
                    <stop offset="100%" style={{ stopColor: '#10B981', stopOpacity: 0.15 }} />
                  </linearGradient>
                </defs>

                {/* Background Circle */}
                <circle cx="150" cy="150" r="130" fill="url(#gradLogin)" />

                {/* Car Body */}
                <rect x="60" y="120" width="180" height="80" rx="15" fill="#E5E7EB" stroke="#D1D5DB" strokeWidth="2" />
                
                {/* Car Head */}
                <rect x="75" y="90" width="150" height="35" rx="12" fill="#F3F4F6" stroke="#D1D5DB" strokeWidth="2" />
                
                {/* Windows */}
                <rect x="90" y="102" width="40" height="20" rx="6" fill="#DBEAFE" opacity="0.6" stroke="#3B82F6" strokeWidth="1" />
                <rect x="170" y="102" width="40" height="20" rx="6" fill="#DBEAFE" opacity="0.6" stroke="#3B82F6" strokeWidth="1" />
                
                {/* Wheels */}
                <circle cx="100" cy="210" r="18" fill="#374151" stroke="#1F2937" strokeWidth="2" />
                <circle cx="200" cy="210" r="18" fill="#374151" stroke="#1F2937" strokeWidth="2" />
                
                {/* AI Detection Lines */}
                <line x1="110" y1="110" x2="190" y2="110" stroke="#2563EB" strokeWidth="1.5" opacity="0.4" strokeDasharray="3,3" />
                <line x1="100" y1="130" x2="200" y2="130" stroke="#10B981" strokeWidth="1.5" opacity="0.4" strokeDasharray="3,3" />
                <line x1="110" y1="150" x2="190" y2="150" stroke="#2563EB" strokeWidth="1.5" opacity="0.4" strokeDasharray="3,3" />
                
                {/* Checkmark */}
                <circle cx="250" cy="80" r="20" fill="#10B981" opacity="0.8" />
                <path d="M244 78 L248 82 L256 74" stroke="var(--white)" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>

              <ul className={styles.featureList}>
                <li>
                  <span className={styles.featureCheck}><FontAwesomeIcon icon={faCheck} /></span>
                  {t('login.feature1')}
                </li>
                <li>
                  <span className={styles.featureCheck}><FontAwesomeIcon icon={faCheck} /></span>
                  {t('login.feature2')}
                </li>
                <li>
                  <span className={styles.featureCheck}><FontAwesomeIcon icon={faCheck} /></span>
                  {t('login.feature3')}
                </li>
              </ul>
            </div>
          </div>

          {/* Right Side - Login Form */}
          <div className={styles.formContainer}>
            <div className={styles.formCard}>
              {/* Logo */}
              <div className={styles.logo}>
                <img className={styles.logoIcon} src={comarLogo} alt="COMAR Assurances" />
                <span className={styles.logoText}>COMAR Assurances</span>
              </div>

              {/* Welcome Text */}
              <div className={styles.welcome}>
                <h1 id="login-title">{t('login.welcome')}</h1>
                <p>{t('login.subtitle')}</p>
              </div>

              {/* Error Message */}
              {error && (
                <div className={styles.errorMessage}>
                  <FontAwesomeIcon icon={faShieldAlt} />
                  <span>{error}</span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className={styles.form}>
                {/* Email Field */}
                <div className={styles.formGroup}>
                  <label htmlFor="email" className={styles.label}>{t('login.label.email')}</label>
                  <div className={styles.inputWrapper}>
                    <span className={styles.inputIcon}>
                      <FontAwesomeIcon icon={faEnvelope} />
                    </span>
                    <input
                      id="email"
                      type="email"
                      placeholder={t('login.placeholder.email')}
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className={styles.input}
                      disabled={loading}
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className={styles.formGroup}>
                  <label htmlFor="password" className={styles.label}>{t('login.label.password')}</label>
                  <div className={`${styles.inputWrapper} ${styles.inputWrapperPassword}`}>
                    <span className={styles.inputIcon}>
                      <FontAwesomeIcon icon={faLock} />
                    </span>
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder={t('login.placeholder.password')}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={styles.input}
                      disabled={loading}
                    />
                    <button
                      type="button"
                      className={styles.passwordToggle}
                      onClick={() => setShowPassword((value) => !value)}
                      aria-label={showPassword ? t('login.hidePassword') : t('login.showPassword')}
                      tabIndex={-1}
                    >
                      <FontAwesomeIcon icon={showPassword ? faEyeSlash : faEye} />
                    </button>
                  </div>
                </div>

                {/* Remember Me & Forgot Password */}
                <div className={styles.formFooter}>
                  <label className={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      disabled={loading}
                    />
                    <span>{t('login.remember')}</span>
                  </label>
                  <a href="#forgot-password" className={styles.forgotPassword}>
                    {t('login.forgot')}
                  </a>
                </div>

                {/* Submit Button */}
                <button 
                  type="submit" 
                  className={styles.submitButton}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className={styles.spinner}></span>
                      {t('login.signing')}
                    </>
                  ) : (
                    <>
                      {t('login.signin')}
                      <FontAwesomeIcon icon={faArrowRight} />
                    </>
                  )}
                </button>
              </form>

              {/* Back to Landing */}
              <div className={styles.bottomLink}>
                <span>{t('login.backHelp')} </span>
                <button 
                  type="button"
                  className={styles.landingLink}
                  onClick={onNavigateToLanding}
                >
                  {t('login.backToLanding')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
