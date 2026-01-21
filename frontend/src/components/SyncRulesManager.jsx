import React, { useState, useEffect } from 'react';
import api from '../api';

const SyncRulesManager = () => {
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [editValue, setEditValue] = useState('');
    const [newRule, setNewRule] = useState({ 
        rule_key: '', 
        rule_name: '', 
        rule_value: '',
        is_enabled: true 
    });

    useEffect(() => {
        fetchRules();
    }, []);

    const fetchRules = async () => {
        setLoading(true);
        try {
            const response = await api.get('/rules');
            setRules(response.data);
        } catch (error) {
            console.error("Error fetching rules:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddRule = async (e) => {
        e.preventDefault();
        try {
            await api.post('/rules', newRule);
            setNewRule({ rule_key: '', rule_name: '', rule_value: '', is_enabled: true });
            setShowAddForm(false);
            fetchRules();
        } catch (error) {
            alert("Error adding rule: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleEdit = (rule) => {
        setEditingId(rule.id);
        setEditValue(rule.rule_value);
    };

    const handleSaveEdit = async (id) => {
        try {
            await api.put(`/rules/${id}`, { rule_value: editValue });
            setEditingId(null);
            fetchRules();
        } catch (error) {
            alert("Failed to update rule: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleToggleStatus = async (rule) => {
        try {
            await api.put(`/rules/${rule.id}`, { is_enabled: !rule.is_enabled });
            fetchRules();
        } catch (error) {
            alert("Failed to toggle rule status");
        }
    };

    if (loading) return <div className="card">Loading sync rules...</div>;

    return (
        <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 className="card-title">Synchronization Rules</h2>
                <button 
                    className="btn btn-primary" 
                    onClick={() => setShowAddForm(!showAddForm)}
                >
                    {showAddForm ? 'Cancel' : '+ Add New Rule'}
                </button>
            </div>

            {showAddForm && (
                <div style={{ backgroundColor: '#f9f9f9', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', border: '1px solid #ddd' }}>
                    <h3 style={{ marginTop: 0 }}>Add New System Rule</h3>
                    <form onSubmit={handleAddRule}>
                        <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                            <div className="form-group">
                                <label>Internal Key (e.g., RevenueAccount)</label>
                                <input 
                                    type="text" 
                                    value={newRule.rule_key} 
                                    onChange={(e) => setNewRule({...newRule, rule_key: e.target.value})} 
                                    placeholder="Unique identifier for the code"
                                    required 
                                />
                            </div>
                            <div className="form-group">
                                <label>Rule Name (Display Only)</label>
                                <input 
                                    type="text" 
                                    value={newRule.rule_name} 
                                    onChange={(e) => setNewRule({...newRule, rule_name: e.target.value})} 
                                    placeholder="e.g., Default Revenue Account"
                                    required 
                                />
                            </div>
                        </div>
                        <div className="form-group" style={{ marginBottom: '1rem' }}>
                            <label>Value (e.g., 4001: Sales)</label>
                            <input 
                                type="text" 
                                value={newRule.rule_value} 
                                onChange={(e) => setNewRule({...newRule, rule_value: e.target.value})} 
                                placeholder="The actual value used in mapping"
                                required 
                            />
                        </div>
                        <button type="submit" className="btn btn-success">Save Rule to Database</button>
                    </form>
                </div>
            )}

            <div className="table-responsive">
                <table className="rules-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ textAlign: 'left', borderBottom: '2px solid #eee' }}>
                            <th style={{ padding: '0.75rem' }}>Rule Name</th>
                            <th style={{ padding: '0.75rem' }}>Value</th>
                            <th style={{ padding: '0.75rem' }}>Status</th>
                            <th style={{ padding: '0.75rem' }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rules.map(rule => (
                            <tr key={rule.id} style={{ borderBottom: '1px solid #eee' }}>
                                <td style={{ padding: '0.75rem' }}>
                                    <strong>{rule.rule_name}</strong>
                                    <br />
                                    <small style={{ color: '#666' }}>Key: {rule.rule_key}</small>
                                </td>
                                <td style={{ padding: '0.75rem' }}>
                                    {editingId === rule.id ? (
                                        <input 
                                            type="text" 
                                            value={editValue} 
                                            onChange={(e) => setEditValue(e.target.value)} 
                                            style={{ width: '100%' }}
                                        />
                                    ) : (
                                        <code style={{ backgroundColor: '#f4f4f4', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                                            {rule.rule_value}
                                        </code>
                                    )}
                                </td>
                                <td style={{ padding: '0.75rem' }}>
                                    <span 
                                        className={`status-badge ${rule.is_enabled ? 'success' : 'error'}`}
                                        onClick={() => handleToggleStatus(rule)}
                                        style={{ cursor: 'pointer' }}
                                    >
                                        {rule.is_enabled ? 'Active' : 'Disabled'}
                                    </span>
                                </td>
                                <td style={{ padding: '0.75rem' }}>
                                    {editingId === rule.id ? (
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button onClick={() => handleSaveEdit(rule.id)} className="btn btn-success btn-sm">Save</button>
                                            <button onClick={() => setEditingId(null)} className="btn btn-secondary btn-sm">Cancel</button>
                                        </div>
                                    ) : (
                                        <button onClick={() => handleEdit(rule)} className="btn btn-outline btn-sm">Edit</button>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {rules.length === 0 && (
                            <tr>
                                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                                    No rules found. Add one to get started.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default SyncRulesManager;