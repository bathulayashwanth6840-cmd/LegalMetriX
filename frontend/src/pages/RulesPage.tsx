import { useState } from 'react';
import { Search, ChevronDown, ChevronUp, AlertCircle, CheckSquare, ArrowRight, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useRole } from '../context/RoleContext';

interface RuleItem {
  id: number;
  ruleCode: string;
  title: string;
  category: string;
  explanation: string;
  verificationGuidelines: string[];
  violationExamples: string[];
  checkCriteria: string;
}

const SAMPLE_RULES: RuleItem[] = [
  {
    id: 1,
    ruleCode: "Rule 6(1)(a)",
    title: "Common Name of the Commodity",
    category: "Mandatory Declarations",
    explanation: "Every package must declare the common or generic name of the commodity contained in the package.",
    verificationGuidelines: [
      "Verify that the name is prominent and clearly visible on the principal display panel.",
      "Check if generic words like 'Food Product' are qualified by the actual common name (e.g., 'Potato Chips')."
    ],
    violationExamples: [
      "Name printed in extremely small font on the side flap.",
      "Vague representation that doesn't name the actual commodity."
    ],
    checkCriteria: "Name must be in Hindi or English, easily readable, and occupy a prominent position on the principal display area."
  },
  {
    id: 2,
    ruleCode: "Rule 6(1)(b)",
    title: "Net Quantity Declaration",
    category: "Package/Net Quantity",
    explanation: "The net quantity in terms of standard unit of weight or measure or number must be declared on every package.",
    verificationGuidelines: [
      "Verify the net quantity matches standard units (g, kg, ml, L, or units/pcs).",
      "Check if symbols are correct (use 'g' instead of 'gms', 'ml' instead of 'm.l.').",
      "Ensure no qualifying words like 'approximate' or 'when packed' are used."
    ],
    violationExamples: [
      "Using non-standard units (e.g. '1 Kilo' or '10 Gms').",
      "Qualifying statements like 'Net weight when packed: 500g'."
    ],
    checkCriteria: "Must use standard SI symbols only. No trailing abbreviations or qualifying text allowed."
  },
  {
    id: 3,
    ruleCode: "Rule 6(1)(da)",
    title: "Maximum Retail Price (MRP)",
    category: "MRP Declaration",
    explanation: "The maximum retail price inclusive of all taxes must be clearly declared on the package.",
    verificationGuidelines: [
      "Ensure the MRP is printed as 'MRP Rs. XX.XX incl. of all taxes' or similar clear wording.",
      "Verify the price digits are clear and not overwritten or stickered over."
    ],
    violationExamples: [
      "Sticker pasted over original MRP increasing the price.",
      "Absence of 'inclusive of all taxes' phrase."
    ],
    checkCriteria: "Must include currency symbol/name and clear indication that all statutory taxes are included."
  },
  {
    id: 4,
    ruleCode: "Rule 6(1)(c)",
    title: "Name & Address of Manufacturer / Packer",
    category: "Manufacturer/Importer Details",
    explanation: "The name and complete address of the manufacturer or packer must be clearly declared.",
    verificationGuidelines: [
      "Verify complete address including premises number, street, city, state, and pin code.",
      "If imported, verify name and address of the importer as well as country of origin."
    ],
    violationExamples: [
      "Only city name provided without postal address or PIN code.",
      "Missing importer identification on foreign goods."
    ],
    checkCriteria: "Complete physical address enabling physical inspection and consumer correspondence."
  },
  {
    id: 5,
    ruleCode: "Rule 6(1)(d)",
    title: "Month & Year of Manufacture / Packaging",
    category: "Date/Month/Year Information",
    explanation: "Month and year in which the commodity is manufactured or pre-packed must be clearly indicated.",
    verificationGuidelines: [
      "Check for 'Mfg Date:', 'Packed on:', or 'Date of Pkg:'.",
      "Ensure format is valid (e.g. MM/YYYY, Month YYYY)."
    ],
    violationExamples: [
      "Missing manufacture month/year on perishable commodities.",
      "Illegible smudged date stamps."
    ],
    checkCriteria: "Clear month and year declaration with conspicuous font on the package."
  },
  {
    id: 6,
    ruleCode: "Rule 6(1)(g)",
    title: "Consumer Care Helpline & Email",
    category: "Consumer Care Details",
    explanation: "Name, address, telephone number, and email of the person or office to be contacted in case of consumer complaints.",
    verificationGuidelines: [
      "Verify presence of toll-free number or helpline.",
      "Ensure valid email address is clearly visible."
    ],
    violationExamples: [
      "No email or phone number listed for grievances.",
      "Invalid or non-functional telephone helpline."
    ],
    checkCriteria: "Designated consumer complaint channel with phone/email and contact person/office designation."
  }
];

const CATEGORIES = [
  "All",
  "Mandatory Declarations",
  "Package/Net Quantity",
  "MRP Declaration",
  "Manufacturer/Importer Details",
  "Consumer Care Details",
  "Date/Month/Year Information"
];

