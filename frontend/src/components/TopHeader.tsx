// src/components/TopHeader.tsx
import { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Bell, ShieldCheck, Sparkles, Globe, ChevronDown, Check } from 'lucide-react';
import { useRole } from '../context/RoleContext';
import { useLanguage, type Language } from '../i18n/LanguageContext';
import ThemeToggle from './ThemeToggle';
import RoleSwitcher from './RoleSwitcher';
import { getStoredComplaints } from '../services/complaintService';

export default function TopHeader() {
  const { isCitizen } = useRole();
  const { language, setLanguage } = useLanguage();
  const location = useLocation();
  const [unreadNotifications, setUnreadNotifications] = useState<number>(0);
  const [langMenuOpen, setLangMenuOpen] = useState<boolean>(false);
  const [notifMenuOpen, setNotifMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    // Count active complaints needing attention
    const complaints = getStoredComplaints();
    const pending = complaints.filter(
      (c) => c.currentStatus === 'Submitted' || c.currentStatus === 'Awaiting Verification' || c.currentStatus === 'Further Enquiry'
    ).length;
    setUnreadNotifications(pending > 0 ? pending : 2);
  }, [location.pathname]);

  const languages: { code: Language; label: string; flag: string }[] = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
    { code: 'te', label: 'తెలుగు', flag: '🇮🇳' },
  ];

  // Helper to determine title/breadcrumb based on current route
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') {
      return isCitizen ? 'Citizen Consumer Portal' : 'Statutory Inspection Dashboard';
    }
    if (path === '/citizen/scan') return 'Consumer Product Scanner';
    if (path === '/citizen/manual-entry') return 'Manual Product Entry';
    if (path === '/scan') return 'Packaging Inspection Scanner';
    if (path.startsWith('/scan/')) return 'Inspection Dossier';
    if (path === '/complaints') return 'Statutory Complaints & Enquiries';
    if (path.startsWith('/complaints/')) return 'Complaint Investigation Docket';
    if (path === '/track') return 'Track Complaint Status';
    if (path === '/history') return 'Field Inspection History';
    if (path === '/reports') return 'Certified Assessment Reports';
    if (path === '/analytics') return 'Directorate Compliance Analytics';
    if (path === '/rules') return 'Legal Metrology Rules 2011';
    if (path === '/profile') return 'System & Profile Settings';
    return 'LegalMetriX Portal';
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 px-4 sm:px-8 py-2.5 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Left Side: Page Context & Emblem */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center flex-shrink-0 shadow-2xs">
              <ShieldCheck size={18} className="text-blue-600 dark:text-blue-400" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h2 className="text-xs sm:text-sm font-black text-slate-900 dark:text-white truncate">
                  {getPageTitle()}
                </h2>
                <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.2 rounded-full text-[9px] font-black uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  <Sparkles size={9} className="text-amber-500" />
                  <span>SIH 2024</span>
                </span>
              </div>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate hidden sm:block">
                Dept. of Consumer Affairs • Legal Metrology (Packaged Commodities) Rules, 2011
              </p>
            </div>
          </div>
        </div>

        {/* Right Side: Capsule Navigation Controls */}
        <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
          {/* Notification Bell Capsule */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setNotifMenuOpen(!notifMenuOpen)}
              className="relative p-2 rounded-full bg-white dark:bg-slate-800/90 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200/90 dark:border-slate-700 shadow-2xs transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Notifications & Active Alerts"
              aria-label="Notifications"
            >
              <Bell size={16} />
              {unreadNotifications > 0 && (
                <span className="absolute top-0.5 right-0.5 w-4 h-4 bg-rose-500 text-white font-black text-[9px] rounded-full flex items-center justify-center shadow-xs border-2 border-white dark:border-slate-900">
                  {unreadNotifications}
                </span>
              )}
            </button>

            {/* Notifications Dropdown Panel */}
            {notifMenuOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-xs font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                    <Bell size={13} className="text-blue-600" />
                    <span>Active Notifications</span>
                  </span>
                  <span className="text-[10px] bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-bold px-2 py-0.5 rounded-full">
                    {unreadNotifications} New
                  </span>
                </div>
                <div className="space-y-2 py-2 text-xs">
                  <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
                    <p className="font-bold text-slate-900 dark:text-white text-[11px]">
                      {isCitizen ? 'Consumer Complaint Submitted' : 'Statutory Docket Awaiting Review'}
                    </p>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {isCitizen
                        ? 'Your recent product report CMP-2026-567935 is under official inspection.'
                        : 'New complaint docket flagged for Rule 6(1)(e) MRP violation.'}
                    </p>
                  </div>
                  <div className="p-2 rounded-xl bg-amber-50/70 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60">
                    <p className="font-bold text-amber-900 dark:text-amber-300 text-[11px]">
                      Legal Metrology AI Engine Active
                    </p>
                    <p className="text-[10px] text-amber-700 dark:text-amber-400 mt-0.5">
                      PaddleOCR + Gemini 2.5 Vision pipeline ready for instant label verification.
                    </p>
                  </div>
                </div>
                <Link
                  to="/complaints"
                  onClick={() => setNotifMenuOpen(false)}
                  className="w-full mt-1 py-1.5 text-center block text-[11px] font-bold text-blue-600 dark:text-blue-400 hover:underline"
                >
                  View All Complaints →
                </Link>
              </div>
            )}
          </div>

          {/* Theme Capsule Segmented Control (Sun / Moon / Auto) */}
          <div className="hidden sm:block">
            <ThemeToggle />
          </div>

          {/* Role Switcher Pill */}
          <div className="hidden sm:block">
            <RoleSwitcher align="right" />
          </div>

          {/* Language Selector Capsule */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setLangMenuOpen(!langMenuOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800/90 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200/90 dark:border-slate-700 shadow-2xs text-xs font-semibold transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Change Language"
              aria-label="Language menu"
            >
              <Globe size={14} className="text-slate-500 dark:text-slate-400" />
              <span className="uppercase text-[11px] font-bold">{language}</span>
              <ChevronDown size={12} className={`text-slate-400 transition-transform ${langMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {langMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-36 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-1.5 space-y-0.5 z-50 animate-in fade-in slide-in-from-top-1">
                {languages.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() => {
                      setLanguage(l.code);
                      setLangMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                      language === l.code
                        ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-bold'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{l.flag}</span>
                      <span>{l.label}</span>
                    </div>
                    {language === l.code && <Check size={13} className="text-blue-600 dark:text-blue-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
