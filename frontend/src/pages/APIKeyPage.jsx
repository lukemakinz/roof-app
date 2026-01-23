import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { widgetAPI } from '../lib/api';
import { toast } from 'react-hot-toast';
import Layout from '../components/Layout';
import { format } from 'date-fns';
import { Trash2, Copy } from 'lucide-react';

export default function APIKeyPage() {
    // const { token } = useAuthStore(); // No longer needed
    const queryClient = useQueryClient();
    const [newKey, setNewKey] = useState(null);

    const { data: keys, isLoading } = useQuery({
        queryKey: ['apiKeys'],
        queryFn: async () => {
            const res = await widgetAPI.getKeys();
            return res.data;
        }
    });

    const createMutation = useMutation({
        mutationFn: async (name) => {
            const res = await widgetAPI.createKey(name);
            return res.data;
        },
        onSuccess: (data) => {
            setNewKey(data);
            toast.success('Klucz utworzony!');
            queryClient.invalidateQueries(['apiKeys']);
        },
        onError: (error) => {
            toast.error(error.response?.data?.error || 'Błąd tworzenia klucza');
        }
    });

    const deleteMutation = useMutation({
        mutationFn: async (keyId) => {
            const res = await widgetAPI.deleteKey(keyId);
            return res.data;
        },
        onSuccess: () => {
            toast.success('Klucz usunięty!');
            queryClient.invalidateQueries(['apiKeys']);
        },
        onError: (error) => {
            toast.error(error.response?.data?.error || 'Błąd usuwania klucza');
        }
    });

    const handleDelete = (keyId, keyName) => {
        if (confirm(`Czy na pewno chcesz usunąć klucz "${keyName}"? Ta operacja jest nieodwracalna.`)) {
            deleteMutation.mutate(keyId);
        }
    };

    const handleCreate = (e) => {
        e.preventDefault();
        const name = e.target.name.value;
        createMutation.mutate(name);
        e.target.reset();
    };

    return (
        <Layout>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <h1 className="text-3xl font-bold mb-8 text-white">Zarządzanie Kluczami API</h1>

                {/* Create Key Form */}
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg mb-8">
                    <h2 className="text-xl font-semibold mb-4 text-white">Utwórz nowy klucz</h2>
                    <form onSubmit={handleCreate} className="flex gap-4">
                        <input
                            type="text"
                            name="name"
                            placeholder="Nazwa klucza (np. Strona Główna)"
                            required
                            className="flex-1 rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2"
                        />
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                            {createMutation.isPending ? 'Tworzenie...' : 'Utwórz klucz'}
                        </button>
                    </form>
                </div>

                {/* New Key Modal / Display */}
                {newKey && (
                    <div className="bg-green-900/30 border border-green-500/50 p-6 rounded-xl mb-8">
                        <h3 className="text-lg font-bold text-green-400 mb-2">🎉 Klucz utworzony pomyślnie!</h3>
                        <p className="text-slate-300 mb-4 text-sm">Skopiuj <strong>Secret Key</strong> teraz. Nie zobaczysz go ponownie.</p>

                        <div className="grid gap-4">
                            <div>
                                <label className="text-xs text-slate-400 uppercase font-bold">Public Key</label>
                                <div className="flex items-center gap-2 mt-1 bg-slate-900 rounded border border-slate-700">
                                    <code className="flex-1 p-3 text-green-300 font-mono text-sm break-all">
                                        {newKey.public_key}
                                    </code>
                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(newKey.public_key);
                                            toast.success('Public Key skopiowany!');
                                        }}
                                        className="p-2 mr-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
                                        title="Kopiuj Public Key"
                                    >
                                        <Copy className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 uppercase font-bold">Secret Key</label>
                                <div className="flex items-center gap-2 mt-1 bg-slate-900 rounded border border-red-500/30">
                                    <code className="flex-1 p-3 text-red-300 font-mono text-sm break-all">
                                        {newKey.secret_key}
                                    </code>
                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(newKey.secret_key);
                                            toast.success('Secret Key skopiowany!');
                                        }}
                                        className="p-2 mr-2 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition-colors"
                                        title="Kopiuj Secret Key"
                                    >
                                        <Copy className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={() => setNewKey(null)}
                            className="mt-4 text-sm text-slate-400 hover:text-white underline"
                        >
                            Zamknij
                        </button>
                    </div>
                )}

                {/* Keys List */}
                <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-slate-700">
                        <thead className="bg-slate-750">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Nazwa</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Public Key</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Utworzono</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Ostatnie użycie</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Akcje</th>
                            </tr>
                        </thead>
                        <tbody className="bg-slate-800 divide-y divide-slate-700">
                            {isLoading ? (
                                <tr><td colSpan="6" className="px-6 py-4 text-center text-slate-400">Ładowanie...</td></tr>
                            ) : keys?.map((key) => (
                                <tr key={key.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{key.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300 font-mono">{key.public_key} ...</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                                        {format(new Date(key.created_at), 'yyyy-MM-dd')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                                        {key.last_used_at ? format(new Date(key.last_used_at), 'yyyy-MM-dd HH:mm') : '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        {key.is_active ?
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Aktywny</span> :
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Nieaktywny</span>
                                        }
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <button
                                            onClick={() => handleDelete(key.id, key.name)}
                                            disabled={deleteMutation.isPending}
                                            className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
                                            title="Usuń klucz"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {keys?.length === 0 && (
                                <tr><td colSpan="6" className="px-6 py-4 text-center text-slate-400">Brak kluczy API. Utwórz pierwszy.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </Layout>
    );
}
