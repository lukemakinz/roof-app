import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import Layout from '../components/Layout';

export default function WidgetConfigPage() {
    const { token } = useAuthStore();
    const queryClient = useQueryClient();

    const [formState, setFormState] = useState({
        primary_color: '#3B82F6',
        position: 'bottom-right',
        header_text: '',
        button_text: '',
        description_text: ''
    });

    const { data: config, isLoading } = useQuery({
        queryKey: ['widgetConfig'],
        queryFn: async () => {
            const res = await fetch('http://localhost:8000/api/widget/dashboard/config/', {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to load config');
            return res.json();
        }
    });

    useEffect(() => {
        if (config) {
            setFormState({
                primary_color: config.primary_color || '#3B82F6',
                position: config.position || 'bottom-right',
                header_text: config.header_text || '',
                button_text: config.button_text || '',
                description_text: config.description_text || ''
            });
        }
    }, [config]);

    const mutation = useMutation({
        mutationFn: async (newData) => {
            const res = await fetch('http://localhost:8000/api/widget/dashboard/config/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(newData)
            });
            if (!res.ok) throw new Error('Failed to update config');
            return res.json();
        },
        onSuccess: () => {
            toast.success('Konfiguracja zapisana!');
            queryClient.invalidateQueries(['widgetConfig']);
        }
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormState(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        mutation.mutate(formState);
    };

    if (isLoading) return <div className="p-8 text-white">Ładowanie...</div>;

    // Helper to calculate preview styles
    const [vPos, hPos] = formState.position ? formState.position.split('-') : ['bottom', 'right'];

    // Offset the open widget box so it doesn't overlap the launcher button
    // If bottom-* -> bottom: 90px
    // If top-* -> top: 90px
    const openWidgetStyle = {
        position: 'absolute',
        [vPos]: '90px',
        [hPos]: '20px',
        borderTop: `4px solid ${formState.primary_color}`,
        zIndex: 5
    };

    const launcherButtonStyle = {
        position: 'absolute',
        backgroundColor: formState.primary_color,
        [vPos]: '20px',
        [hPos]: '20px',
        zIndex: 10
    };

    return (
        <Layout>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <h1 className="text-3xl font-bold mb-8 text-white">Konfiguracja Widgetu</h1>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Form */}
                    <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Kolor główny</label>
                                <div className="flex gap-2">
                                    <input
                                        type="color"
                                        name="primary_color"
                                        value={formState.primary_color}
                                        onChange={handleChange}
                                        className="h-10 w-20 rounded border border-slate-600 bg-slate-700 p-1 cursor-pointer"
                                    />
                                    <input
                                        type="text"
                                        name="primary_color"
                                        value={formState.primary_color}
                                        onChange={handleChange}
                                        className="flex-1 rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Pozycja</label>
                                <select
                                    name="position"
                                    value={formState.position}
                                    onChange={handleChange}
                                    className="w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                                >
                                    <option value="bottom-right">Dolny prawy</option>
                                    <option value="bottom-left">Dolny lewy</option>
                                    <option value="top-right">Górny prawy</option>
                                    <option value="top-left">Górny lewy</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Tekst nagłówka</label>
                                <input
                                    type="text"
                                    name="header_text"
                                    value={formState.header_text}
                                    onChange={handleChange}
                                    className="w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Tekst przycisku</label>
                                <input
                                    type="text"
                                    name="button_text"
                                    value={formState.button_text}
                                    onChange={handleChange}
                                    className="w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Opis</label>
                                <textarea
                                    name="description_text"
                                    value={formState.description_text}
                                    onChange={handleChange}
                                    rows={3}
                                    className="w-full rounded-md border-slate-600 bg-slate-700 text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2"
                                />
                            </div>

                            <div className="pt-4">
                                <button
                                    type="submit"
                                    disabled={mutation.isPending}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                                >
                                    {mutation.isPending ? 'Zapisywanie...' : 'Zapisz zmiany'}
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Preview */}
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden relative min-h-[500px] border-4 border-slate-200">
                        <div className="absolute inset-0 bg-gray-50 flex items-center justify-center text-gray-300 font-bold text-3xl">
                            Podgląd
                        </div>

                        {/* Open Widget Preview */}
                        <div
                            className="bg-white rounded-lg shadow-2xl p-4 w-72"
                            style={openWidgetStyle}
                        >
                            <div className="font-bold text-gray-900 mb-2">{formState.header_text || 'Przykładowy nagłówek'}</div>
                            <div className="text-sm text-gray-600 mb-4">{formState.description_text || 'Przykładowy opis zachęcający do kontaktu.'}</div>

                            {/* Mock Inputs */}
                            <div className="space-y-3 mb-4 text-left">
                                <div>
                                    <label className="block text-xs font-semibold text-gray-700 mb-1">Email</label>
                                    <input disabled type="email" className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 bg-gray-50 text-gray-400 cursor-not-allowed" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-700 mb-1">Telefon</label>
                                    <input disabled type="tel" className="w-full text-sm border border-gray-300 rounded px-2 py-1.5 bg-gray-50 text-gray-400 cursor-not-allowed" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-700 mb-1">Zdjęcie dachu / Rzut</label>
                                    <div className="w-full text-sm border border-dashed border-gray-300 rounded px-2 py-2 bg-gray-50 text-gray-400 text-center cursor-not-allowed">
                                        Wybierz plik (PNG, JPG, PDF)
                                    </div>
                                </div>
                            </div>

                            <button
                                className="w-full py-2 px-4 rounded text-white font-medium text-sm transition-opacity hover:opacity-90"
                                style={{ backgroundColor: formState.primary_color }}
                            >
                                Wyślij
                            </button>
                        </div>

                        {/* Launcher Button Preview */}
                        <button
                            className="px-6 py-3 rounded-full text-white font-bold shadow-lg transition-transform hover:scale-105"
                            style={launcherButtonStyle}
                        >
                            {formState.button_text || 'Wycena'}
                        </button>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
