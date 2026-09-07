// src/components/ThemeToggle.tsx
import { Sun, Moon, Laptop, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';

interface ThemeToggleProps {
  compact?: boolean;
  variant?: 'segmented' | 'dropdown' | 'compact';
}

export default function ThemeToggle({ compact = false, variant = 'segmented' }: ThemeToggleProps) {
  const { theme, setTheme, isDark, toggleTheme } = useTheme();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (compact || variant === 'compact') {
    return (
      <button
        type="button"
        onClick={toggleTheme}
        className="p-2 rounded-full bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-amber-300 border border-slate-200/90 dark:border-slate-700 shadow-xs transition-all flex items-center justify-center cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
        title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        aria-label={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      >
        {isDark ? (
          <Sun size={15} aria-hidden="true" className="animate-in spin-in-180 duration-200 text-amber-400" />
        ) : (
          <Moon size={15} aria-hidden="true" className="text-slate-600 animate-in spin-in-180 duration-200" />
        )}
      </button>
    );
  }

  if (variant === 'dropdown') {
    return (
      <div className="relative inline-block text-left" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800/90 border border-slate-200/90 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold shadow-xs hover:border-slate-300 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
          aria-haspopup="true"
          aria-expanded={dropdownOpen}
          aria-label="Theme mode menu"
        >
          {theme === 'dark' ? (
            <Moon size={14} className="text-indigo-400" />
          ) : theme === 'light' ? (
            <Sun size={14} className="text-amber-500" />
          ) : (
            <Laptop size={14} className="text-slate-500" />
          )}
          <span className="capitalize">{theme}</span>
          <ChevronDown size={13} className={`text-slate-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropdownOpen && (
          <div className="absolute right-0 mt-1.5 w-32 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-1.5 space-y-0.5 z-50 animate-in fade-in slide-in-from-top-1">
            <button
              type="button"
              onClick={() => { setTheme('light'); setDropdownOpen(false); }}
              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                theme === 'light' ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Sun size={13} className="text-amber-500" />
              <span>Light</span>
            </button>
            <button
              type="button"
              onClick={() => { setTheme('dark'); setDropdownOpen(false); }}
              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                theme === 'dark' ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Moon size={13} className="text-indigo-400" />
              <span>Dark</span>
            </button>
            <button
              type="button"
              onClick={() => { setTheme('system'); setDropdownOpen(false); }}
              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                theme === 'system' ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Laptop size={13} className="text-slate-500" />
              <span>Auto</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // Segmented Capsule Style (Default)
  return (
    <div
      role="group"
      aria-label="Theme mode selection"
      className="bg-slate-100/90 dark:bg-slate-900/90 p-1 rounded-full border border-slate-200/90 dark:border-slate-800 flex items-center gap-0.5 text-xs shadow-2xs"
    >
      <button
        type="button"
        onClick={() => setTheme('light')}
        aria-pressed={theme === 'light'}
        aria-label="Light mode"
        className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
          theme === 'light'
            ? 'bg-white text-slate-900 shadow-xs'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
        }`}
        title="Light Mode"
      >
        <Sun size={12} className={theme === 'light' ? 'text-amber-500' : 'text-slate-400'} aria-hidden="true" />
        <span>Light</span>
      </button>

      <button
        type="button"
        onClick={() => setTheme('dark')}
        aria-pressed={theme === 'dark'}
        aria-label="Dark mode"
        className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5 transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
          theme === 'dark'
            ? 'bg-slate-800 text-white shadow-xs'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
        }`}
        title="Dark Mode"
      >
        <Moon size={12} className={theme === 'dark' ? 'text-indigo-300' : 'text-slate-400'} aria-hidden="true" />
        <span>Dark</span>
      </button>

      <button
        type="button"
        onClick={() => setTheme('system')}
        aria-pressed={theme === 'system'}
        aria-label="System automatic mode"
        className={`p-1 px-1.5 rounded-full text-[11px] font-bold transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
          theme === 'system'
            ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-xs'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
        }`}
        title="System Auto Mode"
      >
        <Laptop size={12} aria-hidden="true" />
      </button>
    </div>
  );
}
