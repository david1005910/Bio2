'use client';

import { useState, useEffect } from 'react';
import { BookOpen, Search, Loader2, ExternalLink, Trash2, FolderOpen, Sparkles } from 'lucide-react';
import Layout from '@/components/Layout';
import { api } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';

interface SavedPaper {
  pmid: string;
  title: string;
  abstract?: string;
  journal?: string;
  publication_date?: string;
  saved_at: string;
}

export default function LibraryPage() {
  const { user, isAuthenticated } = useAuth();
  const [papers, setPapers] = useState<SavedPaper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchLibrary = async () => {
      if (!isAuthenticated) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getSavedPapers();
        setPapers(data.papers || []);
      } catch (err) {
        setError('Failed to load your library. Please try again later.');
        console.error('Error fetching library:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLibrary();
  }, [isAuthenticated]);

  const handleRemovePaper = async (pmid: string) => {
    try {
      await api.removeSavedPaper(pmid);
      setPapers(papers.filter(p => p.pmid !== pmid));
    } catch (err) {
      console.error('Error removing paper:', err);
    }
  };

  const filteredPapers = papers.filter(paper =>
    paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.abstract?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isAuthenticated) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center py-16">
          <div className="gooey-card p-12">
            <div className="inline-flex p-4 rounded-full bg-gradient-to-br from-orange-500/30 to-yellow-500/30 mb-6">
              <FolderOpen className="h-12 w-12 text-orange-300" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Your Research Library
            </h1>
            <p className="text-white/60 mb-8">
              Sign in to save and organize your research papers
            </p>
            <Link
              href="/login"
              className="gooey-btn-primary inline-flex items-center px-8 py-3 font-semibold rounded-xl"
            >
              <Sparkles className="h-5 w-5 mr-2" />
              Sign in to continue
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="gooey-card p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <BookOpen className="h-7 w-7 text-orange-400" />
                My Library
              </h1>
              <p className="text-white/60 text-sm mt-2">
                {papers.length} saved paper{papers.length !== 1 ? 's' : ''}
              </p>
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-white/40" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search your library..."
                className="gooey-input pl-12 pr-4 py-2.5 w-64"
              />
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="gooey-card p-12 flex flex-col items-center justify-center">
            <Loader2 className="h-10 w-10 animate-spin text-pink-400 mb-4" />
            <span className="text-white/70">Loading your library...</span>
          </div>
        ) : error ? (
          <div className="gooey-card p-8 text-center">
            <p className="text-red-300">{error}</p>
          </div>
        ) : papers.length === 0 ? (
          <div className="gooey-card p-12 text-center">
            <div className="inline-flex p-4 rounded-full bg-gradient-to-br from-orange-500/30 to-yellow-500/30 mb-6">
              <BookOpen className="h-12 w-12 text-orange-300" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Your library is empty
            </h2>
            <p className="text-white/60 mb-6">
              Start saving papers from your search results
            </p>
            <Link
              href="/search"
              className="gooey-btn-primary inline-flex items-center px-6 py-3 font-semibold rounded-xl"
            >
              <Search className="h-5 w-5 mr-2" />
              Search Papers
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredPapers.map((paper) => (
              <div
                key={paper.pmid}
                className="gooey-card p-5 hover:scale-[1.01] transition-all duration-300"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2 hover:text-pink-300 transition-colors">
                      {paper.title}
                    </h3>
                    {paper.abstract && (
                      <p className="text-white/60 text-sm line-clamp-2 mb-3">
                        {paper.abstract}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 text-sm text-white/50">
                      <span className="px-3 py-1 rounded-full bg-white/5">PMID: {paper.pmid}</span>
                      {paper.journal && <span className="px-3 py-1 rounded-full bg-white/5">{paper.journal}</span>}
                      {paper.publication_date && <span className="px-3 py-1 rounded-full bg-white/5">{paper.publication_date}</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2.5 bg-white/10 text-white/60 hover:text-white hover:bg-white/20 rounded-xl transition-all duration-300 border border-white/10"
                      title="View on PubMed"
                    >
                      <ExternalLink className="h-5 w-5" />
                    </a>
                    <button
                      onClick={() => handleRemovePaper(paper.pmid)}
                      className="p-2.5 bg-white/10 text-white/60 hover:text-red-400 hover:bg-red-500/20 rounded-xl transition-all duration-300 border border-white/10"
                      title="Remove from library"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
