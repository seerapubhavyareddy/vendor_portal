// src/components/layout/Header.js
import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Header.css';

const Header = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const [showManagementDropdown, setShowManagementDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const managementDropdownRef = useRef(null);

  // Fixed: Helper to determine if a link is active
  const isActiveLink = (path) => {
    // Handle exact path matching
    if (path === '/') {
      return location.pathname === '/' || location.pathname === '/dashboard';
    }
    if (path === '/products') {
      return location.pathname === '/products' || location.pathname.startsWith('/products');
    }
    if (path === '/management') {
      return location.pathname.startsWith('/management');
    }
    if (path === '/clinical-trial') {
      return location.pathname === '/clinical-trial';
    }
    return location.pathname === path;
  };

  // Handle logout function
  const handleLogout = () => {
    logout();
    navigate('/login');
    setShowDropdown(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
      if (managementDropdownRef.current && !managementDropdownRef.current.contains(event.target)) {
        setShowManagementDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Close dropdown on escape key
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setShowDropdown(false);
        setShowManagementDropdown(false);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, []);

  // Get user initials with fallback
  const getUserInitials = () => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
    }
    if (user?.firstName) {
      return user.firstName.charAt(0).toUpperCase();
    }
    if (user?.username) {
      return user.username.charAt(0).toUpperCase();
    }
    return 'U';
  };

  // Get user's full name with fallback
  const getUserFullName = () => {
    if (user?.firstName && user?.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    if (user?.firstName) {
      return user.firstName;
    }
    if (user?.username) {
      return user.username;
    }
    return 'User';
  };

  // Get user role display text
  const getUserRole = () => {
    const role = user?.role || 'vendor';
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  // Get user email with fallback
  const getUserEmail = () => {
    return user?.email || 'user@mannbiome.com';
  };

  // Handle dropdown toggle
  const toggleDropdown = () => {
    setShowDropdown(!showDropdown);
  };

  // Handle management dropdown toggle
  const toggleManagementDropdown = () => {
    setShowManagementDropdown(!showManagementDropdown);
  };

  // Handle navigation with dropdown close
  const handleNavigation = (path) => {
    setShowDropdown(false);
    setShowManagementDropdown(false);
    navigate(path);
  };

  // Check if user is a vendor
  // const isVendor = user?.role === 'vendor';

  // Debug: Log current path to console (remove this in production)
  console.log('Current path:', location.pathname);

  return (
    <header className="header">
      <div className="main-nav">
        <div className="container">
          <div className="brand">
            <Link to="/">
              <img
                src="/logo.png"
                alt="MannBiome"
                className="logo"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDE1MCAxNTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPGNpcmNsZSBjeD0iNzUiIGN5PSI3NSIgcj0iNzAiIGZpbGw9IiNGRkZGRkYiIHN0cm9rZT0iI0UwRTBFMCIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgPHBhdGggZD0iTTc1IDMwQzU0LjUgMzAgMzggNDYuNSAzOCA2N0MzOCA3Ny41IDQyLjUgODYuNSA1MCA5Mi41QzUyIDk0IDUzLjUgOTcgNTMuNSAxMDAuNVYxMDVDNTMuNSAxMTAgNTcuNSAxMTQgNjIuNSAxMTRIODcuNUM5Mi41IDExNCA5Ni41IDExMCA5Ni41IDEwNVYxMDAuNUM5Ni41IDk3IDk4IDk0IDEwMCA5Mi41QzEwNy41IDg2LjUgMTEyIDc3LjUgMTEyIDY3QzExMiA0Ni41IDk1LjUgMzAgNzUgMzBaIiBmaWxsPSIjRTFGNUYzIiBzdHJva2U9IiMwMEJGQTUiIHN0cm9rZS13aWR0aD0iMyIvPgogIDxjaXJjbGUgY3g9IjYyIiBjeT0iNjciIHI9IjUiIGZpbGw9IiMwMEJGQTUiLz4KICA8Y2lyY2xlIGN4PSI4OCIgY3k9IjY3IiByPSI1IiBmaWxsPSIjMDBCRkE1Ii8+CiAgPHBhdGggZD0iTTYwIDg1QzY1IDkyIDg1IDkyIDkwIDg1IiBzdHJva2U9IiMwMEJGQTUiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+Cjwvc3ZnPg==';
                }}
              />
            </Link>
          </div>

          <nav className="nav-links">
            {/* Home link - always visible, goes to VendorHub or Dashboard */}
            <Link to="/" className={isActiveLink('/') ? 'active' : ''}>
              🏠 Home
            </Link>

            {process.env.REACT_APP_ENABLE_DASHBOARD !== 'false' && (
              <Link to="/" className={isActiveLink('/') ? 'active' : ''}>
                Dashboard
              </Link>
            )}
            {process.env.REACT_APP_ENABLE_PRODUCTS !== 'false' && (
              <Link to="/products" className={isActiveLink('/products') ? 'active' : ''}>
                Our Products
              </Link>
            )}

            <Link to="/clinical-trial" className={isActiveLink('/clinical-trial') ? 'active' : ''}>
              Clinical Trial
            </Link>

            {/* Management dropdown - only for vendors */}
            {/* Management dropdown - for vendors and employees */}
            {(user?.role === 'vendor' || user?.role === 'employee') && (
              <div className="nav-dropdown" ref={managementDropdownRef}>
                <button
                  className={`nav-dropdown-trigger ${isActiveLink('/management') ? 'active' : ''}`}
                  onClick={toggleManagementDropdown}
                  aria-label="Management menu"
                  aria-expanded={showManagementDropdown}
                  aria-haspopup="true"
                >
                  Management
                  <span className={`dropdown-arrow ${showManagementDropdown ? 'open' : ''}`}>
                    ▼
                  </span>
                </button>

                {showManagementDropdown && (
                  <div className="nav-dropdown-menu">
                    {/* Only show Patients for vendors */}
                    {(user?.role === 'vendor' || user?.role === 'employee') && (
                      <button
                        className="nav-dropdown-item"
                        onClick={() => handleNavigation('/management/patients')}
                      >
                        <span className="item-icon">👥</span>
                        <div className="item-content">
                          <div className="item-title">Patients</div>
                          <div className="item-description">Manage patient accounts</div>
                        </div>
                      </button>
                    )}
                    {/* Employees - available to all vendors and employees */}
                    <button
                      className="nav-dropdown-item"
                      onClick={() => handleNavigation('/management/employees')}
                    >
                      <span className="item-icon">👨‍💼</span>
                      <div className="item-content">
                        <div className="item-title">Employees</div>
                        <div className="item-description">Manage team members</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* Compact User profile dropdown */}
          <div className="user-profile" ref={dropdownRef}>
            <button
              className="avatar-button"
              onClick={toggleDropdown}
              aria-label="User menu"
              aria-expanded={showDropdown}
              aria-haspopup="true"
            >
              <div className="avatar-circle">
                {getUserInitials()}
              </div>
              <span className="user-name-compact">{getUserFullName()}</span>
              <span className={`dropdown-arrow ${showDropdown ? 'open' : ''}`}>▼</span>
            </button>

            {showDropdown && (
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <div className="user-avatar-large">
                    {getUserInitials()}
                  </div>
                  <div className="user-info-dropdown">
                    <div className="user-name-full">{getUserFullName()}</div>
                    <div className="user-role-badge">{getUserRole()}</div>
                    <div className="user-email">{getUserEmail()}</div>
                  </div>
                </div>

                <div className="dropdown-divider"></div>

                <div className="dropdown-section">
                  <button
                    className="dropdown-item"
                    onClick={() => handleNavigation('/profile')}
                  >
                    <span className="item-icon">👤</span>
                    <span>My Profile</span>
                  </button>
                  <button
                    className="dropdown-item"
                    onClick={() => handleNavigation('/settings')}
                  >
                    <span className="item-icon">⚙️</span>
                    <span>Settings</span>
                  </button>
                  <button
                    className="dropdown-item"
                    onClick={() => handleNavigation('/billing')}
                  >
                    <span className="item-icon">💳</span>
                    <span>Billing</span>
                  </button>
                </div>

                <div className="dropdown-divider"></div>

                <div className="dropdown-section">
                  <button
                    className="dropdown-item logout"
                    onClick={handleLogout}
                  >
                    <span className="item-icon">🚪</span>
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;