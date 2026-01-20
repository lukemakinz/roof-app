import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { quotesAPI } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import Layout from '../components/Layout';
import {
    Plus, Search, Filter, MoreVertical, FileText, Calendar,
    TrendingUp, Clock, CheckCircle, XCircle, Send, Loader2
} from 'lucide-react';

const statusConfig = {
    draft: { label: 'Roboczy', class: 'status-draft', icon: Clock },
    sent: { label: 'Wysłano', class: 'status-sent', icon: Send },
    accepted: { label: 'Zaakceptowano', class: 'status-accepted', icon: CheckCircle },
    rejected: { label: 'Odrzucono', class: 'status-rejected', icon: XCircle },
};

export default function DashboardPage() {
    const { user } = useAuthStore();
    const [quotes, setQuotes] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        fetchQuotes();
    }, []);

    const fetchQuotes = async () => {
        try {
            const response = await quotesAPI.getAll();
            setQuotes(response.data.results || response.data);
        } catch (error) {
            console.error('Failed to fetch quotes:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredQuotes = quotes.filter((quote) => {
        const matchesSearch =
            quote.client_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            quote.number?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'all' || quote.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    // Stats calculation
    const stats = {
        total: quotes.length,
        draft: quotes.filter((q) => q.status === 'draft').length,
        sent: quotes.filter((q) => q.status === 'sent').length,
        accepted: quotes.filter((q) => q.status === 'accepted').length,
        totalValue: quotes
            .filter((q) => q.status === 'accepted')
            .reduce((sum, q) => sum + (parseFloat(q.total_gross) || 0), 0),
    };

    return (
        <Layout>
            <div className="space-y-8 animate-fade-in">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white">
                            Witaj, {user?.first_name || user?.username || 'Użytkowniku'}
                        </h1>
                        <p className="text-dark-400 mt-1">
                            Zarządzaj swoimi wycenami dachów
                        </p>
                    </div>
                    <Link to="/quotes/new" className="btn-primary flex items-center gap-2">
                        <Plus className="w-5 h-5" />
                        Nowa wycena
                    </Link>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-dark-400 text-sm">Wszystkie wyceny</p>
                                <p className="text-3xl font-bold text-white mt-1">{stats.total}</p>
                            </div>
                            <div className="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center">
                                <FileText className="w-6 h-6 text-brand-400" />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-dark-400 text-sm">Robocze</p>
                                <p className="text-3xl font-bold text-white mt-1">{stats.draft}</p>
                            </div>
                            <div className="w-12 h-12 rounded-xl bg-dark-600/50 flex items-center justify-center">
                                <Clock className="w-6 h-6 text-dark-400" />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-dark-400 text-sm">Zaakceptowane</p>
                                <p className="text-3xl font-bold text-white mt-1">{stats.accepted}</p>
                            </div>
                            <div className="w-12 h-12 rounded-xl bg-success-500/10 flex items-center justify-center">
                                <CheckCircle className="w-6 h-6 text-success-400" />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-dark-400 text-sm">Wartość zamówień</p>
                                <p className="text-2xl font-bold text-white mt-1">
                                    {stats.totalValue.toLocaleString('pl-PL')} <span className="text-lg text-dark-400">PLN</span>
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-xl bg-success-500/10 flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-success-400" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Szukaj wycen..."
                            className="input-field pl-12"
                        />
                    </div>
                    <div className="flex gap-2">
                        {['all', 'draft', 'sent', 'accepted', 'rejected'].map((status) => (
                            <button
                                key={status}
                                onClick={() => setStatusFilter(status)}
                                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${statusFilter === status
                                        ? 'bg-brand-500 text-white'
                                        : 'bg-dark-800 text-dark-300 hover:bg-dark-700'
                                    }`}
                            >
                                {status === 'all' ? 'Wszystkie' : statusConfig[status]?.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Quotes List */}
                <div className="card overflow-hidden p-0">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
                            <p className="text-dark-400 mt-4">Ładowanie wycen...</p>
                        </div>
                    ) : filteredQuotes.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 px-4">
                            <div className="w-16 h-16 rounded-2xl bg-dark-700 flex items-center justify-center mb-4">
                                <FileText className="w-8 h-8 text-dark-400" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">
                                {quotes.length === 0 ? 'Brak wycen' : 'Brak wyników'}
                            </h3>
                            <p className="text-dark-400 text-center max-w-sm mb-6">
                                {quotes.length === 0
                                    ? 'Utwórz swoją pierwszą wycenę, aby zacząć zarabiać szybciej.'
                                    : 'Zmień kryteria wyszukiwania, aby znaleźć wyceny.'}
                            </p>
                            {quotes.length === 0 && (
                                <Link to="/quotes/new" className="btn-primary">
                                    <Plus className="w-5 h-5 mr-2" />
                                    Nowa wycena
                                </Link>
                            )}
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-dark-700">
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Numer</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Klient</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4 hidden md:table-cell">Typ dachu</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4 hidden lg:table-cell">Powierzchnia</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Wartość</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4">Status</th>
                                    <th className="text-left text-dark-400 text-sm font-medium px-6 py-4 hidden sm:table-cell">Data</th>
                                    <th className="px-6 py-4"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredQuotes.map((quote) => {
                                    const StatusIcon = statusConfig[quote.status]?.icon || Clock;
                                    return (
                                        <tr
                                            key={quote.id}
                                            className="border-b border-dark-700/50 hover:bg-dark-800/50 transition-colors"
                                        >
                                            <td className="px-6 py-4">
                                                <Link
                                                    to={`/quotes/${quote.id}`}
                                                    className="text-brand-400 hover:text-brand-300 font-medium"
                                                >
                                                    {quote.number}
                                                </Link>
                                            </td>
                                            <td className="px-6 py-4 text-white">
                                                {quote.client_name || <span className="text-dark-500">-</span>}
                                            </td>
                                            <td className="px-6 py-4 text-dark-300 hidden md:table-cell">
                                                {quote.roof_type_display}
                                            </td>
                                            <td className="px-6 py-4 text-dark-300 hidden lg:table-cell">
                                                {quote.real_area ? `${quote.real_area} m²` : '-'}
                                            </td>
                                            <td className="px-6 py-4 text-white font-medium">
                                                {quote.total_gross
                                                    ? `${parseFloat(quote.total_gross).toLocaleString('pl-PL')} PLN`
                                                    : '-'}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={statusConfig[quote.status]?.class}>
                                                    <StatusIcon className="w-3 h-3 mr-1.5" />
                                                    {statusConfig[quote.status]?.label}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-dark-400 text-sm hidden sm:table-cell">
                                                {new Date(quote.created_at).toLocaleDateString('pl-PL')}
                                            </td>
                                            <td className="px-6 py-4">
                                                <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                                                    <MoreVertical className="w-4 h-4 text-dark-400" />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </Layout>
    );
}
