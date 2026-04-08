import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Health from './pages/Health';
import Nutrition from './pages/Nutrition';
import Activity from './pages/Activity';
import Analytics from './pages/Analytics';
import Patients from './pages/Patients';
import Footer from './components/Footer';

function App() {
  return (
    <Router>
      <div className='app'>
        <nav className='navbar'>
          <div className='nav-container'>
            <h1 className='logo'>📊 MSPR Dashboard</h1>
            <ul className='nav-menu'>
              <li><Link to="/">Accueil</Link></li>
              <li><Link to="/patients">Patients</Link></li>
              <li><Link to="/health">Santé</Link></li>
              <li><Link to="/nutrition">Nutrition</Link></li>
              <li><Link to="/activity">Activité</Link></li>
              <li><Link to="/analytics">Analytics</Link></li>
            </ul>
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
          </Routes>
        </main>

        <Footer />
      </div>
    </Router>
  );
}

export default App;

