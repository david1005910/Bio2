'use client';

import { useState, FormEvent } from 'react';
import { Search, Filter, X, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';

interface SearchBarProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export interface SearchFilters {
  yearStart?: number;
  yearEnd?: number;
  journals?: string;
  sortBy: 'relevance' | 'date' | 'citations';
}

export default function SearchBar({
  onSearch,
  isLoading = false,
  placeholder = 'Search papers...',
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    sortBy: 'relevance',
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), filters);
    }
  };

  const currentYear = new Date().getFullYear();

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-white/50" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="gooey-input w-full pl-12 pr-28 py-3.5"
            placeholder={placeholder}
            disabled={isLoading}
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-2">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={clsx(
                'p-2.5 rounded-xl transition-all duration-300',
                showFilters
                  ? 'bg-gradient-to-br from-pink-500/30 to-purple-500/30 text-pink-300 border border-pink-400/30'
                  : 'bg-white/10 text-white/60 hover:text-white hover:bg-white/20 border border-white/10'
              )}
            >
              <Filter className="h-5 w-5" />
            </button>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className={clsx(
                'gooey-btn-primary px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-all duration-300'
              )}
            >
              {isLoading ? (
                'Searching...'
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Search
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Filters panel */}
      {showFilters && (
        <div className="mt-4 p-5 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Filter className="h-4 w-4 text-pink-400" />
              Filters
            </h3>
            <button
              onClick={() => setShowFilters(false)}
              className="p-1.5 text-white/50 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Year range */}
            <div>
              <label className="block text-xs font-medium text-white/60 mb-2">
                Year From
              </label>
              <input
                type="number"
                min={1900}
                max={currentYear}
                value={filters.yearStart || ''}
                onChange={(e) =>
                  setFilters({ ...filters, yearStart: e.target.value ? parseInt(e.target.value) : undefined })
                }
                className="gooey-input w-full px-3 py-2 text-sm"
                placeholder="1900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-2">
                Year To
              </label>
              <input
                type="number"
                min={1900}
                max={currentYear}
                value={filters.yearEnd || ''}
                onChange={(e) =>
                  setFilters({ ...filters, yearEnd: e.target.value ? parseInt(e.target.value) : undefined })
                }
                className="gooey-input w-full px-3 py-2 text-sm"
                placeholder={currentYear.toString()}
              />
            </div>

            {/* Journals */}
            <div>
              <label className="block text-xs font-medium text-white/60 mb-2">
                Journals
              </label>
              <input
                type="text"
                value={filters.journals || ''}
                onChange={(e) => setFilters({ ...filters, journals: e.target.value })}
                className="gooey-input w-full px-3 py-2 text-sm"
                placeholder="Nature, Cell"
              />
            </div>

            {/* Sort by */}
            <div>
              <label className="block text-xs font-medium text-white/60 mb-2">
                Sort By
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) =>
                  setFilters({ ...filters, sortBy: e.target.value as 'relevance' | 'date' | 'citations' })
                }
                className="gooey-input w-full px-3 py-2 text-sm"
              >
                <option value="relevance">Relevance</option>
                <option value="date">Date</option>
                <option value="citations">Citations</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
