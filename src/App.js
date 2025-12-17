// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import VendorHub from './pages/VendorHub';
import Login from './pages/Login';
import Signup from './pages/Signup';
import SignupPending from './pages/SignupPending';
import Unauthorized from './pages/Unauthorized';
import MyProducts from './pages/MyProducts';
import Employees from './pages/Employees';
import Patients from './pages/PatientManagement';
import Billing from './pages/Billing';
import ClinicalTrialDashboard from './pages/ClinicalTrialDashboard';
import Header from './components/layout/Header';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import ForgotPassword from './pages/ForgotPassword';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/signup-pending" element={<SignupPending />} />
            <Route path="/unauthorized" element={<Unauthorized />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />


            {/* Protected routes */}
            {/* Default landing page - VendorHub is shown when Dashboard is disabled */}
            {process.env.REACT_APP_ENABLE_DASHBOARD === 'false' && (
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <>
                      <Header />
                      <div className="content">
                        <VendorHub />
                      </div>
                    </>
                  </ProtectedRoute>
                }
              />
            )}

            {/* Dashboard - enabled by REACT_APP_ENABLE_DASHBOARD flag */}
            {process.env.REACT_APP_ENABLE_DASHBOARD !== 'false' && (
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <>
                      <Header />
                      <div className="content">
                        <Dashboard />
                      </div>
                    </>
                  </ProtectedRoute>
                }
              />
            )}

            {/* Products - enabled by REACT_APP_ENABLE_PRODUCTS flag */}
            {process.env.REACT_APP_ENABLE_PRODUCTS !== 'false' && (
              <Route
                path="/products"
                element={
                  <ProtectedRoute>
                    <>
                      <Header />
                      <div className="content">
                        <MyProducts />
                      </div>
                    </>
                  </ProtectedRoute>
                }
              />
            )}

            {/* Management Routes */}
            <Route
              path="/management/patients"
              element={
                <ProtectedRoute>
                  <>
                    <Header />
                    <div className="content">
                      <Patients />
                    </div>
                  </>
                </ProtectedRoute>
              }
            />

            <Route
              path="/management/employees"
              element={
                <ProtectedRoute>
                  <>
                    <Header />
                    <div className="content">
                      <Employees />
                    </div>
                  </>
                </ProtectedRoute>
              }
            />

            <Route
              path="/billing"
              element={
                <ProtectedRoute>
                  <>
                    <Header />
                    <div className="content">
                      <Billing />
                    </div>
                  </>
                </ProtectedRoute>
              }
            />

            <Route
              path="/clinical-trial"
              element={
                <ProtectedRoute>
                  <>
                    <Header />
                    <div className="content">
                      <ClinicalTrialDashboard />
                    </div>
                  </>
                </ProtectedRoute>
              }
            />

            {/* Add more protected routes as needed */}
            {/* <Route
              path="/analytics"
              element={
                <ProtectedRoute requiredRole="vendor">
                  <>
                    <Header />
                    <div className="content">
                      <Analytics />
                    </div>
                  </>
                </ProtectedRoute>
              }
            /> */}

            {/* <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <>
                    <Header />
                    <div className="content">
                      <Settings />
                    </div>
                  </>
                </ProtectedRoute>
              }
            /> */}
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;