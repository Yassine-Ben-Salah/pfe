import { useState } from 'react';
import { useTranslation } from '../i18n';
import { registerUser } from '../api/client';
import styles from './AddAccountModal.module.css';

interface Props {
  onClose: () => void;
  onCreated?: () => void;
}

export function AddAccountModal({ onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [telephone, setTelephone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await registerUser({ email, username, telephone, password, role });
      if (onCreated) onCreated();
      onClose();
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError(t('addAccount.onlyAdmins'));
      } else if (err.response?.status === 400) {
        setError(err.response.data.detail || t('addAccount.exists'));
      } else {
        setError(t('addAccount.failed'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2>{t('addAccount.title')}</h2>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <label>{t('addAccount.email')}</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label>{t('addAccount.username')}</label>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />

          <label>{t('addAccount.telephone')}</label>
          <input type="text" value={telephone} onChange={(e) => setTelephone(e.target.value)} required />

          <label>{t('addAccount.password')}</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          <label>{t('addAccount.role')}</label>
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="user">{t('role.user')}</option>
            <option value="admin">{t('role.admin')}</option>
          </select>

          <div className={styles.actions}>
            <button type="button" onClick={onClose} disabled={loading}>{t('addAccount.cancel')}</button>
            <button type="submit" disabled={loading}>
              {loading ? t('addAccount.creating') : t('addAccount.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}