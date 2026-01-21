import React from 'react';
import { X, CheckCircle, AlertTriangle, FileJson } from 'lucide-react';

const SyncResultModal = ({ result, onClose, title }) => {
  if (!result) return null;

  const isSuccess = result.status === 'success' || result.status === 'complete' || result.status === 'mock_success';
  const hasErrors = result.errors && result.errors.length > 0;
  const isDryRun = result.dry_run === true || result.Mode === 'DRY_RUN';

  return (
    <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className={`px-6 py-4 border-b flex items-center justify-between ${isSuccess ? 'bg-emerald-50 border-emerald-100' : 'bg-slate-50 border-slate-200'}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${isSuccess ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'}`}>
               {isSuccess ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            </div>
            <div>
               <h3 className="text-lg font-bold text-slate-800">{title} Result</h3>
               <p className="text-sm text-slate-500">
                  {isDryRun ? 'Simulation Mode (No changes made)' : 'Live Execution Mode'}
               </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-black/5 rounded-lg transition-colors text-slate-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-center">
                    <div className="text-sm text-slate-500 mb-1">Items Processed</div>
                    <div className="text-2xl font-bold text-slate-800">
                        {result.summary?.mocked || result.summary?.success || result.items_harvested || 0}
                    </div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg border border-red-100 text-center">
                    <div className="text-sm text-red-600 mb-1">Failures</div>
                    <div className="text-2xl font-bold text-red-700">
                        {result.summary?.failed || (result.errors ? result.errors.length : 0)}
                    </div>
                </div>
                 <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 text-center">
                    <div className="text-sm text-blue-600 mb-1">Status</div>
                    <div className="text-lg font-bold text-blue-700 uppercase tracking-wide">
                        {result.status}
                    </div>
                </div>
            </div>

            {/* Error List */}
            {hasErrors && (
                <div className="mb-6">
                    <h4 className="text-sm font-semibold text-red-800 mb-2 flex items-center">
                        <AlertTriangle className="w-4 h-4 mr-2" /> Error Log
                    </h4>
                    <div className="bg-red-50 rounded-lg p-3 text-sm text-red-700 border border-red-200 max-h-40 overflow-y-auto space-y-1">
                        {result.errors.map((err, idx) => (
                             <div key={idx} className="flex gap-2">
                                <span className="opacity-50 select-none">{idx + 1}.</span>
                                <span>{err}</span>
                             </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Raw JSON Toggle */}
            <details className="group">
                <summary className="flex items-center cursor-pointer text-sm font-medium text-slate-500 hover:text-blue-600 transition-colors list-none">
                    <FileJson className="w-4 h-4 mr-2" />
                    View Raw API Response
                    <span className="ml-2 text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-400 group-open:bg-blue-100 group-open:text-blue-600">JSON</span>
                </summary>
                <div className="mt-3 bg-slate-900 rounded-lg p-4 overflow-x-auto shadow-inner">
                   <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap">
                       {JSON.stringify(result, null, 2)}
                   </pre>
                </div>
            </details>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
             <button 
               onClick={onClose}
               className="px-5 py-2 bg-white border border-slate-300 shadow-sm text-slate-700 font-medium rounded-lg hover:bg-slate-100 transition-colors"
             >
                Close
             </button>
        </div>
      </div>
    </div>
  );
};

export default SyncResultModal;
