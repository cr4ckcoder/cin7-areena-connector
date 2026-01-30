import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Configuration from './pages/Configuration';
import Tools from './pages/Tools';
import Logs from './pages/Logs';
import Login from './pages/Login';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={
          <PrivateRoute>
            <Layout>
               <Dashboard />
            </Layout>
          </PrivateRoute>
        } />
        
        <Route path="/settings" element={
          <PrivateRoute>
             <Layout>
                <Configuration />
             </Layout>
          </PrivateRoute>
        } />
        
        <Route path="/tools" element={
          <PrivateRoute>
             <Layout>
                <Tools />
             </Layout>
          </PrivateRoute>
        } />
        
        <Route path="/logs" element={
          <PrivateRoute>
             <Layout>
                <Logs />
             </Layout>
          </PrivateRoute>
        } />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
