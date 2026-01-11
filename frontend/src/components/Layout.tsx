import { NavLink } from 'react-router-dom';
import { ReactNode } from 'react';

// Simple icon components to replace lucide-react
const Icon = ({ children }: { children: ReactNode }) => (
  <span style={{ width: 18, height: 18, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
    {children}
  </span>
);

const LayoutDashboardIcon = () => <Icon>&#9632;</Icon>;
const SearchIcon = () => <Icon>&#128269;</Icon>;
const UsersIcon = () => <Icon>&#128101;</Icon>;
const ActivityIcon = () => <Icon>&#128200;</Icon>;
const ClockIcon = () => <Icon>&#128339;</Icon>;
const MapIcon = () => <Icon>&#127759;</Icon>;
const DatabaseIcon = () => <Icon>&#128451;</Icon>;
const AlertIcon = () => <Icon>&#9888;</Icon>;
const SettingsIcon = () => <Icon>&#9881;</Icon>;

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <span>OSINT</span> Platform
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">Overview</div>
            <NavLink
              exact
              to="/"
              className="nav-item"
              activeClassName="active"
            >
              <LayoutDashboardIcon />
              Dashboard
            </NavLink>
            <NavLink
              to="/query"
              className="nav-item"
              activeClassName="active"
            >
              <SearchIcon />
              Query
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Intelligence</div>
            <NavLink
              to="/entities"
              className="nav-item"
              activeClassName="active"
            >
              <UsersIcon />
              Entities
            </NavLink>
            <NavLink
              to="/analysis"
              className="nav-item"
              activeClassName="active"
            >
              <ActivityIcon />
              Analysis
            </NavLink>
            <NavLink
              to="/temporal"
              className="nav-item"
              activeClassName="active"
            >
              <ClockIcon />
              Temporal
            </NavLink>
            <NavLink
              to="/map"
              className="nav-item"
              activeClassName="active"
            >
              <MapIcon />
              Geographic
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Data</div>
            <NavLink
              to="/sources"
              className="nav-item"
              activeClassName="active"
            >
              <DatabaseIcon />
              Sources
            </NavLink>
            <NavLink
              to="/alerts"
              className="nav-item"
              activeClassName="active"
            >
              <AlertIcon />
              Alerts
            </NavLink>
          </div>

          <div className="nav-section" style={{ marginTop: 'auto' }}>
            <NavLink
              to="/settings"
              className="nav-item"
              activeClassName="active"
            >
              <SettingsIcon />
              Settings
            </NavLink>
          </div>
        </nav>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
