import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AddAccountModal } from './AddAccountModal';
import { UserList } from './UserList';
import styles from './AdminDashboard.module.css';
import { useTranslation } from '../i18n';

export function AdminDashboard() {
  const navigate = useNavigate();
  const [showAddModal, setShowAddModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const { t } = useTranslation();

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h1>{t('admin.title')}</h1>
        <button className={styles.addButton} onClick={() => navigate('/admin/historique')}>
          {t('admin.viewHistory')}
        </button>
      </div>

      <UserList key={refreshKey} />

      {showAddModal && (
        <AddAccountModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </div>
  );
}