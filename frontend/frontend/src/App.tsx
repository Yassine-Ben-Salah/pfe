import { BrowserRouter as Router, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { AdminDashboard } from './components/AdminDashboard';
import { AdminHistorique } from './components/AdminHistorique';
import Home from './Pages/Home';
import { Historique } from './components/Historique';
import { CreateAccountPage } from './components/CreateAccountPage';
import { PartsCatalogPage } from './Pages/PartsCatalogPage';
import './styles/theme.css';
import './App.css';
import { AppLayout } from './components/AppLayout';

function AppRoutes() {
  const navigate = useNavigate();
  const isAuthenticated = typeof window !== 'undefined' && localStorage.getItem('isAuthenticated') === 'true';
  const userRole = typeof window !== 'undefined' ? localStorage.getItem('userRole') : null;

  return (
    <Routes>
      <Route 
        path="/" 
        element={
          <LandingPage 
            onNavigateToLogin={() => navigate('/login')}
          />
        } 
      />
      <Route 
        path="/login" 
        element={
          <LoginPage 
            onLoginSuccess={() => {
              const role = localStorage.getItem('userRole');
              navigate(role === 'admin' ? '/admin' : '/dashboard');
            }}
            onNavigateToLanding={() => navigate('/')}
          />
        } 
      />
      <Route 
        path="/dashboard" 
        element={
          isAuthenticated ? (
            <AppLayout>
              <Home />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        } 
      />
      <Route
        path="/historique"
        element={
          isAuthenticated ? (
            <AppLayout>
              <Historique />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/admin"
        element={
          isAuthenticated && userRole === 'admin' ? (
            <AppLayout>
              <AdminDashboard />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/admin/historique"
        element={
          isAuthenticated && userRole === 'admin' ? (
            <AppLayout>
              <AdminHistorique />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/admin/create-account"
        element={
          isAuthenticated && userRole === 'admin' ? (
            <AppLayout>
              <CreateAccountPage />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/parts-catalog"
        element={
          isAuthenticated ? (
            <AppLayout>
              <PartsCatalogPage />
            </AppLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}