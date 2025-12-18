'use client';

import { useRouter } from 'next/router';
import { Search, MessageSquare, TrendingUp, BookOpen, Sparkles, Zap } from 'lucide-react';
import Layout from '@/components/Layout';

const features = [
  {
    name: 'Semantic Search',
    description: 'Find relevant papers using natural language queries',
    icon: Search,
    href: '/search',
    gradient: 'from-cyan-500 to-blue-500',
  },
  {
    name: 'AI Chat',
    description: 'Ask questions and get AI-powered answers with citations',
    icon: MessageSquare,
    href: '/chat',
    gradient: 'from-purple-500 to-pink-500',
  },
  {
    name: 'Research Trends',
    description: 'Discover emerging topics and track keyword trends',
    icon: TrendingUp,
    href: '/trends',
    gradient: 'from-green-500 to-emerald-500',
  },
  {
    name: 'My Library',
    description: 'Save and organize papers for later reference',
    icon: BookOpen,
    href: '/library',
    gradient: 'from-orange-500 to-yellow-500',
  },
];

export default function Home() {
  const router = useRouter();

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Hero */}
        <div className="gooey-card p-8 md:p-12 mb-8 text-center relative overflow-hidden">
          {/* Decorative elements */}
          <div className="absolute top-4 right-4 w-20 h-20 bg-gradient-to-br from-pink-500/30 to-purple-500/30 rounded-full blur-2xl" />
          <div className="absolute bottom-4 left-4 w-16 h-16 bg-gradient-to-br from-cyan-500/30 to-blue-500/30 rounded-full blur-2xl" />

          <div className="relative z-10">
            <div className="flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8 text-pink-400 mr-2" />
              <Zap className="h-6 w-6 text-yellow-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Welcome to{' '}
              <span className="bg-gradient-to-r from-pink-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                Bio-RAG
              </span>
            </h1>
            <p className="text-lg text-white/70 max-w-2xl mx-auto">
              AI-powered biomedical research assistant. Search papers, get answers, and discover trends.
            </p>
          </div>
        </div>

        {/* Quick search */}
        <div className="mb-10">
          <div className="relative max-w-2xl mx-auto">
            <div className="gooey-card p-2">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-white/50" />
                <input
                  type="text"
                  placeholder="Search papers or ask a question..."
                  className="gooey-input w-full pl-12 pr-4 py-4 text-lg"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      router.push(`/search?q=${encodeURIComponent(e.currentTarget.value)}`);
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {features.map((feature) => (
            <button
              key={feature.name}
              onClick={() => router.push(feature.href)}
              className="gooey-card p-6 text-left group hover:scale-[1.02] transition-all duration-300"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-2xl bg-gradient-to-br ${feature.gradient} shadow-lg`}>
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white group-hover:text-pink-300 transition-colors">
                    {feature.name}
                  </h3>
                  <p className="text-white/60 text-sm mt-1">{feature.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Stats */}
        <div className="mt-10 gooey-card p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Papers Indexed', value: '1M+', icon: '📄' },
              { label: 'Daily Updates', value: '5,000+', icon: '🔄' },
              { label: 'Research Topics', value: '500+', icon: '🔬' },
              { label: 'Active Users', value: '10K+', icon: '👥' },
            ].map((stat) => (
              <div
                key={stat.label}
                className="text-center p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-colors"
              >
                <span className="text-2xl mb-2 block">{stat.icon}</span>
                <p className="text-2xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-sm text-white/50">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
