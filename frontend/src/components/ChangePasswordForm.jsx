import React, { useState } from 'react';
import { changePassword } from '../api';
import { Lock } from 'lucide-react';

const ChangePasswordForm = () => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState({ type: '', text: '' });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage({ type: '', text: '' });

        if (newPassword !== confirmPassword) {
            setMessage({ type: 'error', text: 'New passwords do not match' });
            return;
        }

        if (newPassword.length < 6) {
             setMessage({ type: 'error', text: 'Password must be at least 6 characters' });
             return;
        }

        setLoading(true);
        try {
            await changePassword(currentPassword, newPassword);
            setMessage({ type: 'success', text: 'Password updated successfully' });
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error) {
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to update password' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-lg font-medium text-slate-800 mb-4 flex items-center">
                <Lock className="w-5 h-5 mr-2 text-blue-600" />
                Change Password
            </h3>

            {message.text && (
                <div className={`p-3 rounded mb-4 text-sm ${message.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-600 border border-green-200'}`}>
                    {message.text}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
                <div>
                    <label className="block text-slate-700 text-sm font-medium mb-1">Current Password</label>
                    <input
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-blue-500 transition-colors"
                        required
                    />
                </div>
                <div>
                    <label className="block text-slate-700 text-sm font-medium mb-1">New Password</label>
                    <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-blue-500 transition-colors"
                        required
                    />
                </div>
                <div>
                    <label className="block text-slate-700 text-sm font-medium mb-1">Confirm New Password</label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-blue-500 transition-colors"
                        required
                    />
                </div>
                <button
                    type="submit"
                    disabled={loading}
                    className={`bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 transition-colors ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                    {loading ? 'Updating...' : 'Update Password'}
                </button>
            </form>
        </div>
    );
};

export default ChangePasswordForm;
