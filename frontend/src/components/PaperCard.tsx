'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ExternalLink,
  BookmarkPlus,
  BookmarkCheck,
  ChevronDown,
  ChevronUp,
  Users,
  Calendar,
  Quote,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';
import { SearchResult } from '@/services/api';

interface PaperCardProps {
  paper: SearchResult;
  onSave?: (pmid: string) => void;
  onUnsave?: (pmid: string) => void;
  isSaved?: boolean;
}

export default function PaperCard({
  paper,
  onSave,
  onUnsave,
  isSaved = false,
}: PaperCardProps) {
  const [showAbstract, setShowAbstract] = useState(false);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
  };

  const relevancePercent = Math.round(paper.relevance_score * 100);

  return (
    <div className="gooey-card p-5 hover:scale-[1.01] transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={clsx(
                'px-3 py-1 text-xs font-semibold rounded-full',
                relevancePercent >= 80
                  ? 'bg-gradient-to-r from-green-400/30 to-emerald-400/30 text-green-300 border border-green-400/30'
                  : relevancePercent >= 60
                  ? 'bg-gradient-to-r from-yellow-400/30 to-orange-400/30 text-yellow-300 border border-yellow-400/30'
                  : 'bg-white/10 text-white/70 border border-white/20'
              )}
            >
              <Sparkles className="inline h-3 w-3 mr-1" />
              {relevancePercent}% match
            </span>
            {paper.journal && (
              <span className="text-xs text-white/50 px-2 py-1 rounded-full bg-white/5">
                {paper.journal}
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-white leading-tight hover:text-pink-300 transition-colors">
            {paper.title}
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => (isSaved && onUnsave ? onUnsave(paper.pmid) : onSave?.(paper.pmid))}
            className={clsx(
              'p-2.5 rounded-xl transition-all duration-300',
              isSaved
                ? 'bg-gradient-to-br from-pink-500/30 to-purple-500/30 text-pink-300 border border-pink-400/30 shadow-lg shadow-pink-500/20'
                : 'bg-white/10 text-white/60 hover:text-white hover:bg-white/20 border border-white/10'
            )}
            title={isSaved ? 'Remove from library' : 'Save to library'}
          >
            {isSaved ? (
              <BookmarkCheck className="h-5 w-5" />
            ) : (
              <BookmarkPlus className="h-5 w-5" />
            )}
          </button>
          <a
            href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2.5 bg-white/10 text-white/60 hover:text-white hover:bg-white/20 rounded-xl transition-all duration-300 border border-white/10"
            title="View on PubMed"
          >
            <ExternalLink className="h-5 w-5" />
          </a>
        </div>
      </div>

      {/* Meta info */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-white/60">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5">
          <Calendar className="h-4 w-4 text-cyan-400" />
          <span>{formatDate(paper.publication_date)}</span>
        </div>
        {paper.authors.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5">
            <Users className="h-4 w-4 text-purple-400" />
            <span>
              {paper.authors.slice(0, 3).join(', ')}
              {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
            </span>
          </div>
        )}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5">
          <Quote className="h-4 w-4 text-orange-400" />
          <span>{paper.citation_count} citations</span>
        </div>
        <span className="text-white/40 text-xs">PMID: {paper.pmid}</span>
      </div>

      {/* Keywords */}
      {paper.keywords.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {paper.keywords.slice(0, 5).map((keyword) => (
            <span
              key={keyword}
              className="px-3 py-1 text-xs bg-gradient-to-r from-white/10 to-white/5 text-white/70 rounded-full border border-white/10 hover:border-white/30 transition-colors"
            >
              {keyword}
            </span>
          ))}
          {paper.keywords.length > 5 && (
            <span className="px-3 py-1 text-xs text-white/40">
              +{paper.keywords.length - 5} more
            </span>
          )}
        </div>
      )}

      {/* Abstract toggle */}
      {paper.abstract && (
        <div className="mt-4">
          <button
            onClick={() => setShowAbstract(!showAbstract)}
            className="flex items-center gap-1.5 text-sm text-pink-400 hover:text-pink-300 transition-colors font-medium"
          >
            {showAbstract ? (
              <>
                <ChevronUp className="h-4 w-4" />
                Hide abstract
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" />
                Show abstract
              </>
            )}
          </button>

          {showAbstract && (
            <div className="mt-3 p-4 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-sm text-white/70 leading-relaxed">
                {paper.abstract}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-4">
        <Link
          href={`/chat?pmid=${paper.pmid}`}
          className="gooey-btn px-4 py-2 text-sm font-medium flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          Ask AI about this paper
        </Link>
        <Link
          href={`/papers/${paper.pmid}/similar`}
          className="text-sm font-medium text-white/60 hover:text-white transition-colors"
        >
          Find similar papers
        </Link>
      </div>
    </div>
  );
}
