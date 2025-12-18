'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Sparkles } from 'lucide-react';
import Layout from '@/components/Layout';
import SearchBar, { SearchFilters } from '@/components/SearchBar';
import PaperCard from '@/components/PaperCard';
import { searchApi, papersApi, SearchResult } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

export default function SearchPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({ sortBy: 'relevance' });
  const [savedPapers, setSavedPapers] = useState<Set<string>>(new Set());

  // Get initial query from URL
  useEffect(() => {
    if (router.query.q) {
      setSearchQuery(router.query.q as string);
    }
  }, [router.query.q]);

  // Search query
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', searchQuery, filters],
    queryFn: () =>
      searchApi.search(searchQuery, {
        limit: 20,
        year_start: filters.yearStart,
        year_end: filters.yearEnd,
        journals: filters.journals,
        sort_by: filters.sortBy,
      }),
    enabled: !!searchQuery,
  });

  // Fetch saved papers
  useQuery({
    queryKey: ['savedPapers'],
    queryFn: async () => {
      const saved = await papersApi.getSaved();
      setSavedPapers(new Set(saved.map((p: SearchResult) => p.pmid)));
      return saved;
    },
    enabled: isAuthenticated,
  });

  const handleSearch = (query: string, newFilters: SearchFilters) => {
    setSearchQuery(query);
    setFilters(newFilters);
    router.push(`/search?q=${encodeURIComponent(query)}`, undefined, { shallow: true });
  };

  const handleSave = async (pmid: string) => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    await papersApi.save(pmid);
    setSavedPapers((prev) => new Set([...prev, pmid]));
  };

  const handleUnsave = async (pmid: string) => {
    await papersApi.unsave(pmid);
    setSavedPapers((prev) => {
      const next = new Set(prev);
      next.delete(pmid);
      return next;
    });
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="gooey-card p-6 mb-6">
          <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
            <Sparkles className="h-7 w-7 text-pink-400" />
            Search Papers
          </h1>
          <p className="text-white/60 text-sm">
            Discover biomedical research using AI-powered semantic search
          </p>
        </div>

        <div className="gooey-card p-4 mb-6">
          <SearchBar
            onSearch={handleSearch}
            isLoading={isLoading}
            placeholder="Search for papers using natural language..."
          />
        </div>

        {/* Results */}
        <div className="mt-6">
          {isLoading && (
            <div className="flex justify-center py-12">
              <div className="gooey-card p-8 flex flex-col items-center">
                <Loader2 className="h-10 w-10 animate-spin text-pink-400 mb-4" />
                <p className="text-white/70">Searching papers...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="gooey-card p-8 text-center">
              <p className="text-pink-300">Failed to load results. Please try again.</p>
            </div>
          )}

          {data && (
            <>
              <div className="flex items-center justify-between mb-4 px-2">
                <p className="text-sm text-white/70">
                  Found <span className="text-pink-400 font-semibold">{data.total}</span> results for "{data.query}"
                  <span className="ml-2 text-white/50">({data.query_time_ms}ms)</span>
                </p>
              </div>

              {data.results.length === 0 ? (
                <div className="gooey-card p-12 text-center">
                  <p className="text-white/60">
                    No papers found. Try a different search query.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {data.results.map((paper) => (
                    <PaperCard
                      key={paper.pmid}
                      paper={paper}
                      onSave={handleSave}
                      onUnsave={handleUnsave}
                      isSaved={savedPapers.has(paper.pmid)}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {!searchQuery && !isLoading && (
            <div className="gooey-card p-12 text-center">
              <Sparkles className="h-12 w-12 text-purple-400 mx-auto mb-4" />
              <p className="text-white/70 mb-6">
                Enter a search query to find relevant papers.
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                {[
                  'CRISPR gene editing',
                  'CAR-T cell therapy',
                  'mRNA vaccines',
                  'single cell RNA sequencing',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSearch(suggestion, filters)}
                    className="gooey-btn px-4 py-2 text-sm font-medium"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
