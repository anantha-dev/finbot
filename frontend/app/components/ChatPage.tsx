'use client';
import { useState, useRef, useEffect } from 'react';
import { sendMessage } from '@/lib/api';
import { User } from '../page';

interface Message {
  id:             number;
  query:          string;
  response:       string | null;
  success:        boolean;
  route:          string | null;
  guardrail_type: string | null;
  warning:        string | null;
  stage:          string;
  chunks:         {
    source_document: string;
    page_number:     number;
    section_title:   string;
    score:           number;
  }[];
  loading:        boolean;
}

interface Props {
  user:     User;
  onLogout: () => void;
}

const ROLE_COLORS: Record<string, string> = {
  employee:    'bg-gray-200 text-gray-800',
  finance:     'bg-blue-200 text-blue-800',
  engineering: 'bg-green-200 text-green-800',
  marketing:   'bg-purple-200 text-purple-800',
  c_level:     'bg-yellow-200 text-yellow-800',
};

const GUARDRAIL_LABELS: Record<string, string> = {
  prompt_injection: '🚫 Prompt Injection Detected',
  off_topic:        '🚫 Off-Topic Query',
  pii:              '🚫 PII Detected',
  rate_limit:       '🚫 Rate Limit Exceeded',
  rbac_denied:      '🔒 Access Denied',
};

export default function ChatPage({ user, onLogout }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery]       = useState('');
  const [loading, setLoading]   = useState(false);
  const bottomRef               = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!query.trim() || loading) return;

    const newMessage: Message = {
      id:             Date.now(),
      query:          query,
      response:       null,
      success:        false,
      route:          null,
      guardrail_type: null,
      warning:        null,
      stage:          'loading',
      chunks:         [],
      loading:        true,
    };

    setMessages(prev => [...prev, newMessage]);
    setQuery('');
    setLoading(true);

    try {
      const result = await sendMessage(
        query,
        user.username,
        user.role,
        user.session_id,
      );

      setMessages(prev =>
        prev.map(m =>
          m.id === newMessage.id
            ? { ...m, ...result, loading: false }
            : m
        )
      );
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === newMessage.id
            ? {
                ...m,
                loading:  false,
                success:  false,
                response: 'Error connecting to FinBot. Please try again.',
                stage:    'error',
              }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">

      {/* Header */}
      <div className="bg-white border-b px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🤖</span>
          <div>
            <h1 className="font-bold text-gray-800">FinBot</h1>
            <p className="text-xs text-gray-400">FinSolve Technologies</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">{user.name}</p>
            <div className="flex gap-1 justify-end flex-wrap mt-1">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[user.role]}`}>
                {user.role}
              </span>
              {user.collections.map(c => (
                <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                  {c}
                </span>
              ))}
            </div>
          </div>
          <button
            onClick={onLogout}
            className="text-sm text-gray-400 hover:text-red-500 transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <div className="text-5xl mb-4">💬</div>
            <p className="text-lg font-medium">Ask FinBot anything</p>
            <p className="text-sm mt-1">
              You have access to: {user.collections.join(', ')} documents
            </p>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className="max-w-3xl mx-auto space-y-2">

            {/* User query */}
            <div className="flex justify-end">
              <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2 max-w-lg text-sm">
                {msg.query}
              </div>
            </div>

            {/* Bot response */}
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 max-w-2xl shadow-sm border text-sm space-y-3">

                {msg.loading ? (
                  <div className="flex items-center gap-2 text-gray-400">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full"/>
                    <span>Thinking...</span>
                  </div>
                ) : (
                  <>
                    {/* Guardrail warning banner */}
                    {!msg.success && msg.guardrail_type && (
                      <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-red-700 text-xs font-medium">
                        {GUARDRAIL_LABELS[msg.guardrail_type] || '🚫 Blocked'}
                      </div>
                    )}

                    {/* Response text */}
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {msg.success ? msg.response : msg.message}
                    </p>

                    {/* Output warning */}
                    {msg.warning && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-yellow-700 text-xs">
                        {msg.warning}
                      </div>
                    )}

                    {/* Route + sources */}
                    {msg.success && (
                      <div className="border-t pt-2 space-y-1">
                        {msg.route && (
                          <p className="text-xs text-gray-400">
                            Route: <span className="font-medium text-gray-500">{msg.route}</span>
                          </p>
                        )}
                        {msg.chunks.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-400 mb-1">Sources:</p>
                            {msg.chunks.slice(0, 3).map((c, i) => (
                              <div key={i} className="text-xs text-gray-500 flex gap-2">
                                <span>📄</span>
                                <span>{c.source_document} — page {c.page_number}</span>
                                <span className="text-gray-300">({c.score})</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question..."
            disabled={loading}
            className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={loading || !query.trim()}
            className="bg-blue-600 text-white rounded-xl px-5 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
