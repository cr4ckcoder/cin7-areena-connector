import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Settings, Wrench, FileText, Menu, X } from 'lucide-react';
import { useState } from 'react';

const Layout = ({ children }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Configuration', href: '/settings', icon: Settings },
    { name: 'Tools', href: '/tools', icon: Wrench },
    { name: 'Logs', href: '/logs', icon: FileText },
  ];

  const handleMobileClick = () => setIsMobileOpen(false);

  return (
    <div className="flex h-screen bg-slate-50 w-full overflow-hidden">
      {/* Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-slate-900 text-white shadow-xl">
        <div className="p-6 border-b border-slate-700">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Cin7-Arena
          </h1>
          <p className="text-xs text-slate-400 mt-1">Connector Admin</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md translation-x-1'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center text-xs text-slate-500">
             <div className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></div>
             System Online
          </div>
        </div>
      </aside>

      {/* Mobile Header & Sidebar */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setIsMobileOpen(false)}></div>
          <div className="relative flex-col flex w-64 max-w-xs bg-slate-900 h-full text-white shadow-2xl transform transition-transform">
             <div className="p-6 flex justify-between items-center border-b border-slate-700">
                <span className="font-bold text-lg">Menu</span>
                <button onClick={() => setIsMobileOpen(false)} className="text-slate-400 hover:text-white">
                  <X size={24} />
                </button>
             </div>
             <nav className="flex-1 p-4 space-y-2">
               {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={handleMobileClick}
                  className={({ isActive }) =>
                    `flex items-center px-4 py-3 text-sm font-medium rounded-lg ${
                      isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                    }`
                  }
                >
                  <item.icon className="h-5 w-5 mr-3" />
                  {item.name}
                </NavLink>
               ))}
             </nav>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden bg-white border-b border-slate-200 p-4 flex items-center shadow-sm">
             <button onClick={() => setIsMobileOpen(true)} className="text-slate-600 mr-4">
               <Menu size={24} />
             </button>
             <span className="font-bold text-slate-800">Cin7-Arena Connector</span>
        </div>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-auto p-4 md:p-8">
           <div className="max-w-7xl mx-auto w-full">
             {children}
           </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
