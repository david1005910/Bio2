'use client';

import { ReactNode, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Search,
  MessageSquare,
  TrendingUp,
  BookOpen,
  Settings,
  Menu,
  X,
  LogOut,
  User,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { clsx } from 'clsx';

interface LayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Search', href: '/search', icon: Search },
  { name: 'AI Chat', href: '/chat', icon: MessageSquare },
  { name: 'Trends', href: '/trends', icon: TrendingUp },
  { name: 'Library', href: '/library', icon: BookOpen },
];

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* SVG Gooey Filter */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <filter id="goo">
          <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
          <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9" result="goo" />
        </filter>
      </svg>

      {/* Animated Background Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
        <div className="blob blob-4" />
      </div>

      {/* Mobile sidebar */}
      <div
        className={clsx(
          'fixed inset-0 z-40 lg:hidden',
          sidebarOpen ? 'block' : 'hidden'
        )}
      >
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col glossy-panel-dark m-2 my-2 rounded-3xl overflow-hidden">
          <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
            <span className="text-xl font-bold gooey-text bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
              Bio-RAG
            </span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-xl hover:bg-white/10 transition-colors"
            >
              <X className="h-6 w-6 text-white/80" />
            </button>
          </div>
          <nav className="flex-1 space-y-2 px-3 py-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'flex items-center px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-300',
                  pathname === item.href
                    ? 'gooey-btn-primary text-white shadow-lg'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                )}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-30 lg:flex lg:w-72 lg:flex-col lg:p-3">
        <div className="flex flex-col flex-grow glossy-panel-dark rounded-3xl overflow-hidden">
          <div className="flex h-16 items-center px-6 border-b border-white/10">
            <span className="text-2xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent drop-shadow-lg">
              Bio-RAG
            </span>
          </div>
          <nav className="flex-1 space-y-2 px-3 py-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'flex items-center px-4 py-3 rounded-2xl text-sm font-semibold transition-all duration-300',
                  pathname === item.href
                    ? 'gooey-btn-primary text-white shadow-lg shadow-purple-500/25'
                    : 'text-white/70 hover:bg-white/10 hover:text-white hover:shadow-md'
                )}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </nav>

          {/* User section */}
          <div className="border-t border-white/10 p-4">
            {isAuthenticated && user ? (
              <div className="space-y-3">
                <div className="flex items-center p-2 rounded-2xl bg-white/5">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center shadow-lg">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-semibold text-white">
                      {user.name || user.email}
                    </p>
                    <p className="text-xs text-white/50">Researcher</p>
                  </div>
                </div>
                <button
                  onClick={() => logout()}
                  className="flex items-center w-full px-4 py-2.5 text-sm text-white/70 hover:bg-white/10 rounded-xl transition-all duration-300"
                >
                  <LogOut className="mr-3 h-4 w-4" />
                  Logout
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="flex items-center justify-center px-4 py-3 text-sm font-semibold gooey-btn-primary rounded-2xl transition-all duration-300"
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-72 relative z-10">
        {/* Mobile header */}
        <div className="sticky top-0 z-20 flex h-16 items-center gap-x-4 px-4 lg:hidden">
          <div className="flex-1 flex items-center gap-4 glossy-panel px-4 py-2 rounded-2xl">
            <button
              type="button"
              className="p-2 text-white/80 hover:text-white transition-colors"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <span className="text-lg font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
              Bio-RAG
            </span>
          </div>
        </div>

        <main className="py-6 px-4 sm:px-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
