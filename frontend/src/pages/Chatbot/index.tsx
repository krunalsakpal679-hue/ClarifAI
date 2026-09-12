import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const ChatbotPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hello! I am your ClarifAI Legal Assistant. I can answer questions about this contract with strict grounding in the document's actual clauses. What would you like to know?",
      citations: [] as string[],
    },
    {
      role: 'user',
      text: 'Does this contract allow automatic renewal without prior notice?',
      citations: [] as string[],
    },
    {
      role: 'assistant',
      text: 'Yes. Per Section 4.2, the agreement automatically renews for successive 12-month periods unless either party provides written notice of non-renewal at least 60 days prior to the expiration of the current term.',
      citations: ['Section 4.2: Renewal Term'],
    },
  ]);
  const [inputVal, setInputVal] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const userMessage = inputVal;
    setInputVal('');
    setMessages((prev) => [
      ...prev,
      { role: 'user', text: userMessage, citations: [] },
      {
        role: 'assistant',
        text: 'Full streaming RAG interaction with citations will be connected in Phase 05. For now, this confirms your route and chat context are functioning correctly.',
        citations: ['Phase 05 AI Service Integration'],
      },
    ]);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info" size="sm">Grounded Q&amp;A</Badge>
            <span className="text-xs text-secondary-500 font-mono">Doc: {id}</span>
          </div>
          <h1 className="text-2xl font-serif font-bold text-primary-950">
            Document Assistant
          </h1>
        </div>
        <Link to={`/documents/${id}`}>
          <Button variant="outline" size="sm">
            &larr; Document Analysis
          </Button>
        </Link>
      </div>

      {/* Chat Area */}
      <Card elevation="md" className="flex flex-col h-[560px]">
        <CardHeader className="py-3 px-6 border-b border-secondary-200 bg-secondary-50/50">
          <CardTitle className="text-sm font-semibold text-secondary-800">
            Contract-Grounded Conversation
          </CardTitle>
          <CardDescription className="text-xs">
            Responses are strictly constrained to clauses present in the uploaded document.
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${
                m.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-[85%] rounded-xl p-3.5 text-sm ${
                  m.role === 'user'
                    ? 'bg-primary-900 text-white'
                    : 'bg-secondary-100 text-secondary-900 border border-secondary-200'
                }`}
              >
                <p className="leading-relaxed">{m.text}</p>
              </div>

              {m.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-1.5 ml-1">
                  {m.citations.map((cite) => (
                    <span
                      key={cite}
                      className="text-[10px] font-mono bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full"
                    >
                      📎 {cite}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </CardContent>

        <form onSubmit={handleSend} className="p-4 border-t border-secondary-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Input
                id="chat-input"
                type="text"
                placeholder="Ask any question about this contract's clauses..."
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
              />
            </div>
            <Button type="submit" variant="primary">
              Send
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
