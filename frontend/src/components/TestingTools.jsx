import React, { useState } from 'react';
import { testArenaItem } from '../api';

const TestingTools = () => {
    const [guid, setGuid] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleTest = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const data = await testArenaItem(guid);
            setResult(data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <div className="card-title">
                <span>Arena Testing Tools</span>
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Enter an Arena Item GUID to fetch its raw details and BOM directly from the API.
                </p>
                <form onSubmit={handleTest} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                    <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                        <label>Item GUID</label>
                        <input 
                            type="text" 
                            value={guid} 
                            onChange={(e) => setGuid(e.target.value)} 
                            placeholder="e.g. 1234567890abcdef" 
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading || !guid}>
                        {loading ? 'Fetching...' : 'Fetch Item Data'}
                    </button>
                </form>
            </div>

            {error && <div className="log-item error">Error: {error}</div>}
            
            {result && (
                <div className="log-container" style={{ maxHeight: '400px' }}>
                    <div className="log-item success">Fetch Successful</div>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

export default TestingTools;
