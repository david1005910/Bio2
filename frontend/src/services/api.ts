import axios, { AxiosError, AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);

          // Retry original request
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
            return api.request(error.config);
          }
        } catch {
          // Refresh failed, clear tokens
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
    }
    return Promise.reject(error);
  }
);

// Types
export interface SearchResult {
  pmid: string;
  title: string;
  abstract?: string;
  relevance_score: number;
  publication_date?: string;
  journal?: string;
  authors: string[];
  citation_count: number;
  keywords: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  query_time_ms: number;
  query: string;
}

export interface RAGResponse {
  answer: string;
  sources: {
    pmid: string;
    title: string;
    relevance: number;
    excerpt: string;
    section?: string;
  }[];
  confidence: number;
  response_time_ms: number;
  session_id?: string;
  chunks_used: number;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Auth API
export const authApi = {
  register: async (email: string, password: string, name?: string): Promise<User> => {
    const response = await api.post('/auth/register', { email, password, name });
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthTokens> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Search API
export const searchApi = {
  search: async (
    query: string,
    options?: {
      limit?: number;
      offset?: number;
      year_start?: number;
      year_end?: number;
      journals?: string;
      sort_by?: 'relevance' | 'date' | 'citations';
      rerank?: boolean;
    }
  ): Promise<SearchResponse> => {
    const params = new URLSearchParams({ q: query });

    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());
    if (options?.year_start) params.append('year_start', options.year_start.toString());
    if (options?.year_end) params.append('year_end', options.year_end.toString());
    if (options?.journals) params.append('journals', options.journals);
    if (options?.sort_by) params.append('sort_by', options.sort_by);
    if (options?.rerank !== undefined) params.append('rerank', options.rerank.toString());

    const response = await api.get(`/search?${params}`);
    return response.data;
  },
};

// Chat/RAG API
export const chatApi = {
  query: async (
    question: string,
    options?: {
      session_id?: string;
      max_sources?: number;
      temperature?: number;
    }
  ): Promise<RAGResponse> => {
    const response = await api.post('/chat/query', {
      question,
      ...options,
    });
    return response.data;
  },

  getHistory: async (sessionId: string) => {
    const response = await api.get(`/chat/history/${sessionId}`);
    return response.data;
  },

  clearHistory: async (sessionId: string) => {
    const response = await api.delete(`/chat/history/${sessionId}`);
    return response.data;
  },
};

// Papers API
export const papersApi = {
  list: async (options?: {
    page?: number;
    page_size?: number;
    journal?: string;
    year?: number;
  }) => {
    const params = new URLSearchParams();
    if (options?.page) params.append('page', options.page.toString());
    if (options?.page_size) params.append('page_size', options.page_size.toString());
    if (options?.journal) params.append('journal', options.journal);
    if (options?.year) params.append('year', options.year.toString());

    const response = await api.get(`/papers?${params}`);
    return response.data;
  },

  get: async (pmid: string) => {
    const response = await api.get(`/papers/${pmid}`);
    return response.data;
  },

  save: async (pmid: string, notes?: string, tags?: string) => {
    const response = await api.post(`/papers/${pmid}/save`, { notes, tags });
    return response.data;
  },

  unsave: async (pmid: string) => {
    const response = await api.delete(`/papers/${pmid}/save`);
    return response.data;
  },

  getSaved: async () => {
    const response = await api.get('/papers/library/saved');
    return response.data;
  },
};

// Recommendations API
export const recommendationsApi = {
  getSimilar: async (pmid: string, options?: {
    limit?: number;
    method?: 'content' | 'citation' | 'hybrid';
  }) => {
    const params = new URLSearchParams();
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.method) params.append('method', options.method);

    const response = await api.get(`/recommendations/similar/${pmid}?${params}`);
    return response.data;
  },

  getTrending: async (options?: {
    days?: number;
    limit?: number;
  }) => {
    const params = new URLSearchParams();
    if (options?.days) params.append('days', options.days.toString());
    if (options?.limit) params.append('limit', options.limit.toString());

    const response = await api.get(`/recommendations/trending?${params}`);
    return response.data;
  },

  getPersonalized: async (limit?: number) => {
    const params = limit ? `?limit=${limit}` : '';
    const response = await api.get(`/recommendations/personalized${params}`);
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  getKeywordTrends: async (options?: {
    keywords?: string;
    start_date?: string;
    end_date?: string;
    aggregation?: 'weekly' | 'monthly' | 'yearly';
  }) => {
    const params = new URLSearchParams();
    if (options?.keywords) params.append('keywords', options.keywords);
    if (options?.start_date) params.append('start_date', options.start_date);
    if (options?.end_date) params.append('end_date', options.end_date);
    if (options?.aggregation) params.append('aggregation', options.aggregation);

    const response = await api.get(`/analytics/trends/keywords?${params}`);
    return response.data;
  },

  getEmergingTopics: async (options?: {
    window_months?: number;
    growth_threshold?: number;
    limit?: number;
  }) => {
    const params = new URLSearchParams();
    if (options?.window_months) params.append('window_months', options.window_months.toString());
    if (options?.growth_threshold) params.append('growth_threshold', options.growth_threshold.toString());
    if (options?.limit) params.append('limit', options.limit.toString());

    const response = await api.get(`/analytics/topics/emerging?${params}`);
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/analytics/stats');
    return response.data;
  },
};

export default api;
