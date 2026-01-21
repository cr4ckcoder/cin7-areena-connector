import React from 'react';
import TestingTools from '../components/TestingTools';
import OnDemandSync from '../components/OnDemandSync';
import { Wrench } from 'lucide-react';

const Tools = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
         <div>
           <h2 className="text-2xl font-bold text-slate-800">Operational Tools</h2>
           <p className="text-slate-500">Utilities for testing and on-demand synchronization.</p>
         </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         {/* Arena Inspector Tool */}
         <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
             <div className="flex items-center mb-4">
                 <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-4">
                     <Wrench className="w-5 h-5 text-blue-600" />
                 </div>
                 <div>
                     <h3 className="text-lg font-semibold text-slate-800">Arena Inspector</h3>
                     <p className="text-sm text-slate-500">Fetch raw item JSON from Arena</p>
                 </div>
             </div>
             <TestingTools />
         </div>

         {/* On-Demand Sync Tool */}
         <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
             <div className="flex items-center mb-4">
                 <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center mr-4">
                     <Wrench className="w-5 h-5 text-green-600" />
                 </div>
                 <div>
                     <h3 className="text-lg font-semibold text-slate-800">Single Item Sync</h3>
                     <p className="text-sm text-slate-500">Push individual items immediately</p>
                 </div>
             </div>
             <OnDemandSync />
         </div>
      </div>
    </div>
  );
};

export default Tools;
