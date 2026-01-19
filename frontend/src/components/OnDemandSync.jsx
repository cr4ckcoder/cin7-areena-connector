import React, { useState } from 'react';
import { syncOnDemand } from '../api';

const OnDemandSync = () => {
    const [itemNumber, setItemNumber] = useState('');
    const [dryRun, setDryRun] = useState(true);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleOnDemandSync = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);
        try {
            const data = await syncOnDemand(itemNumber, dryRun);
            setResult(data);
        } catch (err) {
            setResult({ status: 'error', message: err.response?.data?.detail || err.message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <div className="card-title">
                <span>On-Demand Item Sync</span>
                {result && (
                    <span className={`status-badge ${result.status.includes('success') ? 'success' : 'error'}`}>
                        {result.status}
                    </span>
                )}
            </div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Fetch a specific item from Arena, prepare the Cin7 payload, and optionally push it live.
            </p>
            
            <form onSubmit={handleOnDemandSync} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                    <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                        <label>Arena Item Number</label>
                        <input 
                            type="text" 
                            value={itemNumber} 
                            onChange={(e) => setItemNumber(e.target.value)} 
                            placeholder="e.g. 06-04856" 
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading || !itemNumber}>
                        {loading ? 'Processing...' : (dryRun ? 'Preview JSON' : 'Sync to Cin7')}
                    </button>
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input 
                        type="checkbox" 
                        checked={dryRun} 
                        onChange={(e) => setDryRun(e.target.checked)} 
                        style={{ width: 'auto' }}
                    />
                    Dry Run (Mock API call and show JSON only)
                </label>
            </form>

            {result && (
                <div style={{ marginTop: '1.5rem' }}>
                    <label>Results / Payload</label>
                    <div className="log-container" style={{ maxHeight: '400px' }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
};

export default OnDemandSync;