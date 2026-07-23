import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../api/client';
import styles from './CreateAccountPage.module.css';
import { useTranslation } from '../i18n';

export function CreateAccountPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [telephone, setTelephone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await registerUser({ email, username, telephone, password, role });
      setSuccess(t('create.success'));
      setEmail('');
      setUsername('');
      setTelephone('');
      setPassword('');
      setRole('user');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('create.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1>{t('create.title')}</h1>
          <p>{t('create.description')}</p>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {success && <div className={styles.success}>{success}</div>}

        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>{t('create.email')}</label>
          <input className={styles.input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label className={styles.label}>{t('create.username')}</label>
          <input className={styles.input} type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />

          <label className={styles.label}>{t('create.telephone')}</label>
          <input className={styles.input} type="text" value={telephone} onChange={(e) => setTelephone(e.target.value)} required />

          <label className={styles.label}>{t('create.password')}</label>
          <input className={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          <label className={styles.label}>{t('create.role')}</label>
          <select className={styles.select} value={role} onChange={(e) => setRole(e.target.value)}>
                    <option value="user">{t('role.user')}</option>
                    <option value="admin">{t('role.admin')}</option>
          </select>

          <div className={styles.actions}>
          <div className={styles.actions}>
            <button type="button" className={styles.secondary} onClick={() => navigate('/admin')}>{t('create.back')}</button>
            <button type="submit" className={styles.primary} disabled={loading}>{loading ? t('create.creating') : t('create.submit')}</button>
          </div>
          </div>
        </form>
      </div>
    </div>
  );
}
