import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ScreenerPage from './pages/ScreenerPage';
import AIPage from './pages/AIPage';
import BacktestPage from './pages/BacktestPage';
import PortfolioPage from './pages/PortfolioPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<ScreenerPage />} />
          <Route path="/ai" element={<AIPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
