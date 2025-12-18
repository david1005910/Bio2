'use client';

import { useRouter } from 'next/router';
import { MessageSquare, Sparkles } from 'lucide-react';
import Layout from '@/components/Layout';
import ChatInterface from '@/components/ChatInterface';

export default function ChatPage() {
  const router = useRouter();
  const { pmid, q } = router.query;

  let initialQuestion = '';
  if (pmid) {
    initialQuestion = `Tell me about the paper with PMID ${pmid}`;
  } else if (q) {
    initialQuestion = q as string;
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="gooey-card p-6 mb-6">
          <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
            <MessageSquare className="h-7 w-7 text-purple-400" />
            AI Research Assistant
          </h1>
          <p className="text-white/60 text-sm flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-pink-400" />
            Ask questions about biomedical research. Get answers with citations from scientific papers.
          </p>
        </div>

        <ChatInterface initialQuestion={initialQuestion} />
      </div>
    </Layout>
  );
}
