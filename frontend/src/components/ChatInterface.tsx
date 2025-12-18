'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { Send, Bot, User, Loader2, ExternalLink, AlertCircle, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';
import { chatApi, RAGResponse } from '@/services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGResponse['sources'];
  confidence?: number;
  timestamp: Date;
}

interface ChatInterfaceProps {
  initialQuestion?: string;
}

export default function ChatInterface({ initialQuestion }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(initialQuestion || '');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialSubmitted = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialQuestion && !initialSubmitted.current) {
      initialSubmitted.current = true;
      handleSubmit(new Event('submit') as unknown as FormEvent);
    }
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatApi.query(input.trim(), {
        session_id: sessionId || undefined,
        max_sources: 5,
      });

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] gooey-card overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="inline-flex p-4 rounded-full bg-gradient-to-br from-purple-500/30 to-pink-500/30 mb-4">
              <Bot className="h-12 w-12 text-purple-300" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              Ask me about biomedical research
            </h3>
            <p className="text-white/60 max-w-md mx-auto text-sm">
              I can help you understand research papers, find related studies, and answer
              questions about specific topics.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {[
                'What are the latest CAR-T therapy improvements?',
                'Explain CRISPR off-target effects',
                'Compare mRNA vs viral vector vaccines',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="gooey-btn px-4 py-2 text-sm font-medium"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              'flex gap-3',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/30 to-pink-500/30 flex items-center justify-center border border-white/10">
                <Bot className="h-5 w-5 text-purple-300" />
              </div>
            )}

            <div
              className={clsx(
                'max-w-[80%] rounded-2xl px-4 py-3',
                message.role === 'user'
                  ? 'bg-gradient-to-br from-pink-500 to-purple-600 text-white shadow-lg shadow-pink-500/20'
                  : 'bg-white/10 backdrop-blur-sm text-white border border-white/10'
              )}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/20">
                  <p className="text-xs font-medium text-white/50 mb-2 flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    Sources:
                  </p>
                  <div className="space-y-2">
                    {message.sources.map((source, idx) => (
                      <a
                        key={idx}
                        href={`https://pubmed.ncbi.nlm.nih.gov/${source.pmid}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start gap-2 text-sm hover:bg-white/10 rounded-lg p-2 -mx-2 transition-colors"
                      >
                        <ExternalLink className="h-4 w-4 mt-0.5 flex-shrink-0 text-pink-400" />
                        <div className="min-w-0">
                          <p className="font-medium truncate text-white/90">{source.title}</p>
                          <p className="text-xs text-white/50">
                            PMID: {source.pmid} • {Math.round(source.relevance * 100)}% relevant
                          </p>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Confidence */}
              {message.confidence !== undefined && (
                <div className="mt-2 flex items-center gap-1 text-xs text-white/50">
                  <AlertCircle className="h-3 w-3" />
                  <span>
                    Confidence: {Math.round(message.confidence * 100)}%
                  </span>
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/30 to-blue-500/30 flex items-center justify-center border border-white/10">
                <User className="h-5 w-5 text-cyan-300" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/30 to-pink-500/30 flex items-center justify-center border border-white/10">
              <Bot className="h-5 w-5 text-purple-300" />
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl px-4 py-3 border border-white/10">
              <Loader2 className="h-5 w-5 animate-spin text-pink-400" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/10 p-4 bg-white/5">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about biomedical research..."
            className="gooey-input flex-1 px-4 py-3"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className={clsx(
              'gooey-btn-primary px-5 py-3 rounded-xl font-medium',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-all duration-300 flex items-center gap-2'
            )}
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