export default function RulesPage() {
  const { isCitizen } = useRole();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isChecklistOpen, setIsChecklistOpen] = useState(true);
  
  const navigate = useNavigate();

  // Search and Filter logic
  const filteredRules = SAMPLE_RULES.filter(rule => {
    const matchesSearch = rule.ruleCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          rule.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          rule.explanation.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = selectedCategory === 'All' || rule.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="p-4 sm:p-8 pb-24 max-w-5xl mx-auto flex flex-col gap-6 select-none bg-[#F6F8FA] dark:bg-[#090E1A] min-h-full transition-colors">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <span>📖</span>
            <span>Rules & Guidelines</span>
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm font-medium">
            Reference handbook for Legal Metrology (Packaged Commodities) Rules, 2011
          </p>
        </div>
      </div>

      {/* Official Status Warning Banner */}
      <div className="theme-card p-4 bg-amber-50/70 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60 flex items-start gap-3">
        <ShieldAlert className="text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" size={20} />
        <div>
          <h4 className="font-bold text-amber-900 dark:text-amber-300 text-xs sm:text-sm">Sample / Reference Content Only</h4>
          <p className="text-amber-800 dark:text-amber-400 text-xs mt-0.5 leading-relaxed font-medium">
            The rules and sections displayed below represent the Legal Metrology statutory framework. Verify with the official gazette before issuing formal statutory notices.
          </p>
        </div>
      </div>

      {/* Quick Reference Checklist */}
      <div className="theme-card overflow-hidden">
        <button 
          onClick={() => setIsChecklistOpen(!isChecklistOpen)}
          className="w-full px-5 py-4 bg-slate-50/80 dark:bg-slate-800/80 flex items-center justify-between border-b border-slate-100 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2 font-bold text-slate-900 dark:text-white text-xs sm:text-sm">
            <CheckSquare className="text-blue-600 dark:text-blue-400" size={18} />
            <span>Field Inspection Checklist (Standard Declarations)</span>
          </div>
          {isChecklistOpen ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
        </button>
        
        {isChecklistOpen && (
          <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-[10px]">1</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">Common or generic commodity name</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-[10px]">2</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">Net quantity in standard SI units</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-[10px]">3</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">MRP with tax inclusion statement</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold text-[10px]">4</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">Complete name and physical address</span>
            </div>
          </div>
        )}
      </div>

      {/* Search & Categories */}
      <div className="theme-card p-4 space-y-3">
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search rules by code, title, or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 text-xs bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
          />
        </div>

        {/* Categories Bar */}
        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === cat 
                  ? 'bg-blue-600 text-white shadow-2xs' 
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Rule Cards Grid */}
      <div className="flex flex-col gap-4">
        {filteredRules.map(rule => (
          <div 
            key={rule.id}
            className="theme-card overflow-hidden flex flex-col hover:border-slate-300 dark:hover:border-slate-700 transition-all shadow-xs"
          >
            {/* Title Block */}
            <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <div>
                <span className="inline-block px-2.5 py-0.5 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-full text-[10px] font-black uppercase tracking-wide">
                  {rule.ruleCode}
                </span>
                <h3 className="font-bold text-slate-900 dark:text-white text-base mt-1">{rule.title}</h3>
              </div>
              <span className="text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold px-2.5 py-1 rounded-full">
                {rule.category}
              </span>
            </div>

            {/* Content Details */}
            <div className="p-5 flex flex-col gap-4">
              <div>
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Rule Explanation</h4>
                <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 mt-1 leading-relaxed font-medium">{rule.explanation}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Guidelines */}
                <div className="bg-blue-50/50 dark:bg-slate-800/60 p-4 rounded-2xl border border-blue-100 dark:border-slate-700">
                  <h4 className="text-xs font-bold text-blue-800 dark:text-blue-300 uppercase tracking-wider flex items-center gap-1.5">
                    🔍 Field Verification Guidelines
                  </h4>
                  <ul className="list-disc pl-4 mt-2 text-xs text-slate-600 dark:text-slate-400 flex flex-col gap-1.5">
                    {rule.verificationGuidelines.map((guideline, idx) => (
                      <li key={idx}>{guideline}</li>
                    ))}
                  </ul>
                </div>

                {/* Common Violations */}
                <div className="bg-rose-50/40 dark:bg-rose-950/30 p-4 rounded-2xl border border-rose-100 dark:border-rose-900/40">
                  <h4 className="text-xs font-bold text-rose-800 dark:text-rose-300 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertCircle size={14} /> Common Violations
                  </h4>
                  <ul className="list-disc pl-4 mt-2 text-xs text-rose-700 dark:text-rose-400 flex flex-col gap-1.5">
                    {rule.violationExamples.map((violation, idx) => (
                      <li key={idx}>{violation}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Compliance Status Checks */}
              <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Compliance Criteria</h4>
                <p className="text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-3 py-2 rounded-xl mt-1">
                  {rule.checkCriteria}
                </p>
              </div>
            </div>

            {/* Inspection / Citizen Scan Trigger Button */}
            <div className="px-5 py-3.5 bg-slate-50/50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => navigate(isCitizen ? '/citizen/scan' : '/scan')}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-5 rounded-full text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
              >
                <span>{isCitizen ? 'Scan Product with This Rule' : 'Use During Inspection'}</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        ))}

        {filteredRules.length === 0 && (
          <div className="text-center py-10 theme-card text-slate-400 text-xs">
            No rules found matching your filters.
          </div>
        )}
      </div>

    </div>
  );
}
