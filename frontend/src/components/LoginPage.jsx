import { useState, useEffect } from 'react';
import { EnvelopeIcon } from '@heroicons/react/24/outline';
import { login, setupUser, checkAuth } from '../services/api';

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSetup, setIsSetup] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    checkAuth()
      .then((res) => setIsSetup(!res.data.has_users))
      .catch(() => setIsSetup(false))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const res = isSetup
        ? await setupUser(username, password)
        : await login(username, password);

      localStorage.setItem('auth_token', res.data.token);
      localStorage.setItem('auth_username', res.data.username);
      onLogin();
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <EnvelopeIcon className="h-12 w-12 text-blue-600 mx-auto" />
          <h1 className="mt-4 text-2xl font-bold text-gray-900">
            AI Email Auto-Reply
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {isSetup ? 'Create your admin account to get started' : 'Sign in to your dashboard'}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-8">
          {isSetup && (
            <div className="mb-6 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                Welcome! Create your admin account to begin using the system.
              </p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-50 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter username"
                required
                minLength={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter password"
                required
                minLength={6}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {submitting
                ? 'Please wait...'
                : isSetup
                  ? 'Create Account'
                  : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
