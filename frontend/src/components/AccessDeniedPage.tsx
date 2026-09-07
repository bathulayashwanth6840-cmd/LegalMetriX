// src/components/AccessDeniedPage.tsx
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, UserCheck, Shield, Sparkles } from 'lucide-react';
import { useRole } from '../context/RoleContext';
import type { UserRole } from '../types/complaint';

interface AccessDeniedPageProps {
  requiredRoleName?: string;
  targetFeatureName?: string;
}

export default function AccessDeniedPage({
  requiredRoleName = 'Legal Metrology Officer or Administrator',
  targetFeatureName = 'this enforcement module',
}: AccessDeniedPageProps) {
  const { currentRole, setRole, profile } = useRole();

  const handleQuickSwitch = (role: UserRole) => {
    setRole(role);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4 sm:p-6 select-none">
      <div className="max-w-xl w-full theme-card overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Top Header Strip */}
        <div className="bg-slate-900 dark:bg-slate-950 p-6 sm:p-8 text-white text-center relative overflow-hidden border-b border-slate-800">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center mx-auto mb-3 shadow-inner">
            <ShieldAlert size={28} className="text-rose-400" aria-hidden="true" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-widest bg-rose-950/60 text-rose-300 px-3 py-1 rounded-full border border-rose-500/30 inline-block mb-2">
            RBAC Access Guard • Hackathon Demo Mode
          </span>
          <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
            Access Restricted
          </h1>
          <p className="text-xs text-slate-300 dark:text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
            You do not possess the necessary role credentials to view {targetFeatureName}.
          </p>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">
          {/* Current Role Card */}
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Your Current Active Role:
              </span>
              <span className="text-[10px] font-mono font-black uppercase px-2.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200">
                {profile.badge}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-black text-base shadow-sm">
                {profile.avatarLetter}
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                  {profile.displayName}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {profile.designation}
                </p>
              </div>
            </div>
          </div>

          {/* Explanation Alert */}
          <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-900 dark:text-amber-200 space-y-1">
            <span className="font-bold block flex items-center gap-1.5">
              <span>⚠️ Authorization Required:</span>
              <span className="underline">{requiredRoleName}</span>
            </span>
            <p className="text-[11px] text-amber-800/90 dark:text-amber-300/80 leading-relaxed font-medium">
              In accordance with Legal Metrology statutory enforcement workflows, only authorized officers and administrators may access direct enforcement inspection tools, analytical intelligence, and backend audit trails.
            </p>
          </div>

          {/* Quick Role Switcher for Hackathon Presentation */}
          <div className="space-y-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              💡 Presentation Quick Switch:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {currentRole !== 'inspector' && (
                <button
                  type="button"
                  onClick={() => handleQuickSwitch('inspector')}
                  className="p-3 bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/50 dark:hover:bg-blue-900/60 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800 rounded-2xl text-xs font-bold flex items-center justify-between gap-2 transition-all cursor-pointer shadow-2xs"
                >
                  <div className="flex items-center gap-2">
                    <Shield size={16} className="text-blue-600 dark:text-blue-400" />
                    <div className="text-left">
                      <span className="block font-bold">Switch to Officer</span>
                      <span className="text-[10px] text-blue-600/80 dark:text-blue-300 font-normal">Field Inspector #LM-204</span>
                    </div>
                  </div>
                  <Sparkles size={14} />
                </button>
              )}

              {currentRole !== 'admin' && (
                <button
                  type="button"
                  onClick={() => handleQuickSwitch('admin')}
                  className="p-3 bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/50 dark:hover:bg-indigo-900/60 text-indigo-800 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-800 rounded-2xl text-xs font-bold flex items-center justify-between gap-2 transition-all cursor-pointer shadow-2xs"
                >
                  <div className="flex items-center gap-2">
                    <UserCheck size={16} className="text-indigo-600 dark:text-indigo-400" />
                    <div className="text-left">
                      <span className="block font-bold">Switch to Admin</span>
                      <span className="text-[10px] text-indigo-600/80 dark:text-indigo-300 font-normal">Central Directorate</span>
                    </div>
                  </div>
                  <Sparkles size={14} />
                </button>
              )}

              {currentRole !== 'citizen' && (
                <button
                  type="button"
                  onClick={() => handleQuickSwitch('citizen')}
                  className="p-3 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/50 dark:hover:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800 rounded-2xl text-xs font-bold flex items-center justify-between gap-2 transition-all cursor-pointer shadow-2xs"
                >
                  <div className="flex items-center gap-2">
                    <Shield size={16} className="text-emerald-600 dark:text-emerald-400" />
                    <div className="text-left">
                      <span className="block font-bold">Switch to Citizen</span>
                      <span className="text-[10px] text-emerald-600/80 dark:text-emerald-300 font-normal">Consumer Portal</span>
                    </div>
                  </div>
                  <Sparkles size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Return to Dashboard CTA */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <Link
              to="/"
              className="w-full py-3.5 bg-slate-900 hover:bg-slate-800 text-white rounded-full text-xs font-black flex items-center justify-center gap-2 shadow-sm transition-all active:scale-[0.99]"
            >
              <ArrowLeft size={16} />
              <span>Return to Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
