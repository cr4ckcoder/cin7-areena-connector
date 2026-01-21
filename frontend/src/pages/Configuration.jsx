import React, { useState } from 'react';
import ConfigurationForm from '../components/ConfigurationForm';
import SyncRulesManager from '../components/SyncRulesManager';
import { Settings, ShieldCheck } from 'lucide-react';

const Configuration = () => {
  const [activeTab, setActiveTab] = useState('connections');

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
           <h2 className="text-2xl font-bold text-slate-800">System Configuration</h2>
           <p className="text-slate-500">Manage API connections and synchronization rules.</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
         <div className="flex border-b border-slate-200 overflow-x-auto">
            <button
               onClick={() => setActiveTab('connections')}
               className={`flex items-center px-6 py-4 font-medium text-sm transition-colors whitespace-nowrap ${
                 activeTab === 'connections' 
                 ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50/50' 
                 : 'text-slate-600 hover:bg-slate-50'
               }`}
            >
              <Settings className="w-4 h-4 mr-2" />
              API Connections
            </button>
            <button
               onClick={() => setActiveTab('rules')}
               className={`flex items-center px-6 py-4 font-medium text-sm transition-colors whitespace-nowrap ${
                 activeTab === 'rules' 
                 ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50/50' 
                 : 'text-slate-600 hover:bg-slate-50'
               }`}
            >
              <ShieldCheck className="w-4 h-4 mr-2" />
              Sync Rules
            </button>
         </div>
         
         <div className="p-6">
            {activeTab === 'connections' && (
               <div className="max-w-4xl">
                  <ConfigurationForm />
               </div>
            )}
            
            {activeTab === 'rules' && (
               <div>
                  <SyncRulesManager />
               </div>
            )}
         </div>
      </div>
    </div>
  );
};

export default Configuration;
