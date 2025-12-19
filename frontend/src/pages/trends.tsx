'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Loader2, BarChart3, Sparkles } from 'lucide-react';
import Layout from '@/components/Layout';
import { analyticsApi } from '@/services/api';

interface KeywordTrend {
  keyword: string;
  count: number;
  growth: number;
}

interface TrendData {
  keywords: KeywordTrend[];
  period: string;
}

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month');

  useEffect(() => {
    const fetchTrends = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await analyticsApi.getKeywordTrends({ aggregation: period === 'week' ? 'weekly' : period === 'month' ? 'monthly' : 'yearly' });
        setTrends(data);
      } catch (err) {
        setError('Failed to load trends. Please try again later.');
        console.error('Error fetching trends:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrends();
  }, [period]);

  // Mock data for display when API is not available
  const mockTrends: KeywordTrend[] = [
    { keyword: 'immunotherapy', count: 1250, growth: 15.2 },
    { keyword: 'CRISPR', count: 980, growth: 22.5 },
    { keyword: 'COVID-19', count: 890, growth: -8.3 },
    { keyword: 'CAR-T cells', count: 720, growth: 18.7 },
    { keyword: 'gene editing', count: 650, growth: 12.4 },
    { keyword: 'mRNA vaccine', count: 580, growth: 25.1 },
    { keyword: 'checkpoint inhibitors', count: 540, growth: 9.8 },
    { keyword: 'precision medicine', count: 480, growth: 14.2 },
  ];

  const displayTrends = trends?.keywords || mockTrends;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="gooey-card p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <TrendingUp className="h-7 w-7 text-green-400" />
                Research Trends
              </h1>
              <p className="text-white/60 text-sm mt-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-pink-400" />
                Explore trending topics in biomedical research
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-white/50" />
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value as 'week' | 'month' | 'year')}
                className="gooey-input px-4 py-2 text-sm font-medium"
              >
                <option value="week">Past Week</option>
                <option value="month">Past Month</option>
                <option value="year">Past Year</option>
              </select>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="gooey-card p-12 flex flex-col items-center justify-center">
            <Loader2 className="h-10 w-10 animate-spin text-pink-400 mb-4" />
            <span className="text-white/70">Loading trends...</span>
          </div>
        ) : error ? (
          <div className="gooey-card p-8 text-center">
            <p className="text-yellow-300 mb-4">{error}</p>
            <p className="text-white/50 text-sm">Showing sample data</p>
          </div>
        ) : null}

        <div className="grid gap-4">
          {displayTrends.map((trend, index) => (
            <div
              key={trend.keyword}
              className="gooey-card p-5 hover:scale-[1.01] transition-all duration-300"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-white/30 w-10 text-center">
                    #{index + 1}
                  </span>
                  <div>
                    <h3 className="text-lg font-semibold text-white hover:text-pink-300 transition-colors">
                      {trend.keyword}
                    </h3>
                    <p className="text-white/50 text-sm">
                      {trend.count.toLocaleString()} papers
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="w-48 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min((trend.count / 1500) * 100, 100)}%` }}
                    />
                  </div>

                  <div
                    className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-semibold ${
                      trend.growth >= 0
                        ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-300 border border-green-400/30'
                        : 'bg-gradient-to-r from-red-500/20 to-orange-500/20 text-red-300 border border-red-400/30'
                    }`}
                  >
                    <BarChart3 className="h-4 w-4" />
                    {trend.growth >= 0 ? '+' : ''}{trend.growth.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center text-white/40 text-sm">
          Data based on PubMed publications analysis
        </div>
      </div>
    </Layout>
  );
}
