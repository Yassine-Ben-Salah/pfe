import { useState, useEffect } from 'react';
import { listUsers, updateUser, deleteUser, type UserData } from '../api/client';
import styles from './UserList.module.css';
import { useTranslation } from '../i18n';

export function UserList() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const currentUserEmail = localStorage.getItem('userEmail');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await listUsers();
      setUsers(data);
    } catch {
      setError(t('user.failedLoad'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleActive = async (user: UserData) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      fetchUsers();
    } catch {
      setError(t('user.failedUpdate'));
    }
  };

  const handleRoleChange = async (user: UserData, newRole: string) => {
    try {
      await updateUser(user.id, { role: newRole });
      fetchUsers();
    } catch {
      setError(t('user.failedUpdateRole'));
    }
  };
  const handleResetPassword = async (user: UserData) => {
  const newPassword = prompt(t('user.resetPrompt').replace('{{email}}', user.email));
  if (!newPassword) return;
  if (newPassword.length < 6) {
    setError(t('user.passwordTooShort'));
    return;
  }
  try {
    await updateUser(user.id, { password: newPassword });
    alert(t('user.passwordUpdated'));
  } catch {
    setError(t('user.failedUpdate'));
  }
};

  const handleDelete = async (user: UserData) => {
    if (!confirm(t('user.confirmDelete').replace('{{email}}', user.email))) return;
    try {
      await deleteUser(user.id);
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('user.failedDelete'));
    }
  };

  if (loading) return <p>{t('user.loading')}</p>;

  return (
    <div className={styles.container}>
      {error && <div className={styles.error}>{error}</div>}

      <table className={styles.table}>
        <thead>
          <tr>
            <th>{t('table.header.email')}</th>
            <th>{t('table.header.username')}</th>
            <th>{t('table.header.telephone')}</th>
            <th>{t('table.header.role')}</th>
            <th>{t('table.header.status')}</th>
            <th>{t('table.header.actions')}</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.username}</td>
              <td>{user.telephone}</td>
              <td>
                <select
                  value={user.role}
                  onChange={(e) => handleRoleChange(user, e.target.value)}
                  disabled={user.email === currentUserEmail}
                >
                  <option value="user">{t('role.user')}</option>
                  <option value="admin">{t('role.admin')}</option>
                </select>
              </td>
              <td>
                <button
                  className={user.is_active ? styles.statusActive : styles.statusInactive}
                  onClick={() => handleToggleActive(user)}
                  disabled={user.email === currentUserEmail}
                >
                  {user.is_active ? t('status.active') : t('status.inactive')}
                </button>
              </td>
              <td>
                    <button className={styles.resetButton} onClick={() => handleResetPassword(user)}>
                        {t('user.resetPassword')}
                    </button>
                    <button
                        className={styles.deleteButton}
                        onClick={() => handleDelete(user)}
                        disabled={user.email === currentUserEmail}
                    >
                        {t('user.delete')}
                    </button>
                </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}