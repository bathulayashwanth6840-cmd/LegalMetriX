// src/components/Navigation.tsx
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home, Camera, History, User, BookOpen,
  Globe, Video, FileText, TrendingUp, ShieldCheck,
  FileWarning, Search, LogOut, Sparkles, Edit3
} from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import type { Language } from '../i18n/LanguageContext';
import { useRole } from '../context/RoleContext';
import RoleSwitcher from './RoleSwitcher';
import ThemeToggle from './ThemeToggle';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: string;
  allowedRoles?: ('citizen' | 'inspector' | 'admin')[];
}

interface NavSection {
  title: string;
  hasDivider?: boolean;
  items: NavItem[];
}

export default function Navigation() {
  const { language, setLanguage, t } = useLanguage();
  const { currentRole, logout } = useRole();
  const location = useLocation();
  const navigate = useNavigate();

  const isItemActive = (itemTo: string) => {
    const currentFullPath = location.pathname + location.search;

    if (itemTo === '/') {
      return location.pathname === '/' && location.search === '';
    }

    if (itemTo.includes('?')) {
      return currentFullPath === itemTo;
    }

    if (itemTo === '/scan') {
      return location.pathname === '/scan' && !location.search.includes('mode=video360');
    }

    return location.pathname.startsWith(itemTo);
  };

  const normalizedRole = currentRole === 'senior_official' ? 'admin' : currentRole;

  // Master Navigation Blueprint with Role Access Control
  const rawNavSections: NavSection[] = [
    {
      title: 'MAIN',
      items: [
        {
          to: '/',
          icon: <Home size={17} aria-hidden="true" />,
          label: t('nav.home') || 'Dashboard',
          allowedRoles: ['citizen', 'inspector', 'admin'],
        },
        {
          to: '/citizen/scan',
          icon: <Camera size={17} aria-hidden="true" />,
          label: 'Scan Product',
          badge: 'AI',
          allowedRoles: ['citizen'],
        },
        {
          to: '/citizen/manual-entry',
          icon: <Edit3 size={17} aria-hidden="true" />,
          label: 'Manual Entry',
          allowedRoles: ['citizen'],
        },
        {
          to: '/scan',
          icon: <Camera size={17} aria-hidden="true" />,
          label: t('nav.scan') || 'New Inspection',
          allowedRoles: ['inspector', 'admin'],
        },
        {
          to: '/scan?mode=video360',
          icon: <Video size={17} aria-hidden="true" />,
          label: t('nav.video360') || '360° Scan',
          badge: '360°',
          allowedRoles: ['inspector', 'admin'],
        },
      ],
    },
    {
      title: 'COMPLAINTS',
      items: [
        {
          to: '/complaints',
          icon: <FileWarning size={17} aria-hidden="true" />,
          label: t('nav.complaints') || 'Complaints & Enquiries',
          badge: 'NEW',
          allowedRoles: ['citizen', 'inspector', 'admin'],
        },
        {
          to: '/track',
          icon: <Search size={17} aria-hidden="true" />,
          label: t('nav.track') || 'Track Complaint',
          allowedRoles: ['citizen', 'inspector', 'admin'],
        },
      ],
    },
    {
      title: 'INSPECTIONS',
      items: [
        {
          to: '/history',
          icon: <History size={17} aria-hidden="true" />,
          label: t('nav.history') || 'Inspection History',
          allowedRoles: ['inspector', 'admin'],
        },
        {
          to: '/reports',
          icon: <FileText size={17} aria-hidden="true" />,
          label: t('nav.reports') || 'Reports',
          allowedRoles: ['inspector', 'admin'],
        },
      ],
    },
    {
      title: 'ADMINISTRATION',
      hasDivider: true,
      items: [
        {
          to: '/analytics',
          icon: <TrendingUp size={17} aria-hidden="true" />,
          label: t('nav.analytics') || 'Compliance Analytics',
          allowedRoles: ['admin'],
        },
        {
          to: '/rules',
          icon: <BookOpen size={17} aria-hidden="true" />,
          label: t('nav.rules') || 'Rules & Act',
          allowedRoles: ['citizen', 'inspector', 'admin'],
        },
        {
          to: '/profile',
          icon: <User size={17} aria-hidden="true" />,
          label: t('nav.profile') || 'Settings & Profile',
          allowedRoles: ['citizen', 'inspector', 'admin'],
        },
      ],
    },
  ];

  // Dynamically filter sections and items for the current role
  const navSections = rawNavSections
    .map((sec) => ({
      ...sec,
      items: sec.items.filter(
        (item) => !item.allowedRoles || item.allowedRoles.includes(normalizedRole as any)
      ),
    }))
    .filter((sec) => sec.items.length > 0);

  // Dynamic Mobile bottom navigation items based on active role
  const rawMobileNavItems: NavItem[] = [
    { to: '/', icon: <Home size={18} aria-hidden="true" />, label: 'Dashboard', allowedRoles: ['citizen', 'inspector', 'admin'] },
    { to: '/citizen/scan', icon: <Camera size={18} aria-hidden="true" />, label: 'Scan', allowedRoles: ['citizen'] },
    { to: '/scan', icon: <Camera size={18} aria-hidden="true" />, label: 'Scan', allowedRoles: ['inspector', 'admin'] },
    { to: '/citizen/manual-entry', icon: <Edit3 size={18} aria-hidden="true" />, label: 'Manual', allowedRoles: ['citizen'] },
    { to: '/complaints', icon: <FileWarning size={18} aria-hidden="true" />, label: 'Complaints', allowedRoles: ['citizen', 'inspector', 'admin'] },
    { to: '/track', icon: <Search size={18} aria-hidden="true" />, label: 'Track', allowedRoles: ['citizen', 'inspector', 'admin'] },
    { to: '/history', icon: <History size={18} aria-hidden="true" />, label: 'History', allowedRoles: ['inspector', 'admin'] },
    { to: '/analytics', icon: <TrendingUp size={18} aria-hidden="true" />, label: 'Analytics', allowedRoles: ['admin'] },
    { to: '/profile', icon: <User size={18} aria-hidden="true" />, label: 'Profile', allowedRoles: ['citizen', 'inspector', 'admin'] },
  ];

  const mobileNavItems = rawMobileNavItems.filter(
    (item) => !item.allowedRoles || item.allowedRoles.includes(normalizedRole as any)
  );

  const languages: { code: Language; label: string; flag: string }[] = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
    { code: 'te', label: 'తెలుగు', flag: '🇮🇳' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* ── Desktop Sidebar ──────────────────────────────────────────────── */}
      <aside
        aria-label="Sidebar Navigation"
        className="hidden sm:flex flex-col w-64 bg-slate-900 dark:bg-slate-950 text-white min-h-screen flex-shrink-0 shadow-lg border-r border-slate-800/80 select-none"
      >
        {/* Header / Logo */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl overflow-hidden border border-slate-700 bg-white flex-shrink-0 shadow-sm flex items-center justify-center">
              <img
                src="/legal_metrology_logo.jpg"
                alt="Government of India Legal Metrology Logo"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <ShieldCheck size={22} className="text-blue-900" aria-hidden="true" />
            </div>
            <div>
              <span className="tracking-wide text-white block font-black text-base leading-tight">LegalMetriX</span>
              <span className="text-[9px] text-blue-300 font-bold tracking-wider uppercase block">
                Enforcement Portal
              </span>
            </div>
          </div>
        </div>

        {/* Live Role Persona in Sidebar */}
        <div className="px-3.5 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
          <RoleSwitcher align="left" variant="sidebar" />
          <span className="text-[9px] bg-amber-400/20 text-amber-300 font-bold px-1.5 py-0.5 rounded-full border border-amber-400/30 flex items-center gap-1">
            <Sparkles size={10} />
            <span>Demo</span>
          </span>
        </div>

        {/* Navigation items grouped by sections */}
        <nav aria-label="Main Navigation Menu" className="flex-1 py-3 overflow-y-auto px-3">
          {navSections.map((section, idx) => (
            <div
              key={section.title}
              className={`${idx > 0 ? 'mt-4' : ''} ${
                section.hasDivider ? 'border-t border-slate-800/80 pt-3 mt-4' : ''
              }`}
            >
              {/* Section Header */}
              <div
                id={`nav-sec-${section.title.toLowerCase()}`}
                className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400 select-none pointer-events-none"
              >
                {section.title}
              </div>

              {/* Section Nav Links */}
              <ul className="space-y-1" aria-labelledby={`nav-sec-${section.title.toLowerCase()}`}>
                {section.items.map((item) => {
                  const isActive = isItemActive(item.to);
                  return (
                    <li key={item.to}>
                      <Link
                        to={item.to}
                        aria-current={isActive ? 'page' : undefined}
                        className={`flex items-center justify-between px-3 py-2 rounded-xl font-medium text-xs transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                          isActive
                            ? 'bg-blue-600 text-white font-bold shadow-xs'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          {item.icon}
                          <span>{item.label}</span>
                        </div>
                        {item.badge && (
                          <span
                            className={`text-[8px] px-1.5 py-0.5 rounded-full uppercase transition-all ${
                              isActive
                                ? 'bg-amber-400 text-slate-950 font-black shadow-2xs'
                                : 'bg-amber-400/20 text-amber-300 border border-amber-400/30 font-bold'
                            }`}
                          >
                            <span className="sr-only">Notification: </span>
                            {item.badge}
                          </span>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Demo Mode Subtitle Indicator */}
        <div className="px-3.5 py-2 bg-slate-950/60 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono flex items-center justify-between">
          <span>Demo Mode — SIH 2024</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
        </div>

        {/* Theme Mode Toggle & Logout in Sidebar footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
          <ThemeToggle />
          <button
            type="button"
            onClick={handleLogout}
            title="Logout of Demo Session"
            className="p-2 text-rose-400 hover:text-white hover:bg-rose-950/60 rounded-xl transition-colors cursor-pointer flex items-center gap-1 text-xs font-bold"
          >
            <LogOut size={14} />
            <span className="text-[10px]">Logout</span>
          </button>
        </div>

        {/* Language Selector Section */}
        <div className="p-3.5 border-t border-slate-800/80 bg-slate-950/50">
          <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-300">
            <Globe size={13} aria-hidden="true" />
            <span>Language / भाषा / భాష</span>
          </div>
          <div
            role="group"
            aria-label="Language selection"
            className="grid grid-cols-3 gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800"
          >
            {languages.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => setLanguage(lang.code)}
                aria-pressed={language === lang.code}
                aria-label={`Change language to ${lang.label}`}
                className={`py-1 px-1 rounded-lg text-xs font-medium transition-all text-center flex flex-col items-center gap-0.5 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                  language === lang.code
                    ? 'bg-blue-600 text-white font-bold shadow-xs'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
                title={lang.label}
              >
                <span className="text-[11px] leading-none" aria-hidden="true">{lang.flag}</span>
                <span className="text-[9px] leading-tight font-bold">{lang.label}</span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Mobile Top Role Switcher Bar ─────────────────────────────────── */}
      <header className="sm:hidden bg-slate-900 dark:bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between text-white">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-amber-400" aria-hidden="true" />
          <span className="font-bold text-xs">LegalMetriX</span>
          <span className="text-[8px] bg-amber-400/20 text-amber-300 font-bold px-1.5 py-0.2 rounded-full">Demo</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle compact />
          <RoleSwitcher align="right" />
        </div>
      </header>

      {/* ── Mobile Bottom Tab Bar ────────────────────────────────────────── */}
      <nav
        aria-label="Mobile Bottom Navigation"
        className="sm:hidden fixed bottom-0 w-full bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 z-50 shadow-lg transition-colors"
      >
        <div className="flex justify-around items-center">
          {mobileNavItems.map((item) => {
            const active = isItemActive(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                aria-current={active ? 'page' : undefined}
                className={`flex flex-col items-center py-2 px-1 w-full text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                  active ? 'text-blue-600 dark:text-blue-400 font-bold' : 'text-slate-400 dark:text-slate-500 font-normal'
                }`}
              >
                {item.icon}
                <span className="text-[9px] mt-0.5 truncate max-w-[60px]">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
