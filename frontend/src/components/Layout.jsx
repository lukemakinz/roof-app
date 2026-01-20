import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import {
    Home, FileText, Settings, LogOut, Menu, X, User, ChevronDown, Layout as LayoutIcon, Key
} from 'lucide-react';
import { useState } from 'react';

export default function Layout({ children }) {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navItems = [
        { to: '/', icon: Home, label: 'Dashboard' },
        { to: '/quotes', icon: FileText, label: 'Wyceny' },
        { to: '/widget-config', icon: LayoutIcon, label: 'Widget' },
        { to: '/api-keys', icon: Key, label: 'Klucze API' },
        { to: '/settings', icon: Settings, label: 'Ustawienia' },
    ];

    return (
        <div className="min-h-screen bg-dark-950 mesh-bg">
            {/* Mobile Header */}
            <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass border-b border-dark-700/50 px-4 py-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setSidebarOpen(true)}
                            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                        >
                            <Menu className="w-5 h-5 text-white" />
                        </button>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
                                <Home className="w-4 h-4 text-white" />
                            </div>
                            <span className="font-bold text-white">RoofQuote</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Sidebar Backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed top-0 left-0 h-full w-64 z-50 transform transition-transform duration-300
          lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          glass border-r border-dark-700/50
        `}
            >
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="flex items-center justify-between p-6 border-b border-dark-700/50">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
                                <Home className="w-5 h-5 text-white" />
                            </div>
                            <span className="text-xl font-bold text-white">RoofQuote</span>
                        </div>
                        <button
                            onClick={() => setSidebarOpen(false)}
                            className="lg:hidden p-2 hover:bg-dark-800 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-dark-400" />
                        </button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-4 space-y-1">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.to}
                                to={item.to}
                                onClick={() => setSidebarOpen(false)}
                                className={({ isActive }) =>
                                    `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive
                                        ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                                        : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                                    }`
                                }
                            >
                                <item.icon className="w-5 h-5" />
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>

                    {/* User section */}
                    <div className="p-4 border-t border-dark-700/50">
                        <div
                            className="relative"
                            onBlur={() => setTimeout(() => setUserMenuOpen(false), 150)}
                        >
                            <button
                                onClick={() => setUserMenuOpen(!userMenuOpen)}
                                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-dark-800 transition-colors"
                            >
                                <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center">
                                    <User className="w-5 h-5 text-brand-400" />
                                </div>
                                <div className="flex-1 text-left">
                                    <div className="text-sm font-medium text-white truncate">
                                        {user?.first_name || user?.username || 'Użytkownik'}
                                    </div>
                                    <div className="text-xs text-dark-400 truncate">
                                        {user?.email}
                                    </div>
                                </div>
                                <ChevronDown className={`w-4 h-4 text-dark-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {userMenuOpen && (
                                <div className="absolute bottom-full left-0 right-0 mb-2 bg-dark-800 border border-dark-700 rounded-xl shadow-lg overflow-hidden">
                                    <button
                                        onClick={handleLogout}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-left text-error-400 hover:bg-dark-700 transition-colors"
                                    >
                                        <LogOut className="w-4 h-4" />
                                        Wyloguj się
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="lg:ml-64 min-h-screen">
                <div className="p-4 lg:p-8 pt-20 lg:pt-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
