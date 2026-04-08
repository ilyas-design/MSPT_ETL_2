import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import Health from './pages/Health';
import Nutrition from './pages/Nutrition';
import Activity from './pages/Activity';
import Analytics from './pages/Analytics';
import Patients from './pages/Patients';
import Footer from './components/Footer';
import Login from './pages/Login';
import Admin from './pages/Admin';
import { apiService } from './services/api';

function NavAuth() {
  const navigate = useNavigate();
  const [isAuthed, setIsAuthed] = useState(apiService.isAuthenticated());

  useEffect(() => {
    const onStorage = () => setIsAuthed(apiService.isAuthenticated());
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const actions = useMemo(() => {
    if (isAuthed) {
      return (
        <button
          className="btn btn-secondary btn-sm"
          type="button"
          onClick={() => {
            apiService.logout();
            setIsAuthed(false);
            navigate('/login');
          }}
        >
          Se déconnecter
        </button>
      );
    }
    return (
      <Link className="btn btn-primary btn-sm" to="/login">
        Se connecter
      </Link>
    );
  }, [isAuthed, navigate]);

  return <div className="nav-actions">{actions}</div>;
}

function App() {
  return (
    <Router>
      <div className='app'>
        <nav className='navbar'>
          <div className='nav-container'>
            <h1 className='logo'>MSPR Dashboard</h1>
            <ul className='nav-menu'>
              <li><Link to="/">Tableau de bord</Link></li>
              <li><Link to="/patients">Patients</Link></li>
              <li><Link to="/health">Santé</Link></li>
              <li><Link to="/nutrition">Nutrition</Link></li>
              <li><Link to="/activity">Activité</Link></li>
              <li><Link to="/analytics">Analytics</Link></li>
              <li><Link to="/admin">Admin</Link></li>
            </ul>
            <NavAuth />
          </div>
        </nav>

        <main className='main-content'>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/health" element={<Health />} />
            <Route path="/nutrition" element={<Nutrition />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/patients" element={<Patients />} />
            <Route path="/login" element={<Login />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </main>

        <Footer />
      </div>
    </Router>
  );
}

export default App;

