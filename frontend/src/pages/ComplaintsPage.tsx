import { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  FileWarning, Search, Plus,
  Eye, RefreshCw, Trash2, Camera, Sparkles, Download, ShieldCheck, Zap
} from 'lucide-react';
import {
  getStoredComplaints,
  createComplaintRecord,
  clearAllComplaints
} from '../services/complaintService';
import type { ComplaintRecord, ComplaintStatus } from '../types/complaint';
import { useRole } from '../context/RoleContext';
import NewComplaintModal from '../components/NewComplaintModal';
import { generateComplaintAssessmentPDF } from '../utils/pdfGenerator';

const STATUS_CONFIG: Record<
  ComplaintStatus,
  { label: string; badgeClass: string; dotColor: string }
> = {
  Submitted: {
    label: 'Submitted',
    badgeClass: 'bg-blue-50 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800',
    dotColor: 'bg-blue-500',
  },
  'Under Review': {
    label: 'Under Review',
    badgeClass: 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
    dotColor: 'bg-indigo-500',
  },
  'Further Enquiry': {
    label: 'Further Enquiry',
    badgeClass: 'bg-amber-50 dark:bg-amber-950/60 text-amber-900 dark:text-amber-300 border-amber-300 dark:border-amber-700 font-bold',
    dotColor: 'bg-amber-500',
  },
  'Awaiting Verification': {
    label: 'Awaiting Verification',
    badgeClass: 'bg-purple-50 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800',
    dotColor: 'bg-purple-500',
  },
  'Verified Violation': {
    label: 'Verified Violation',
    badgeClass: 'bg-rose-50 dark:bg-rose-950/60 text-rose-900 dark:text-rose-300 border-rose-300 dark:border-rose-800 font-black',
    dotColor: 'bg-rose-600',
  },
  'Not Verified': {
    label: 'Not Verified',
    badgeClass: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700',
    dotColor: 'bg-slate-400',
  },
  'Action Taken': {
    label: 'Action Taken',
    badgeClass: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 font-bold',
    dotColor: 'bg-emerald-500',
  },
  Closed: {
    label: 'Closed',
    badgeClass: 'bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-300 border-teal-200 dark:border-teal-800',
    dotColor: 'bg-teal-500',
  },
};

