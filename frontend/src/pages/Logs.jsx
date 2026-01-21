import React from 'react';
import { getLogs } from '../api';
import { FileText, AlertCircle, CheckCircle } from 'lucide-react';

const Logs = () => {
  const [logLines, setLogLines] = React.useState([]);

  const fetchLogs = async () => {
      try {
          const data = await getLogs();
          setLogLines(data.logs || []);
      } catch (e) {
          console.error("Failed to fetch logs", e);
      }
  };

  React.useEffect(() => {
      fetchLogs();
      const interval = setInterval(fetchLogs, 5000); // Poll every 5s
      return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
         <div>
           <h2 className="text-2xl font-bold text-slate-800">System Logs</h2>
           <p className="text-slate-500">View recent system activity and synchronization history.</p>
         </div>
         <button 
           onClick={fetchLogs}
           className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50">
            Refresh Logs
         </button>
      </div>

      <div className="bg-slate-900 rounded-xl shadow-lg border border-slate-700 overflow-hidden">
         <div className="p-4 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
            <span className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Terminal Output (Last 100 Lines)</span>
            <div className="flex space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
            </div>
         </div>
         <div className="p-4 font-mono text-xs h-[500px] overflow-y-auto text-slate-300 whitespace-pre-wrap">
            {logLines.length > 0 ? (
                logLines.map((line, i) => (
                    <div key={i} className="hover:bg-slate-800 px-1 rounded">{line}</div>
                ))
            ) : (
                <div className="text-slate-600 italic">No logs available or waiting for server...</div>
            )}
         </div>
      </div>
    </div>
  );
};

export default Logs;
