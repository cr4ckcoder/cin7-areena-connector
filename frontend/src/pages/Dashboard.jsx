import React, { useState, useEffect } from 'react';
import { triggerSync, getSettings } from '../api';
import { Activity, Database, Clock, PlayCircle } from 'lucide-react';
import SyncResultModal from '../components/SyncResultModal';

const Dashboard = () => {
    const [stats, setStats] = useState({
        itemsHarvested: 0,
        lastSync: 'Never',
        autoSync: false
    });
    const [syncLoading, setSyncLoading] = useState(false);
    const [syncResult, setSyncResult] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [modalTitle, setModalTitle] = useState("");

    // Mock fetching stats for now, or use real data if available
    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
           const settings = await getSettings();
           // In a real app, we'd have a /stats endpoint. 
           // For now, we infer from settings or local storage if possible, or just show placeholders
           setStats({
               itemsHarvested: '-', // Backend doesn't provide this yet easily without a new endpoint
               lastSync:  settings.last_sync_time ? new Date(settings.last_sync_time).toLocaleString() : 'Never',
               autoSync: settings.auto_sync_enabled
           });
        } catch (e) {
            console.error("Failed to load stats", e);
        }
    };

    const handleSync = async (isDryRun = false) => {
        setSyncLoading(true);
        setSyncResult(null);
        setModalTitle(isDryRun ? "Dry Run" : "Manual Sync");
        
        try {
            const result = await triggerSync(isDryRun);
            setSyncResult(result);
            setShowModal(true); // Open Modal on completion
            loadStats(); // Reload stats after sync
        } catch (err) {
            setSyncResult({ status: 'error', message: 'Sync failed to start', errors: [err.message] });
            setShowModal(true);
        } finally {
            setSyncLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {showModal && (
                <SyncResultModal 
                    result={syncResult} 
                    title={modalTitle}
                    onClose={() => setShowModal(false)}
                />
            )}

            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div>
                   <h2 className="text-2xl font-bold text-slate-800">Dashboard</h2>
                   <p className="text-slate-500">Overview of your Cin7-Arena connector status.</p>
                </div>
                <div className="flex gap-2">
                     <button 
                      onClick={() => handleSync(true)}
                      disabled={syncLoading}
                      className="flex items-center px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg shadow-sm transition-colors text-sm font-medium"
                    >
                      <PlayCircle className="w-4 h-4 mr-2 text-slate-500" />
                      {syncLoading ? 'Testing...' : 'Test (Dry Run)'}
                    </button>
                    <button 
                      onClick={() => handleSync(false)}
                      disabled={syncLoading}
                      className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition-colors text-sm font-medium"
                    >
                      <PlayCircle className="w-4 h-4 mr-2" />
                      {syncLoading ? 'Syncing...' : 'Trigger Sync Now'}
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center">
                    <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center mr-4">
                        <Database className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Synced Items</p>
                        <h3 className="text-2xl font-bold text-slate-800">{stats.itemsHarvested}</h3>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center">
                    <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mr-4">
                        <Activity className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Auto-Sync Status</p>
                        <h3 className="text-2xl font-bold text-slate-800">
                             {stats.autoSync ? (
                                <span className="text-emerald-600">Active</span>
                             ) : (
                                <span className="text-slate-400">Inactive</span>
                             )}
                        </h3>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center">
                    <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center mr-4">
                        <Clock className="w-6 h-6 text-amber-600" />
                    </div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Last Successful Sync</p>
                        <h3 className="text-lg font-bold text-slate-800">{stats.lastSync}</h3>
                    </div>
                </div>
            </div>

            {/* Sync Status / Activity Feed */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
                        <Activity className="w-5 h-5 mr-2 text-slate-500" />
                        Live Activity
                    </h3>
                    
                    <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto text-slate-300">
                        {syncLoading ? (
                            <div className="flex items-center text-blue-400">
                                <span className="animate-spin mr-2">⟳</span> Starting sync process...
                            </div>
                        ) : (
                             <div className="text-slate-500 italic">Ready for synchronization...</div>
                        )}
                        
                        {/* We removed the inline result display in favor of the modal */}
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-lg font-bold text-slate-800 mb-4">Quick Tips</h3>
                    <ul className="space-y-3 text-sm text-slate-600">
                        <li className="flex items-start">
                           <span className="mr-2 text-blue-500">•</span>
                           Use <strong>Tools</strong> to inspect raw Arena data before syncing.
                        </li>
                        <li className="flex items-start">
                           <span className="mr-2 text-blue-500">•</span>
                           Enable <strong>Auto-Sync</strong> in Configuration to poll every 5 minutes.
                        </li>
                        <li className="flex items-start">
                           <span className="mr-2 text-blue-500">•</span>
                           Check <strong>Logs</strong> for detailed history of background jobs.
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
