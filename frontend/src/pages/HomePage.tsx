import { Link } from 'react-router-dom';
import { useEffect, useState, useMemo } from 'react';
import { useRole } from '../context/RoleContext';
import {
  Camera, ShieldCheck, Sparkles, ArrowRight,
  Video, Eye, RefreshCw, FileWarning, ChevronRight,
  Search, TrendingUp, History as HistoryIcon, Edit3
} from 'lucide-react';
import { getStoredComplaints } from '../services/complaintService';
import type { ComplaintRecord } from '../types/complaint';
import { evaluateCanonicalCompliance } from '../utils/complianceEngine';

export default function HomePage() {
  const { profile, isCitizen, isOfficer, isAdmin } = useRole();
  const [scans, setScans] = useState<any[]>([]);
  const [complaints, setComplaints] = useState<ComplaintRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchScansAndComplaints();
  }, [apiUrl]);

  const fetchScansAndComplaints = () => {
    setLoading(true);
    // 1. Fetch live inspections from backend if available
    fetch(`${apiUrl}/api/scans/`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setScans(data);
        }
      })
      .catch((err) => console.warn('Failed to fetch dashboard stats:', err))
      .finally(() => setLoading(false));

    // 2. Load stored statutory complaints
    const complaintList = getStoredComplaints();
    setComplaints(complaintList);
  };

  // Compute live real metrics from scans
  const stats = useMemo(() => {
    const total = scans.length;
    let compliant = 0;
    let needsReview = 0;
    let nonCompliant = 0;
    let scoreSum = 0;
    let scoredCount = 0;
    let totalViolations = 0;

    const violationTypes: Record<string, number> = {
      'MRP Declaration': 0,
      'Net Quantity': 0,
      'Manufacturer Address': 0,
      'Consumer Care': 0,
      'Mfg Date / Expiry': 0,
      'Font Size / Placement': 0,
    };

    scans.forEach((s) => {
      const canonical = evaluateCanonicalCompliance({ serverScan: s });
      if (canonical.status === 'COMPLIANT') {
        compliant++;
      } else if (canonical.status === 'NON-COMPLIANT') {
        nonCompliant++;
      } else {
        needsReview++;
      }

      scoreSum += canonical.score;
      scoredCount++;
      totalViolations += canonical.failedChecks;

      const rules = s.extracted_fields?.rules_evaluated || [];
      rules.forEach((r: any) => {
        if (r.status === 'FAIL') {
          if (r.rule_code?.includes('6(1)(e)') || r.rule_name?.toLowerCase().includes('mrp')) {
            violationTypes['MRP Declaration']++;
          } else if (r.rule_code?.includes('12') || r.rule_name?.toLowerCase().includes('quantity')) {
            violationTypes['Net Quantity']++;
          } else if (r.rule_name?.toLowerCase().includes('manufacturer') || r.rule_name?.toLowerCase().includes('address')) {
            violationTypes['Manufacturer Address']++;
          } else if (r.rule_name?.toLowerCase().includes('consumer') || r.rule_name?.toLowerCase().includes('care')) {
            violationTypes['Consumer Care']++;
          } else if (r.rule_name?.toLowerCase().includes('date') || r.rule_name?.toLowerCase().includes('mfg')) {
            violationTypes['Mfg Date / Expiry']++;
          } else {
            violationTypes['Font Size / Placement']++;
          }
        }
      });
    });

    const avgScore = scoredCount > 0 ? Math.round(scoreSum / scoredCount) : total > 0 ? 86 : 0;
    const passRate = total > 0 ? Math.round((compliant / total) * 100) : 0;

    return {
      total,
      compliant,
      needsReview,
      nonCompliant,
      avgScore,
      totalViolations,
      passRate,
      violationTypes,
    };
  }, [scans]);

  // Compute complaint statistics across the 8 statutory statuses
  const complaintStats = useMemo(() => {
    const total = complaints.length;
    const submitted = complaints.filter((c) => c.currentStatus === 'Submitted').length;
    const underReview = complaints.filter((c) => c.currentStatus === 'Under Review').length;
    const furtherEnquiry = complaints.filter((c) => c.currentStatus === 'Further Enquiry').length;
    const awaitingVerification = complaints.filter((c) => c.currentStatus === 'Awaiting Verification').length;
    const verifiedViolation = complaints.filter((c) => c.currentStatus === 'Verified Violation').length;
    const notVerified = complaints.filter((c) => c.currentStatus === 'Not Verified').length;
    const actionTaken = complaints.filter((c) => c.currentStatus === 'Action Taken').length;
    const closed = complaints.filter((c) => c.currentStatus === 'Closed').length;

    // Cases requiring urgent officer attention
    const pendingVerificationList = complaints.filter(
      (c) => c.currentStatus === 'Awaiting Verification' || c.currentStatus === 'Further Enquiry' || c.currentStatus === 'Under Review'
    ).slice(0, 3);

    return {
      total,
      submitted,
      underReview,
      furtherEnquiry,
      awaitingVerification,
      verifiedViolation,
      notVerified,
      actionTaken,
      closed,
      pendingVerificationList,
    };
  }, [complaints]);

  const recentScans = scans.slice(0, 5);

  return (
    <div className="flex flex-col min-h-full select-none pb-24 sm:pb-12 bg-[#F8F9FA] dark:bg-[#0B1120] transition-colors">
      {/* ── Top Hero Banner with Clean White Public-Service Aesthetic ──────────── */}
      <div className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white pt-7 pb-10 px-4 sm:px-8 border-b border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
              <div className={`inline-flex items-center gap-2 border px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase mb-2.5 ${
                isCitizen
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-300'
                  : 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-800 text-blue-950 dark:text-blue-300'
              }`}>
                <Sparkles size={12} className={isCitizen ? 'text-emerald-700 dark:text-emerald-400' : 'text-blue-700 dark:text-blue-400'} />
                <span>
                  {isCitizen
                    ? 'CITIZEN PORTAL • OPEN PUBLIC ACCESS (NO LOGIN REQUIRED)'
                    : `SIH 2024 LEGAL METROLOGY AI PLATFORM • ${profile.badge}`}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                {isCitizen
                  ? 'Citizen Packaging Consumer Check Portal'
                  : isAdmin
                  ? 'Central Metrology Directorate & Compliance Dashboard'
                  : 'Enforcement Officer Packaging Inspection Dashboard'}
              </h1>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 mt-1.5 max-w-2xl leading-relaxed font-medium">
                {isCitizen
                  ? 'Scan a packaged product to check its declared information with AI. Instant public access — no username or password required.'
                  : isAdmin
                  ? 'Executive regulatory dashboard for real-time compliance tracking, statutory enforcement analytics, and multi-zone audit trail inspection.'
                  : 'Autonomous AI inspection suite for verifying packaged commodity declarations under the Legal Metrology (Packaged Commodities) Rules, 2011.'}
              </p>
            </div>

            {/* Role-Tailored Quick Action Buttons */}
            <div className="flex flex-wrap items-center gap-2.5">
              {isCitizen ? (
                <>
                  <Link
                    to="/citizen/scan"
                    className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm rounded-full shadow-xs flex items-center gap-2 transition-all active:scale-[0.98]"
                  >
                    <Camera size={16} />
                    <span>Scan Product</span>
                    <ArrowRight size={14} />
                  </Link>

                  <Link
                    to="/citizen/manual-entry"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-2 transition-all active:scale-[0.98]"
                  >
                    <Edit3 size={14} />
                    <span>Enter Details Manually</span>
                  </Link>

                  <Link
                    to="/complaints"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-1.5 transition-all"
                  >
                    <FileWarning size={14} />
                    <span>My Complaints</span>
                  </Link>
                </>
              ) : isOfficer ? (
                <>
                  <Link
                    to="/scan"
                    className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm rounded-full shadow-xs flex items-center gap-2 transition-all active:scale-[0.98]"
                  >
                    <Camera size={15} />
                    <span>New Inspection</span>
                    <ArrowRight size={13} />
                  </Link>

                  <Link
                    to="/scan?mode=video360"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-1.5 transition-all active:scale-[0.98]"
                  >
                    <Video size={14} />
                    <span>360° Video Scan</span>
                  </Link>

                  <Link
                    to="/history"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-1.5 transition-all"
                  >
                    <HistoryIcon size={14} />
                    <span>History</span>
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/scan"
                    className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm rounded-full shadow-xs flex items-center gap-2 transition-all active:scale-[0.98]"
                  >
                    <Camera size={15} />
                    <span>New Inspection</span>
                    <ArrowRight size={13} />
                  </Link>

                  <Link
                    to="/analytics"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-1.5 transition-all active:scale-[0.98]"
                  >
                    <TrendingUp size={14} />
                    <span>Analytics</span>
                  </Link>

                  <Link
                    to="/complaints"
                    className="px-4 py-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs flex items-center gap-1.5 transition-all"
                  >
                    <FileWarning size={14} />
                    <span>Complaints</span>
                  </Link>
                </>
              )}

              <button
                type="button"
                onClick={fetchScansAndComplaints}
                className="p-2.5 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs transition-all cursor-pointer"
                title="Refresh Live Metrics"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </button>
            </div>
          </div>

          {/* ── 6 Real Analytics Stats Cards (Officer / Admin only) ───────── */}
          {!isCitizen && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mt-7">
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-slate-600 dark:text-slate-400 block">Total Audits</span>
                <span className="text-3xl font-black text-slate-900 dark:text-white mt-1 block">{stats.total}</span>
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Logged packages</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-emerald-800 dark:text-emerald-400 block">Compliant</span>
                <span className="text-3xl font-black text-emerald-900 dark:text-emerald-300 mt-1 block">{stats.compliant}</span>
                <span className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold">{stats.passRate}% pass rate</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-amber-800 dark:text-amber-400 block">Needs Review</span>
                <span className="text-3xl font-black text-amber-900 dark:text-amber-300 mt-1 block">{stats.needsReview}</span>
                <span className="text-xs text-amber-700 dark:text-amber-400 font-semibold">Officer inspection</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-rose-800 dark:text-rose-400 block">Non-Compliant</span>
                <span className="text-3xl font-black text-rose-900 dark:text-rose-300 mt-1 block">{stats.nonCompliant}</span>
                <span className="text-xs text-rose-700 dark:text-rose-400 font-semibold">Statutory breaches</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-slate-700 dark:text-slate-300 block">Violations</span>
                <span className="text-3xl font-black text-slate-900 dark:text-white mt-1 block">{stats.totalViolations}</span>
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Defects identified</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-blue-800 dark:text-blue-400 block">Avg Score</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-3xl font-black text-blue-900 dark:text-blue-300">{stats.avgScore}</span>
                  <span className="text-xs text-slate-500 font-bold">/ 100</span>
                </div>
                <span className="text-xs text-blue-700 dark:text-blue-400 font-semibold">Statutory index</span>
              </div>
            </div>
          )}

          {/* ── Citizen Summary Counter Cards ─────────────────────────────── */}
          {isCitizen && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-7">
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-slate-600 dark:text-slate-400 block">My Complaints</span>
                <span className="text-3xl font-black text-slate-900 dark:text-white mt-1 block">{complaintStats.total}</span>
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Registered dockets</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-blue-800 dark:text-blue-400 block">Under Review</span>
                <span className="text-3xl font-black text-blue-900 dark:text-blue-300 mt-1 block">{complaintStats.underReview + complaintStats.submitted}</span>
                <span className="text-xs text-blue-700 dark:text-blue-400 font-semibold">Queued for review</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-amber-800 dark:text-amber-400 block">In Progress</span>
                <span className="text-3xl font-black text-amber-900 dark:text-amber-300 mt-1 block">{complaintStats.awaitingVerification + complaintStats.furtherEnquiry}</span>
                <span className="text-xs text-amber-700 dark:text-amber-400 font-semibold">Field inspection</span>
              </div>

              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-xs">
                <span className="text-[11px] uppercase tracking-wider font-bold text-emerald-800 dark:text-emerald-400 block">Resolved</span>
                <span className="text-3xl font-black text-emerald-900 dark:text-emerald-300 mt-1 block">{complaintStats.actionTaken + complaintStats.closed}</span>
                <span className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold">Action concluded</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Main Content Body ────────────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 mt-6 space-y-6 w-full">

        {/* ── CITIZEN SPECIFIC DASHBOARD BODY ─────────────────────────────── */}
        {isCitizen ? (
          <div className="space-y-6">
            {/* Primary Action Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <div className="bg-slate-900 dark:bg-slate-800 rounded-2xl p-6 sm:p-7 text-white border border-slate-800 dark:border-slate-700 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="w-11 h-11 rounded-xl bg-white/10 flex items-center justify-center mb-4 text-slate-100">
                    <Camera size={22} />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">Scan Product Label</h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-6 font-normal">
                    Take a photo of any packaged product (front, back, or declarations panel) to let AI automatically extract and assess mandatory Legal Metrology declarations.
                  </p>
                </div>
                <Link
                  to="/citizen/scan"
                  className="py-2.5 px-5 bg-white text-slate-900 hover:bg-slate-100 font-semibold text-xs sm:text-sm rounded-xl shadow-2xs flex items-center justify-center gap-2 transition-all self-start active:scale-[0.98]"
                >
                  <Camera size={15} />
                  <span>Start Consumer Scan</span>
                  <ArrowRight size={13} />
                </Link>
              </div>

              <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 sm:p-7 border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col justify-between">
                <div>
                  <div className="w-11 h-11 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center mb-4">
                    <Edit3 size={22} />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Enter Details Manually</h3>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-6 font-normal">
                    If you cannot capture a clear photo, enter the printed details (MRP, Net Qty, Dates, Manufacturer) manually to run a consumer compliance check.
                  </p>
                </div>
                <Link
                  to="/citizen/manual-entry"
                  className="py-2.5 px-5 bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white font-semibold text-xs sm:text-sm rounded-xl shadow-2xs flex items-center justify-center gap-2 transition-all self-start active:scale-[0.98]"
                >
                  <Edit3 size={15} />
                  <span>Enter Details Manually</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>

            {/* Quick Track Complaint Bar */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-700/80 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold">
                  <Search size={18} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">Track an Existing Complaint</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Enter your official CMP tracking number to see current verification status.</p>
                </div>
              </div>

              <Link
                to="/track"
                className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow-2xs flex items-center gap-1.5 transition-all self-stretch sm:self-auto justify-center"
              >
                <span>Track Complaint Docket</span>
                <ChevronRight size={14} />
              </Link>
            </div>
          </div>
        ) : (
          /* ── INSPECTOR / ADMIN DASHBOARD BODY ──────────────────────────── */
          <>
            <div className="bg-white dark:bg-slate-800/90 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-700/80 shadow-2xs space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-700/60 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 text-[10px] font-bold rounded-full uppercase border border-blue-200/80 dark:border-blue-800/60">
                      Statutory Enforcement Cell
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">LMR Rules 2011 Active Dockets</span>
                  </div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-lg mt-1">
                    Complaint & Enquiry Overview
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Real-time breakdown of all statutory enquiries across the 8 administrative and verification stages.
                  </p>
                </div>

                <Link
                  to="/complaints"
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-xl text-xs font-medium flex items-center gap-2 shadow-2xs transition-colors self-start sm:self-auto cursor-pointer"
                >
                  <span>View All Complaints ({complaintStats.total})</span>
                  <ArrowRight size={13} />
                </Link>
              </div>

          {/* 8 Status Counter Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
            <Link
              to="/complaints?status=Submitted"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-slate-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-slate-700 dark:text-slate-300 block">1. Submitted</span>
              <span className="text-2xl font-black text-slate-900 dark:text-white mt-1 block">{complaintStats.submitted}</span>
              <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">New filings</span>
            </Link>

            <Link
              to="/complaints?status=Under Review"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-blue-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-blue-800 dark:text-blue-300 block">2. Review</span>
              <span className="text-2xl font-black text-blue-900 dark:text-blue-200 mt-1 block">{complaintStats.underReview}</span>
              <span className="text-[10px] font-semibold text-blue-600 dark:text-blue-400">AI analysis</span>
            </Link>

            <Link
              to="/complaints?status=Further Enquiry"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-amber-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-amber-800 dark:text-amber-300 block">3. Enquiry</span>
              <span className="text-2xl font-black text-amber-900 dark:text-amber-200 mt-1 block">{complaintStats.furtherEnquiry}</span>
              <span className="text-[10px] font-semibold text-amber-700 dark:text-amber-400">Zonal audit</span>
            </Link>

            <Link
              to="/complaints?status=Awaiting Verification"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-purple-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-purple-800 dark:text-purple-300 block">4. Awaiting</span>
              <span className="text-2xl font-black text-purple-900 dark:text-purple-200 mt-1 block">{complaintStats.awaitingVerification}</span>
              <span className="text-[10px] font-semibold text-purple-600 dark:text-purple-400">Senior review</span>
            </Link>

            <Link
              to="/complaints?status=Verified Violation"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-rose-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-rose-800 dark:text-rose-300 block">5. Verified</span>
              <span className="text-2xl font-black text-rose-900 dark:text-rose-200 mt-1 block">{complaintStats.verifiedViolation}</span>
              <span className="text-[10px] font-semibold text-rose-700 dark:text-rose-400">Confirmed breach</span>
            </Link>

            <Link
              to="/complaints?status=Not Verified"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-slate-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-slate-700 dark:text-slate-300 block">6. Dismissed</span>
              <span className="text-2xl font-black text-slate-900 dark:text-white mt-1 block">{complaintStats.notVerified}</span>
              <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">Compliant</span>
            </Link>

            <Link
              to="/complaints?status=Action Taken"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-emerald-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-emerald-800 dark:text-emerald-300 block">7. Action</span>
              <span className="text-2xl font-black text-emerald-900 dark:text-emerald-200 mt-1 block">{complaintStats.actionTaken}</span>
              <span className="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400">Fine/Remedy</span>
            </Link>

            <Link
              to="/complaints?status=Closed"
              className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-teal-300 shadow-2xs transition-all"
            >
              <span className="text-[11px] uppercase font-bold text-teal-800 dark:text-teal-300 block">8. Closed</span>
              <span className="text-2xl font-black text-teal-900 dark:text-teal-200 mt-1 block">{complaintStats.closed}</span>
              <span className="text-[10px] font-semibold text-teal-600 dark:text-teal-400">Final docket</span>
            </Link>
          </div>
        </div>

        {/* ── NEW EXTENSION: PENDING OFFICIAL VERIFICATION QUEUE ───────────── */}
        <div className="bg-white dark:bg-slate-800/90 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-700/80 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-700/60 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-[10px] font-bold rounded-full uppercase border border-amber-200/80 dark:border-amber-800/60">
                  Senior Authority Queue
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Requires Authorized Official Sign-off</span>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white mt-1">
                Pending Official Verification & Forwarded Cases
              </h3>
            </div>

            <Link
              to="/complaints?status=Awaiting Verification"
              className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 self-start sm:self-auto"
            >
              <span>View Verification Queue</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          {complaintStats.pendingVerificationList.length === 0 ? (
            <div className="py-6 px-4 text-center text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/70 dark:border-slate-700/60">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">No Pending Verification Dockets</p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Cases flagged during packaged commodity scanning or manual filings will appear here for statutory sign-off.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {complaintStats.pendingVerificationList.map((c) => (
                <div
                  key={c.id}
                  className="bg-slate-50/70 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/80 p-4 rounded-xl space-y-2 hover:bg-slate-100/80 dark:hover:bg-slate-700/60 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono font-bold text-xs text-slate-900 dark:text-white">{c.id}</span>
                      <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200/80 dark:border-amber-800/60">
                        {c.currentStatus}
                      </span>
                    </div>
                    <h4 className="font-bold text-xs text-slate-900 dark:text-white mt-1 truncate">{c.product.productName}</h4>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 line-clamp-2">
                      {c.findings[0]?.detectedText || c.location}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-200/70 dark:border-slate-700/60 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">Ref: {c.inspectionId}</span>
                    <Link
                      to={`/complaints/${c.id}`}
                      className="px-3 py-1 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-lg text-[11px] font-medium inline-flex items-center gap-1 shadow-2xs"
                    >
                      <span>Verify Docket</span>
                      <ChevronRight size={12} />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── 360° Feature Spotlight Card ─────────────────────────────────── */}
        <div className="bg-slate-900 dark:bg-slate-850 rounded-2xl p-6 text-white border border-slate-800 dark:border-slate-700/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 bg-amber-400/20 text-amber-200 border border-amber-400/30 text-[10px] font-bold rounded-full uppercase">
                Featured SIH Innovation
              </span>
              <span className="text-xs text-slate-300 font-medium">Single-Clip Continuous Capture</span>
            </div>
            <h3 className="text-lg font-bold text-white">
              360° Intelligent Packaging Rotation Scanner
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed font-normal">
              Rotate a package in front of your camera in one continuous clip. Our intelligent video pipeline automatically filters motion blur, extracts sharp keyframes across all angles, and fuses multi-surface declarations into a unified legal compliance dossier.
            </p>
          </div>

          <Link
            to="/scan?mode=video360"
            className="px-5 py-2.5 bg-white text-slate-900 hover:bg-slate-100 font-semibold text-xs rounded-xl shadow-2xs inline-flex items-center justify-center gap-2 transition-all self-start md:self-auto cursor-pointer flex-shrink-0"
          >
            <Video size={15} className="text-slate-700" />
            <span>Launch 360° Scanner</span>
          </Link>
        </div>

        {/* ── Officer-Centric Inspection Workflow Overview ──────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-slate-800/90 p-5 rounded-2xl shadow-2xs border border-slate-200/80 dark:border-slate-700/80 flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-300 border border-blue-200/80 dark:border-blue-800/60 flex items-center justify-center flex-shrink-0 font-bold">
              <Camera size={20} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider block">STAGE 1</span>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm mt-0.5">Package Capture & Identification</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                Capture single images, 4-panel multi-surfaces, or 360° rotation video with barcode decoding.
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800/90 p-5 rounded-2xl shadow-2xs border border-slate-200/80 dark:border-slate-700/80 flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-600 flex items-center justify-center flex-shrink-0 font-bold">
              <Sparkles size={20} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">STAGE 2</span>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm mt-0.5">AI Evidence Assistance Layer</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                PaddleOCR + Gemini Vision assist by parsing mandatory declarations without guessing uncertain text.
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800/90 p-5 rounded-2xl shadow-2xs border border-slate-200/80 dark:border-slate-700/80 flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800/60 flex items-center justify-center flex-shrink-0 font-bold">
              <ShieldCheck size={20} />
            </div>
            <div>
              <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block">STAGE 3</span>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm mt-0.5">Officer Verification & Legal Report</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                Deterministic rule engine evaluates LMR 2011; officer confirms verdict and generates certified PDF docket.
              </p>
            </div>
          </div>
        </div>

        {/* ── Recent Inspections Table ────────────────────────────────────── */}
        <div className="bg-white dark:bg-slate-800/90 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-700/80 shadow-2xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-700/60 pb-4">
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-lg">Recent Enforcement Inspections</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Latest commodity packaging audits recorded in system</p>
            </div>

            <Link
              to="/history"
              className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 self-start sm:self-auto"
            >
              <span>View Full History ({stats.total})</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          {/* ── Desktop & Tablet Table ────────────────────────────────── */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200/80 dark:border-slate-700 text-slate-500 dark:text-slate-400 font-semibold bg-slate-50/70 dark:bg-slate-800/60">
                  <th className="p-3.5">ID</th>
                  <th className="p-3.5">Product Name</th>
                  <th className="p-3.5">Audit Date</th>
                  <th className="p-3.5">Method</th>
                  <th className="p-3.5">Compliance Score</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                {recentScans.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-10 text-slate-400">
                      No inspections found. Click "New Inspection" to start your first scan!
                    </td>
                  </tr>
                ) : (
                  recentScans.map((s) => {
                    const prodName = s.extracted_fields?.product_name || s.extracted_fields?.brand_name || 'Packaged Commodity Sample';
                    const canonical = evaluateCanonicalCompliance({ serverScan: s });
                    const is360 = !!s.extracted_fields?.sides_ocr;

                    return (
                      <tr key={s.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-750 transition-colors">
                        <td className="p-3.5 font-mono font-bold text-slate-900 dark:text-slate-100">#{s.id}</td>
                        <td className="p-3.5">
                          <span className="font-bold text-slate-900 dark:text-slate-100 block max-w-xs truncate">{prodName}</span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            MRP: {s.extracted_fields?.mrp || '₹--'} • Qty: {s.extracted_fields?.net_quantity || '--'}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-600 dark:text-slate-400">
                          {new Date(s.created_at || Date.now()).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="p-3.5">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            is360 ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60' : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200'
                          }`}>
                            {is360 ? '🎥 360° Video' : '📷 Multi-Side'}
                          </span>
                        </td>
                        <td className="p-3.5">
                          <div className="flex items-center gap-1.5 font-bold">
                            <span className={canonical.score >= 85 ? 'text-emerald-600 dark:text-emerald-400' : canonical.score >= 55 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'}>
                              {canonical.score}
                            </span>
                            <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                          </div>
                        </td>
                        <td className="p-3.5">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${canonical.textBadgeClass}`}>
                            {canonical.status === 'COMPLIANT' ? '✅ Compliant' : canonical.status === 'NON-COMPLIANT' ? '❌ Non-Compliant' : '⚠️ Needs Review'}
                          </span>
                        </td>
                        <td className="p-3.5 text-right">
                          <Link
                            to={`/scan/${s.id}`}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-medium inline-flex items-center gap-1 transition-all"
                          >
                            <Eye size={12} /> View Dossier
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* ── Mobile Responsive Stacked Cards (<768px, single-hand use) ── */}
          <div className="block md:hidden space-y-3">
            {recentScans.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs bg-slate-50 dark:bg-slate-800/40 rounded-2xl p-4">
                No inspections found. Click "New Inspection" to start your first scan!
              </div>
            ) : (
              recentScans.map((s) => {
                const prodName = s.extracted_fields?.product_name || s.extracted_fields?.brand_name || 'Packaged Commodity Sample';
                const canonical = evaluateCanonicalCompliance({ serverScan: s });
                const is360 = !!s.extracted_fields?.sides_ocr;

                return (
                  <div
                    key={s.id}
                    className="bg-slate-50/80 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200/80 dark:border-slate-700 shadow-2xs space-y-3 transition-all"
                  >
                    {/* Top Row: ID & Status Badge */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-slate-900 dark:text-white bg-white dark:bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
                          #{s.id}
                        </span>
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          is360 ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60' : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200'
                        }`}>
                          {is360 ? '🎥 360°' : '📷 Multi-Side'}
                        </span>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${canonical.textBadgeClass}`}>
                        {canonical.status === 'COMPLIANT' ? '✅ Compliant' : canonical.status === 'NON-COMPLIANT' ? '❌ Non-Compliant' : '⚠️ Review'}
                      </span>
                    </div>

                    {/* Middle: Product & Metadata */}
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white text-sm leading-snug">{prodName}</h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                        MRP: {s.extracted_fields?.mrp || '₹--'} • Qty: {s.extracted_fields?.net_quantity || '--'}
                      </p>
                    </div>

                    {/* Score Bar */}
                    <div className="flex items-center justify-between bg-white dark:bg-slate-800 p-2.5 rounded-xl border border-slate-200/70 dark:border-slate-700 text-xs">
                      <span className="text-[10px] uppercase font-semibold text-slate-400">Compliance Score</span>
                      <div className="flex items-baseline gap-1 font-bold">
                        <span className={canonical.score >= 85 ? 'text-emerald-700 dark:text-emerald-400' : canonical.score >= 55 ? 'text-amber-700 dark:text-amber-400' : 'text-rose-700 dark:text-rose-400'}>
                          {canonical.score}
                        </span>
                        <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                      </div>
                    </div>

                    {/* Bottom: Date & Full-Width Thumb CTA */}
                    <div className="pt-1 flex flex-col gap-2 border-t border-slate-200/60 dark:border-slate-700">
                      <span className="text-[10px] text-slate-400 font-medium">
                        Audited on: {new Date(s.created_at || Date.now()).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                      <Link
                        to={`/scan/${s.id}`}
                        className="w-full py-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-xl text-xs font-medium flex items-center justify-center gap-1.5 shadow-2xs transition-colors"
                      >
                        <Eye size={13} />
                        <span>View Inspection Dossier</span>
                      </Link>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
        </>
        )}
      </div>
    </div>
  );
}
