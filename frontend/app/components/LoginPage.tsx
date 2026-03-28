'use client';
import { useState } from 'react';
import { loginUser } from '@/lib/api';
import { User } from '../page';

interface Props {
  onLogin: (user: User) => void;
}

const DEMO_CREDENTIALS = [
  { username: 'alice',   password: 'alice123',   role: 'employee',    color: 'bg-gray-100' },
  { username: 'bob',     password: 'bob123',     role: 'finance',     color: 'bg-blue-100' },
  { username: 'charlie', password: 'charlie123', role: 'engineering', color: 'bg-green-100' },
  { username: 'diana',   password: 'diana123',   role: 'marketing',   color: 'bg-purple-100' },
  { username: 'eve',     password: 'eve123',     role: 'c_level',     color: 'bg-yellow-100' },
];

export default function LoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleLogin = async (u?: string, p?: string) => {
    const user = u || username;
    const pass = p || password;
    if (!user || !pass) return;

    setLoading(true);
    setError('');
    try {
      const data = await loginUser(user, pass);
      onLogin({
        ...data,
        session_id: `${user}-${Date.now()}`,
      });
    } catch {
      setError('Invalid username or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🤖</div>
          <h1 className="text-2xl font-bold text-gray-800">FinBot</h1>
          <p className="text-gray-500 text-sm mt-1">
            FinSolve Technologies Internal Assistant
          </p>
        </div>

        {/* Login form */}
        <div className="space-y-4 mb-6">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}
          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>

        {/* Demo accounts */}
        <div>
          <p className="text-xs text-gray-400 text-center mb-3">
            — Demo accounts —
          </p>
          <div className="space-y-2">
            {DEMO_CREDENTIALS.map(cred => (
              <button
                key={cred.username}
                onClick={() => handleLogin(cred.username, cred.password)}
                className={`w-full ${cred.color} rounded-lg px-4 py-2 text-sm text-left hover:opacity-80 transition`}
              >
                <span className="font-medium capitalize">{cred.username}</span>
                <span className="text-gray-500 ml-2">— {cred.role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
