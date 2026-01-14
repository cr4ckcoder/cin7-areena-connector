import React, { useState, useEffect } from 'react';
import { getSettings, saveSettings, triggerSync } from '../api';

const ConfigurationForm = () => {
  const [settings, setSettings] = useState({
    arena_workspace_id: '',
    arena_email: '',
    arena_password: '',
    cin7_api_user: '',
    cin7_api_key: '',
    auto_sync_enabled: false
  });
  const [loading, setLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      console.error("Failed to fetch settings", err);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      await saveSettings(settings);
      setMessage({ type: 'success', text: 'Settings saved successfully' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncLoading(true);
    setSyncResult(null);
    try {
      const result = await triggerSync();
      setSyncResult(result);
    } catch (err) {
        setSyncResult({ status: 'error', message: 'Sync failed to start', errors: [err.message] });
    } finally {
      setSyncLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-title">
          <span>Connection Settings</span>
          {message && (
             <span className={`status-badge ${message.type === 'success' ? 'success' : 'error'}`}>
               {message.text}
             </span>
          )}
        </div>
        <form onSubmit={handleSave}>
          <div className="grid-cols-2">
            <div>
              <h3 style={{fontSize: '0.875rem', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.05em', marginBottom: '1rem'}}>Arena PLM</h3>
              <div className="form-group">
                <label>Workspace ID</label>
                <input type="text" name="arena_workspace_id" value={settings.arena_workspace_id} onChange={handleChange} placeholder="e.g. 123456" />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" name="arena_email" value={settings.arena_email} onChange={handleChange} placeholder="user@example.com" />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input type="password" name="arena_password" value={settings.arena_password} onChange={handleChange} placeholder="••••••••" />
              </div>
            </div>

            <div>
              <h3 style={{fontSize: '0.875rem', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.05em', marginBottom: '1rem'}}>Cin7 Omni</h3>
              <div className="form-group">
                <label>API User</label>
                <input type="text" name="cin7_api_user" value={settings.cin7_api_user} onChange={handleChange} placeholder="Cin7 API User" />
              </div>
              <div className="form-group">
                <label>API Key</label>
                <input type="password" name="cin7_api_key" value={settings.cin7_api_key} onChange={handleChange} placeholder="••••••••" />
              </div>
            </div>
          </div>

          <div style={{borderTop: '1px solid var(--border)', paddingTop: '1.5rem', marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
             <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0, cursor: 'pointer'}}>
                <input type="checkbox" name="auto_sync_enabled" checked={settings.auto_sync_enabled} onChange={handleChange} style={{width: 'auto'}} />
                Enable Auto Sync (Background Polling)
             </label>
             <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                    <>Saving...</>
                ) : (
                    <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                        Save Configuration
                    </>
                )}
             </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-title">
            <span>Manual Operations</span>
            {syncResult && (
                <span className={`status-badge ${syncResult.status === 'success' ? 'success' : 'error'}`}>
                    {syncResult.status === 'success' ? 'Sync Completed' : 'Sync Failed'}
                </span>
            )}
        </div>
        
        <div style={{display: 'flex', alignItems: 'flex-start', gap: '2rem'}}>
            <div style={{flex: 1}}>
                <p style={{marginTop: 0, color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>
                    Triggering a manual sync will immediately check for "Completed" changes in Arena PLM and push them to Cin7.
                </p>
                <button onClick={handleSync} className="btn btn-primary" disabled={syncLoading} style={{width: '100%'}}>
                    {syncLoading ? 'Syncing...' : 'Trigger Sync Now'}
                </button>
            </div>
            
            <div style={{flex: 2}}>
                <label>Activity Log</label>
                <div className="log-container">
                    {!syncResult && !syncLoading && <div className="log-item" style={{color: '#64748B'}}>No recent activity.</div>}
                    {syncLoading && <div className="log-item">Starting sync process...</div>}
                    {syncResult && (
                        <>
                            <div className="log-item success">Result: {syncResult.message}</div>
                            <div className="log-item">Processed Items: {syncResult.processed_items}</div>
                            {syncResult.errors && syncResult.errors.length > 0 ? (
                                syncResult.errors.map((err, idx) => (
                                    <div key={idx} className="log-item error">Error: {err}</div>
                                ))
                            ) : (
                                <div className="log-item success">No errors encountered.</div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationForm;
