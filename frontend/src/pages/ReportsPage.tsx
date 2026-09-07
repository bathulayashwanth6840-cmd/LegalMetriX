import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, Download, Search, Eye, Sparkles, RefreshCw,
  FileWarning, ShieldCheck, Zap
} from 'lucide-react';
import { getStoredComplaints } from '../services/complaintService';
import type { ComplaintRecord } from '../types/complaint';
import { evaluateCanonicalCompliance } from '../utils/complianceEngine';
import { generateComplaintAssessmentPDF, generateInspectionReportPDF } from '../utils/pdfGenerator';

export default function ReportsPage() {
  const [scans, setScans] = useState<any[]>([]);
  const [complaints, setComplaints] = useState<ComplaintRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'ALL' | 'COMPLAINTS' | 'INSPECTIONS'>('ALL');
  const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '');

  useEffect(() => {
    fetchRecords();
  }, [apiUrl]);

  const fetchRecords = () => {
    setLoading(true);
    fetch(`${apiUrl}/api/scans/`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setScans(data);
        }
      })
      .catch((err) => console.warn('Reports fetch error:', err))
      .finally(() => setLoading(false));

    const stored = getStoredComplaints();
    setComplaints(stored);
  };

  const filteredScans = scans.filter((s) => {
    const prodName = (s.extracted_fields?.product_name || s.extracted_fields?.brand_name || 'Packaged Commodity').toLowerCase();
    return prodName.includes(searchQuery.toLowerCase()) || String(s.id).includes(searchQuery);
  });

  const filteredComplaints = complaints.filter((c) => {
    const q = searchQuery.toLowerCase();
    return (
      c.id.toLowerCase().includes(q) ||
      c.product.productName.toLowerCase().includes(q) ||
      c.inspectionId.toLowerCase().includes(q) ||
      c.location.toLowerCase().includes(q)
    );
  });

  const handleDownloadComplaintPDF = (c: ComplaintRecord) => {
    generateComplaintAssessmentPDF(c);
  };

  const handleDownloadScanPDF = async (scan: any) => {
    if (scan) {
      generateInspectionReportPDF(scan);
      return;
    }
  };

  return (
    <div className="flex flex-col min-h-full pb-24 sm:pb-12 bg-[#F6F8FA] dark:bg-[#090E1A] transition-colors">
      {/* ── Top Header Banner ────────────────────────────────────────────── */}
      <div className="bg-slate-900 dark:bg-slate-950 text-white pt-8 pb-10 px-4 sm:px-8 border-b border-slate-800/80 shadow-2xs">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 bg-blue-950/80 border border-blue-500/40 px-3 py-1 rounded-full text-[10px] font-black tracking-widest text-blue-300 uppercase mb-3">
                <FileText size={12} className="text-amber-400" />
                <span>STATUTORY AUDIT & ENFORCEMENT DOSSIERS</span>
              </div>
              <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
                Inspection & Assessment Reports
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 dark:text-slate-400 mt-2 max-w-2xl leading-relaxed font-medium">
                Official statutory assessment reports, declaration non-conformance records, verification dossiers, and certified PDF downloads under Legal Metrology Rules, 2011.
              </p>
            </div>

            <button
              type="button"
              onClick={fetchRecords}
              className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white rounded-full text-xs font-bold flex items-center gap-2 border border-white/20 transition-all self-start sm:self-auto cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Records
            </button>
          </div>
        </div>
      </div>

      {/* ── Main Body ────────────────────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-8 -mt-4 space-y-6 w-full">

        {/* Search & Tabs Toolbar */}
        <div className="theme-card p-4 flex flex-col md:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Product Name, Complaint ID, or Inspection ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 text-xs bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 w-full md:w-auto">
            <button
              type="button"
              onClick={() => setActiveTab('ALL')}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'ALL'
                  ? 'bg-blue-600 text-white shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              All Reports ({filteredComplaints.length + filteredScans.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('COMPLAINTS')}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'COMPLAINTS'
                  ? 'bg-blue-600 text-white shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              Complaints ({filteredComplaints.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('INSPECTIONS')}
              className={`px-4 py-2 rounded-full text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === 'INSPECTIONS'
                  ? 'bg-blue-600 text-white shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              Inspections ({filteredScans.length})
            </button>
          </div>
        </div>

        {/* ── Statutory Complaints & Enquiry Reports ──────────────────────── */}
        {(activeTab === 'ALL' || activeTab === 'COMPLAINTS') && filteredComplaints.length > 0 && (
          <div className="space-y-4">
            <h3 className="font-black text-slate-900 dark:text-white text-base flex items-center gap-2">
              <span className="p-1 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200 text-amber-600">
                <FileWarning size={16} />
              </span>
              <span>Statutory Complaint & Enquiry Assessment Dockets ({filteredComplaints.length})</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredComplaints.map((c) => (
                <div
                  key={c.id}
                  className="theme-card p-6 flex flex-col justify-between space-y-4 hover:border-slate-300 dark:hover:border-slate-600 transition-all shadow-xs"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-black text-xs bg-slate-900 dark:bg-slate-950 text-amber-400 px-3 py-1 rounded-full border border-slate-800">
                          {c.id}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400 font-bold">
                          Ref: {c.inspectionId || 'INS-1'}
                        </span>
                      </div>
                      <span className="text-[10px] font-black uppercase px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-900 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                        {c.currentStatus}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-black text-slate-900 dark:text-white text-base">{c.product.productName}</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Manufacturer: <span className="font-bold text-slate-700 dark:text-slate-300">{c.product.manufacturerName || c.product.brand || 'PARLE PRODUCTS PVT LTD'}</span> • MRP: <span className="font-bold text-slate-700 dark:text-slate-300">₹ {c.product.mrp || '--'}</span>
                      </p>
                    </div>

                    <div className="p-3.5 bg-blue-50/50 dark:bg-slate-800/70 rounded-2xl border border-blue-100 dark:border-slate-700/80 text-xs space-y-1">
                      <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-slate-500 dark:text-slate-400">
                        <ShieldCheck size={13} className="text-blue-600 dark:text-blue-400" />
                        <span>Official Verification:</span>
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 text-xs font-medium leading-relaxed">
                        {c.findings?.length > 0
                          ? `Packaging audit confirms statutory violation under Rule 6(1)(e) / Rule 12.`
                          : 'Packaging audit verified and filed under statutory registry.'}
                      </p>
                      <div className="flex items-center gap-1.5 text-xs text-emerald-800 dark:text-emerald-300 font-bold pt-0.5">
                        <Zap size={13} className="text-amber-500" />
                        <span>Action: {c.verification?.actionTaken || 'Formal Notice issued under Section 18 / 36.'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleDownloadComplaintPDF(c)}
                      className="flex-1 py-3 px-4 bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white rounded-2xl text-xs font-black flex items-center justify-center gap-1.5 shadow-2xs transition-all active:scale-[0.98] cursor-pointer"
                      title="Download Certified Assessment PDF"
                    >
                      <Download size={14} /> <span>Assessment PDF</span>
                    </button>
                    <Link
                      to={`/complaints/${c.id}`}
                      className="flex-1 py-3 px-4 bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/60 text-blue-700 dark:text-blue-300 rounded-2xl text-xs font-black flex items-center justify-center gap-1.5 border border-blue-200 dark:border-blue-800 transition-all text-center active:scale-[0.98]"
                    >
                      <Eye size={14} /> <span>Full Dossier</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Field Inspections List ──────────────────────────────────────── */}
        {(activeTab === 'ALL' || activeTab === 'INSPECTIONS') && (
          <div className="space-y-4 pt-2">
            <h3 className="font-black text-slate-900 dark:text-white text-base flex items-center gap-2">
              <span className="p-1 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200 text-blue-600">
                <FileText size={16} />
              </span>
              <span>Enforcement Inspection Summary Reports ({filteredScans.length})</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredScans.length === 0 ? (
                <div className="col-span-full py-12 text-center theme-card p-8 space-y-3">
                  <FileText size={36} className="text-slate-300 mx-auto" />
                  <h4 className="font-bold text-slate-700 dark:text-slate-300 text-sm">No Inspection Records Found</h4>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Capture new commodity packaging scans to automatically generate certified PDF inspection dossiers.
                  </p>
                  <Link
                    to="/scan"
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full text-xs font-bold inline-flex items-center gap-1.5 shadow-sm transition-all"
                  >
                    <Sparkles size={14} /> Start New Inspection
                  </Link>
                </div>
              ) : (
                filteredScans.map((s) => {
                  const prodName = s.extracted_fields?.product_name || s.extracted_fields?.brand_name || 'Packaged Commodity Sample';
                  const canonical = evaluateCanonicalCompliance({ serverScan: s });

                  return (
                    <div
                      key={s.id}
                      className="theme-card p-5 flex flex-col justify-between space-y-4 hover:border-slate-300 dark:hover:border-slate-600 transition-all shadow-xs"
                    >
                      <div className="space-y-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono font-black text-xs text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
                            #{s.id}
                          </span>
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase border ${canonical.textBadgeClass}`}>
                            {canonical.status === 'COMPLIANT' ? '✅ Compliant' : canonical.status === 'NON-COMPLIANT' ? '❌ Non-Compliant' : '⚠️ Needs Review'}
                          </span>
                        </div>

                        <div>
                          <h4 className="font-black text-slate-900 dark:text-white text-sm leading-snug">{prodName}</h4>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                            MRP: {s.extracted_fields?.mrp || '₹--'} • Qty: {s.extracted_fields?.net_quantity || '--'}
                          </p>
                        </div>

                        <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-700 text-xs flex items-center justify-between">
                          <span className="text-[10px] uppercase font-bold text-slate-400">Score</span>
                          <span className="font-black text-slate-900 dark:text-white">{canonical.score}/100</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                        <button
                          type="button"
                          onClick={() => handleDownloadScanPDF(s)}
                          className="py-2.5 px-3 bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                        >
                          <Download size={13} /> <span>PDF</span>
                        </button>
                        <Link
                          to={`/scan/${s.id}`}
                          className="py-2.5 px-3 bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all text-center"
                        >
                          <Eye size={13} /> <span>Dossier</span>
                        </Link>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
