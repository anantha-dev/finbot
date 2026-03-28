'use client';
import { useState } from 'react';
//import LoginPage from '@/components/LoginPage';
//import ChatPage from '@/components/ChatPage';

import LoginPage from './components/LoginPage';
import ChatPage from './components/ChatPage';

export interface User {
  username: string;
  name: string;
  role: string;
  collections: string[];
  session_id: string;
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {user ? (
        <ChatPage user={user} onLogout={handleLogout} />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </main>
  );
}
