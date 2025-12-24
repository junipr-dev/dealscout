import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import AuthCallback from './pages/AuthCallback'
import Deals from './pages/Deals'
import DealDetail from './pages/DealDetail'
import CurrentFlips from './pages/CurrentFlips'
import ListItem from './pages/ListItem'
import Profits from './pages/Profits'
import Settings from './pages/Settings'
import './App.css'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* App routes with Layout */}
      <Route element={<Layout />}>
        <Route path="/deals" element={<Deals />} />
        <Route path="/deals/:id" element={<DealDetail />} />
        <Route path="/flips" element={<CurrentFlips />} />
        <Route path="/list-item/:flipId" element={<ListItem />} />
        <Route path="/profits" element={<Profits />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      {/* Redirect old routes */}
      <Route path="/app" element={<Navigate to="/deals" replace />} />
    </Routes>
  )
}

export default App