export default function ComplaintsPage() {
  const { currentRole, profile, isCitizen } = useRole();
  const [searchParams] = useSearchParams();
  const [complaints, setComplaints] = useState<ComplaintRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);

  useEffect(() => {
    loadComplaints();
    if (searchParams.get('action') === 'new' || searchParams.get('new') === 'true') {
      setIsNewModalOpen(true);
    }
  }, [searchParams]);

  const loadComplaints = () => {
    setLoading(true);
    const data = getStoredComplaints();
    setComplaints(data);
    setLoading(false);
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all complaint and enquiry records?')) {
      clearAllComplaints();
      setComplaints([]);
    }
  };

  const handleCreateComplaint = (payload: Parameters<typeof createComplaintRecord>[0]) => {
    createComplaintRecord({
      ...payload,
      submittedBy: `${profile.name} (${profile.badge})`,
      submitterRole: currentRole === 'inspector' ? 'Inspector' : currentRole === 'senior_official' ? 'Inspector' : 'Citizen',
    });
    setComplaints(getStoredComplaints());
    setIsNewModalOpen(false);
  };

  // Status Counts
  const stats = useMemo(() => {
    const total = complaints.length;
    const submitted = complaints.filter((c) => c.currentStatus === 'Submitted').length;
    const underReview = complaints.filter((c) => c.currentStatus === 'Under Review').length;
    const furtherEnquiry = complaints.filter((c) => c.currentStatus === 'Further Enquiry').length;
    const awaitingVerif = complaints.filter((c) => c.currentStatus === 'Awaiting Verification').length;
    const verifiedViolation = complaints.filter((c) => c.currentStatus === 'Verified Violation').length;
    const notVerified = complaints.filter((c) => c.currentStatus === 'Not Verified').length;
    const actionTaken = complaints.filter((c) => c.currentStatus === 'Action Taken').length;
    const closed = complaints.filter((c) => c.currentStatus === 'Closed').length;

    return {
      total,
      submitted,
      underReview,
      furtherEnquiry,
      awaitingVerif,
      verifiedViolation,
      notVerified,
      actionTaken,
      closed,
    };
  }, [complaints]);

  // Filtered complaints list
  const filteredComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        c.id.toLowerCase().includes(q) ||
        c.product.productName.toLowerCase().includes(q) ||
        c.product.brand.toLowerCase().includes(q) ||
        c.inspectionId.toLowerCase().includes(q) ||
        c.location.toLowerCase().includes(q) ||
        c.submittedBy.toLowerCase().includes(q);

      const matchesStatus = selectedStatus === 'ALL' || c.currentStatus === selectedStatus;
      const matchesPriority = selectedPriority === 'ALL' || c.priority === selectedPriority;

      return matchesQuery && matchesStatus && matchesPriority;
    });
  }, [complaints, searchQuery, selectedStatus, selectedPriority]);

  return (
    <div className="flex flex-col min-h-full select-none pb-24 sm:pb-12 bg-[#F6F8FA] dark:bg-[#090E1A] transition-colors">
      {/* ── Top Header Banner with Modern Soft Aesthetic ────────────────── */}
      <div className="bg-slate-900 dark:bg-slate-950 text-white pt-8 pb-10 px-4 sm:px-8 border-b border-slate-800/80 shadow-2xs">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 bg-blue-950/80 border border-blue-500/40 px-3 py-1 rounded-full text-[10px] font-black tracking-widest text-blue-300 uppercase mb-3">
                <FileWarning size={12} className="text-amber-400" />
                <span>STATUTORY COMPLAINT & ENQUIRY CELL</span>
              </div>
              <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
                Legal Metrology Complaints & Enquiries
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 dark:text-slate-400 mt-2 max-w-2xl leading-relaxed font-medium">
                Official investigation management, inter-departmental forwarding, physical verification dockets, and statutory enforcement actions.
              </p>
            </div>

            {/* Header Actions */}
            <div className="flex flex-wrap items-center gap-3">
              <Link
                to={isCitizen ? "/citizen/scan" : "/scan"}
                className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-black text-xs rounded-full shadow-md flex items-center gap-2 transition-all active:scale-[0.98] cursor-pointer"
              >
                <Camera size={15} />
                <span>{isCitizen ? "Scan Product" : "Scan to Verify"}</span>
              </Link>

              <button
                type="button"
                onClick={() => setIsNewModalOpen(true)}
                className="px-4 py-3 bg-white/10 hover:bg-white/20 text-white font-bold text-xs rounded-full border border-white/20 flex items-center gap-2 transition-all cursor-pointer"
              >
                <Plus size={15} />
                <span>File Manual Docket</span>
              </button>

              {complaints.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="px-4 py-3 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-bold text-xs rounded-full border border-rose-500/30 flex items-center gap-2 transition-all cursor-pointer"
                  title="Clear All History"
                >
                  <Trash2 size={15} />
                  <span>Clear</span>
                </button>
              )}

              <button
                type="button"
                onClick={loadComplaints}
                className="p-3 bg-white/10 hover:bg-white/20 text-white rounded-full border border-white/20 transition-all cursor-pointer"
                title="Refresh Records"
              >
                <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              </button>
            </div>
          </div>

          {/* ── 8 Statutory Status Metrics Filter Pills ─────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5 mt-8">
            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Submitted' ? 'ALL' : 'Submitted')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Submitted'
                  ? 'bg-blue-600 border-blue-400 text-white shadow-xs'
                  : 'bg-white/10 border-white/15 text-blue-100 hover:bg-white/15'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block opacity-80">1. Submitted</span>
              <span className="text-xl font-black block mt-0.5">{stats.submitted}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Under Review' ? 'ALL' : 'Under Review')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Under Review'
                  ? 'bg-indigo-600 border-indigo-400 text-white shadow-xs'
                  : 'bg-white/10 border-white/15 text-indigo-100 hover:bg-white/15'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block opacity-80">2. Review</span>
              <span className="text-xl font-black block mt-0.5">{stats.underReview}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Further Enquiry' ? 'ALL' : 'Further Enquiry')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Further Enquiry'
                  ? 'bg-amber-500 border-amber-400 text-slate-950 shadow-xs'
                  : 'bg-amber-950/50 border-amber-500/40 text-amber-200 hover:bg-amber-900/60'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block">3. Enquiry</span>
              <span className="text-xl font-black block mt-0.5">{stats.furtherEnquiry}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Awaiting Verification' ? 'ALL' : 'Awaiting Verification')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Awaiting Verification'
                  ? 'bg-purple-600 border-purple-400 text-white shadow-xs'
                  : 'bg-purple-950/50 border-purple-500/40 text-purple-200 hover:bg-purple-900/60'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block">4. Awaiting</span>
              <span className="text-xl font-black block mt-0.5">{stats.awaitingVerif}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Verified Violation' ? 'ALL' : 'Verified Violation')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Verified Violation'
                  ? 'bg-rose-600 border-rose-400 text-white shadow-xs'
                  : 'bg-rose-950/50 border-rose-500/40 text-rose-200 hover:bg-rose-900/60'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block">5. Verified</span>
              <span className="text-xl font-black block mt-0.5">{stats.verifiedViolation}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Not Verified' ? 'ALL' : 'Not Verified')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Not Verified'
                  ? 'bg-slate-700 border-slate-500 text-white shadow-xs'
                  : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block opacity-80">6. Dismissed</span>
              <span className="text-xl font-black block mt-0.5">{stats.notVerified}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Action Taken' ? 'ALL' : 'Action Taken')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Action Taken'
                  ? 'bg-emerald-600 border-emerald-400 text-white shadow-xs'
                  : 'bg-emerald-950/50 border-emerald-500/40 text-emerald-200 hover:bg-emerald-900/60'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block">7. Action</span>
              <span className="text-xl font-black block mt-0.5">{stats.actionTaken}</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedStatus(selectedStatus === 'Closed' ? 'ALL' : 'Closed')}
              className={`p-3 rounded-2xl border transition-all text-left cursor-pointer ${
                selectedStatus === 'Closed'
                  ? 'bg-teal-600 border-teal-400 text-white shadow-xs'
                  : 'bg-white/10 border-white/15 text-teal-100 hover:bg-white/15'
              }`}
            >
              <span className="text-[9px] uppercase font-bold tracking-wider block opacity-80">8. Closed</span>
              <span className="text-xl font-black block mt-0.5">{stats.closed}</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Main Body & Docket List ──────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 -mt-4 space-y-6 w-full">
        {/* Search & Filter Controls Bar */}
        <div className="theme-card p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-lg">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Complaint ID (e.g. LM-2026-XXXXXX), Product, Inspection #, or Location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 text-xs bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Status Filter Dropdown */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3.5 py-2 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="ALL">All Statuses ({complaints.length})</option>
              <option value="Submitted">Submitted ({stats.submitted})</option>
              <option value="Under Review">Under Review ({stats.underReview})</option>
              <option value="Further Enquiry">Further Enquiry ({stats.furtherEnquiry})</option>
              <option value="Awaiting Verification">Awaiting Verification ({stats.awaitingVerif})</option>
              <option value="Verified Violation">Verified Violation ({stats.verifiedViolation})</option>
              <option value="Not Verified">Not Verified ({stats.notVerified})</option>
              <option value="Action Taken">Action Taken ({stats.actionTaken})</option>
              <option value="Closed">Closed ({stats.closed})</option>
            </select>

            {/* Priority Filter */}
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="px-3.5 py-2 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="ALL">All Priorities</option>
              <option value="High">🔴 High Priority</option>
              <option value="Medium">🟡 Medium Priority</option>
              <option value="Low">🟢 Low Priority</option>
            </select>

            {/* View Mode Toggle (Cards vs Table) */}
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-full border border-slate-200 dark:border-slate-700 text-xs">
              <button
                type="button"
                onClick={() => setViewMode('cards')}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  viewMode === 'cards' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Cards
              </button>
              <button
                type="button"
                onClick={() => setViewMode('table')}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  viewMode === 'table' ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Table
              </button>
            </div>

            {(selectedStatus !== 'ALL' || selectedPriority !== 'ALL' || searchQuery) && (
              <button
                type="button"
                onClick={() => {
                  setSelectedStatus('ALL');
                  setSelectedPriority('ALL');
                  setSearchQuery('');
                }}
                className="px-3 py-1.5 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-full transition-colors cursor-pointer"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* ── Section Title: Statutory Complaint & Enquiry Assessment Dockets ── */}
        <div className="flex items-center justify-between px-1">
          <h2 className="text-base sm:text-lg font-black text-slate-900 dark:text-white flex items-center gap-2">
            <span className="p-1 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 text-amber-600">
              <FileWarning size={16} />
            </span>
            <span>Statutory Complaint & Enquiry Assessment Dockets ({filteredComplaints.length})</span>
          </h2>
          <span className="text-[11px] font-mono text-slate-400">
            LMR ACT 2009 • PACKAGED COMMODITIES RULES 2011
          </span>
        </div>

        {/* ── Empty State ── */}
        {filteredComplaints.length === 0 ? (
          <div className="theme-card py-20 px-4 text-center max-w-lg mx-auto space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-blue-50 dark:bg-slate-800 text-blue-600 flex items-center justify-center mx-auto shadow-2xs">
              <FileWarning size={32} />
            </div>
            <div className="space-y-1">
              <h4 className="text-base font-black text-slate-900 dark:text-white">
                No Active Complaints or Enquiries
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Records will appear here when you scan a packaged commodity and escalate detected non-compliances, or when a manual docket is filed.
              </p>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to={isCitizen ? "/citizen/scan" : "/scan"}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-full shadow-sm flex items-center gap-2 transition-all cursor-pointer"
              >
                <Sparkles size={14} className="text-amber-400" />
                <span>{isCitizen ? "Scan Product" : "Start Inspection & Scan Product"}</span>
              </Link>

              <button
                type="button"
                onClick={() => setIsNewModalOpen(true)}
                className="px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-full transition-all cursor-pointer"
              >
                + File Manual Docket
              </button>
            </div>
          </div>
        ) : viewMode === 'cards' ? (
          /* ── Premium Soft Minimalist Card View (Matching Reference Design) ── */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredComplaints.map((c) => {
              const st = STATUS_CONFIG[c.currentStatus] || STATUS_CONFIG.Submitted;
              const hasViolations = c.findings.length > 0;
              const ruleCodes = c.findings.map((f) => f.ruleCode || 'Rule 6(1)').join(' and ');

              return (
                <div
                  key={c.id}
                  className="theme-card p-6 flex flex-col justify-between space-y-4 hover:border-slate-300 dark:hover:border-slate-600 transition-all shadow-xs"
                >
                  <div className="space-y-3">
                    {/* Top Header: Black ID Pill, Ref #, and Status Capsule */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-black text-xs bg-slate-900 dark:bg-slate-950 text-amber-400 px-3 py-1 rounded-full shadow-2xs border border-slate-800">
                          {c.id}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400 font-bold">
                          Ref: {c.inspectionId || 'INS-1'}
                        </span>
                      </div>

                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] uppercase font-black tracking-wider border shadow-2xs ${st.badgeClass}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${st.dotColor}`} />
                        <span>{st.label}</span>
                      </span>
                    </div>

                    {/* Product Name & Details */}
                    <div>
                      <h3 className="text-base sm:text-lg font-black text-slate-900 dark:text-white leading-snug">
                        {c.product.productName}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                        Manufacturer: <span className="font-bold text-slate-700 dark:text-slate-300">{c.product.manufacturerName || c.product.brand || 'PARLE PRODUCTS PVT LTD'}</span> • MRP: <span className="font-bold text-slate-700 dark:text-slate-300">₹ {c.product.mrp || '--'}</span>
                      </p>
                    </div>

                    {/* Official Verification Box */}
                    <div className="p-4 rounded-2xl bg-blue-50/50 dark:bg-slate-800/70 border border-blue-100 dark:border-slate-700/80 space-y-2">
                      <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        <ShieldCheck size={13} className="text-blue-600 dark:text-blue-400" />
                        <span>OFFICIAL VERIFICATION:</span>
                      </div>
                      <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                        {hasViolations
                          ? `Packaging audit confirms violation under ${ruleCodes} of Legal Metrology (Packaged Commodities) Rules 2011.`
                          : 'Packaging audit verified and logged in statutory central database.'}
                      </p>
                      <div className="flex items-start gap-1.5 pt-1 text-xs text-emerald-800 dark:text-emerald-300 font-bold">
                        <Zap size={13} className="text-amber-500 flex-shrink-0 mt-0.5" />
                        <span>
                          Action: {c.verification?.actionTaken || 'Formal Statutory Notice issued to distributor and manufacturer under Section 18 / 36.'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Action Pill Buttons (Matching Design Reference) */}
                  <div className="pt-2 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => generateComplaintAssessmentPDF(c)}
                      className="flex-1 py-3 px-4 bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white text-xs font-black rounded-2xl shadow-sm flex items-center justify-center gap-2 transition-all active:scale-[0.98] cursor-pointer"
                    >
                      <Download size={14} />
                      <span>Assessment PDF</span>
                    </button>

                    <Link
                      to={`/complaints/${c.id}`}
                      className="flex-1 py-3 px-4 bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 text-xs font-black rounded-2xl border border-blue-200 dark:border-blue-800 shadow-2xs flex items-center justify-center gap-1.5 transition-all active:scale-[0.98]"
                    >
                      <Eye size={14} />
                      <span>Full Dossier</span>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* ── Table View ── */
          <div className="theme-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-500 font-bold bg-slate-50/80 dark:bg-slate-800/80">
                    <th className="p-3.5">Complaint ID</th>
                    <th className="p-3.5">Product & Brand</th>
                    <th className="p-3.5">Date & Jurisdiction</th>
                    <th className="p-3.5">Submitted By</th>
                    <th className="p-3.5">Current Status</th>
                    <th className="p-3.5">Priority</th>
                    <th className="p-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredComplaints.map((c) => {
                    const st = STATUS_CONFIG[c.currentStatus] || STATUS_CONFIG.Submitted;
                    return (
                      <tr key={c.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/50 transition-colors">
                        <td className="p-3.5 font-mono font-black text-slate-900 dark:text-white">
                          <Link to={`/complaints/${c.id}`} className="text-blue-600 hover:underline">
                            {c.id}
                          </Link>
                        </td>
                        <td className="p-3.5">
                          <span className="font-bold text-slate-900 dark:text-white block max-w-xs truncate">{c.product.productName}</span>
                          <span className="text-[10px] text-slate-400 font-mono">Ref: {c.inspectionId}</span>
                        </td>
                        <td className="p-3.5 text-slate-600 dark:text-slate-300">
                          {new Date(c.dateSubmitted).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                        </td>
                        <td className="p-3.5 text-slate-700 dark:text-slate-300">{c.submittedBy}</td>
                        <td className="p-3.5">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] border font-bold ${st.badgeClass}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${st.dotColor}`} />
                            <span>{st.label}</span>
                          </span>
                        </td>
                        <td className="p-3.5 font-black uppercase text-[10px] text-slate-700 dark:text-slate-300">{c.priority}</td>
                        <td className="p-3.5 text-right space-x-2">
                          <button
                            type="button"
                            onClick={() => generateComplaintAssessmentPDF(c)}
                            className="px-2.5 py-1 bg-slate-900 text-white rounded-lg text-xs font-bold inline-flex items-center gap-1"
                            title="Download Certified PDF"
                          >
                            <Download size={12} />
                            <span>PDF</span>
                          </button>
                          <Link
                            to={`/complaints/${c.id}`}
                            className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-bold inline-flex items-center gap-1"
                          >
                            <Eye size={12} />
                            <span>Dossier</span>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* New Complaint Modal */}
      {isNewModalOpen && (
        <NewComplaintModal
          isOpen={isNewModalOpen}
          onClose={() => setIsNewModalOpen(false)}
          onSubmit={handleCreateComplaint}
        />
      )}
    </div>
  );
}
