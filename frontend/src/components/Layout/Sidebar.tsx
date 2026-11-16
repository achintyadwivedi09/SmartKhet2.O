import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Map, Database, FlaskConical,
  Cpu, Cloud, TestTube2, FileText, Leaf
} from 'lucide-react';

const navItems = [
  { to: '/',             icon: LayoutDashboard, label: 'Overview' },
  { to: '/farms',        icon: Map,             label: 'Farm Monitoring' },
  { to: '/bigdata',      icon: Database,        label: 'Big Data Analytics' },
  { to: '/ml',           icon: FlaskConical,    label: 'ML Lab' },
  { to: '/fog',          icon: Cpu,             label: 'Fog Nodes' },
  { to: '/cloud',        icon: Cloud,           label: 'Cloud Monitoring' },
  { to: '/experiments',  icon: TestTube2,       label: 'Experiment Lab' },
  { to: '/audit',        icon: FileText,        label: 'Data Audit' },
];

export default function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-sk-primary flex flex-col shadow-lg">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-green-700/40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-sk-accent rounded-lg flex items-center justify-center shadow">
            <Leaf className="w-5 h-5 text-sk-primary" />
          </div>
          <div>
            <div className="text-white font-bold text-base leading-tight">SmartKhet</div>
            <div className="text-sk-accent text-xs font-medium">v2.0 — Tamil Nadu</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-sk-accent/20 text-white border border-sk-accent/30'
                  : 'text-green-200 hover:text-white hover:bg-white/10'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-green-700/40">
        <div className="text-green-300 text-xs">
          <div className="font-semibold text-green-200 mb-0.5">SmartKhet 2.0</div>
          <div>Big Data + ML + Fog</div>
          <div className="mt-1 text-green-400">© 2024 Tamil Nadu AgriTech</div>
        </div>
      </div>
    </aside>
  );
}
