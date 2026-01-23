import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import Layout from '../components/Layout';
import { Eye, Code, Copy, X } from 'lucide-react';
import { widgetAPI } from '../lib/api';

export default function WidgetConfigPage() {
    const { token } = useAuthStore();
    const queryClient = useQueryClient();
    const [showInstallModal, setShowInstallModal] = useState(false);

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
            const res = await widgetAPI.getConfig();
            return res.data;
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
            const res = await widgetAPI.updateConfig(newData);
            return res.data;
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

                            <div className="pt-4 space-y-3">
                                <button
                                    type="submit"
                                    disabled={mutation.isPending}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                                >
                                    {mutation.isPending ? 'Zapisywanie...' : 'Zapisz zmiany'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        const params = new URLSearchParams({
                                            color: formState.primary_color,
                                            position: formState.position,
                                            header: formState.header_text,
                                            button: formState.button_text,
                                            description: formState.description_text
                                        });
                                        window.open(`/widget-preview?${params.toString()}`, '_blank');
                                    }}
                                    className="w-full flex items-center justify-center gap-2 py-2 px-4 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-slate-300 bg-slate-700 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                                >
                                    <Eye className="w-4 h-4" />
                                    Podgląd na stronie
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowInstallModal(true)}
                                    className="w-full flex items-center justify-center gap-2 py-2 px-4 border border-emerald-600 rounded-md shadow-sm text-sm font-medium text-emerald-300 bg-emerald-900/30 hover:bg-emerald-800/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500"
                                >
                                    <Code className="w-4 h-4" />
                                    Instrukcja instalacji
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

            {/* Installation Modal */}
            {showInstallModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-auto">
                        <div className="flex items-center justify-between p-6 border-b border-slate-700">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Code className="w-5 h-5 text-emerald-400" />
                                Instrukcja instalacji widgetu
                            </h2>
                            <button
                                onClick={() => setShowInstallModal(false)}
                                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-slate-400" />
                            </button>
                        </div>
                        <div className="p-6 space-y-6">
                            <div>
                                <h3 className="text-sm font-semibold text-slate-300 mb-2">1. Skopiuj poniższy kod</h3>
                                <p className="text-sm text-slate-400 mb-3">
                                    Wklej ten kod przed zamykającym tagiem <code className="bg-slate-700 px-1.5 py-0.5 rounded text-emerald-400">&lt;/body&gt;</code> na swojej stronie:
                                </p>
                                <div className="relative">
                                    <pre className="bg-slate-900 rounded-lg p-4 text-sm text-slate-300 overflow-x-auto border border-slate-700">
                                        <code>{`<!-- Konfiguracja Widgetu RoofQuote -->
<script>
    window.RoofWidgetConfig = {
        publicKey: '${config?.public_key || 'TU_WKLEJ_PUBLIC_KEY'}',
        secretKey: '${config?.secret_key || 'TU_WKLEJ_SECRET_KEY'}',
    };
</script>
<!-- Skrypt ładujący -->
<script src="http://localhost:5173/widget/loader.js" async></script>`}</code>
                                    </pre>
                                    <button
                                        onClick={() => {
                                            const code = `<!-- Konfiguracja Widgetu RoofQuote -->
<script>
    window.RoofWidgetConfig = {
        publicKey: '${config?.public_key || 'TU_WKLEJ_PUBLIC_KEY'}',
        secretKey: '${config?.secret_key || 'TU_WKLEJ_SECRET_KEY'}',
    };
</script>
<!-- Skrypt ładujący -->
<script src="http://localhost:5173/widget/loader.js" async></script>`;
                                            navigator.clipboard.writeText(code);
                                            toast.success('Kod skopiowany!');
                                        }}
                                        className="absolute top-2 right-2 p-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                                        title="Kopiuj kod"
                                    >
                                        <Copy className="w-4 h-4 text-slate-300" />
                                    </button>
                                </div>
                            </div>
                            <div>
                                <h3 className="text-sm font-semibold text-slate-300 mb-2">2. Pobierz klucze API</h3>
                                <p className="text-sm text-slate-400 mb-3">
                                    Przejdź do sekcji <strong className="text-white">"Klucze API"</strong> w menu bocznym, aby wygenerować klucze dla swojego widgetu.
                                </p>
                                <div className="bg-amber-900/30 border border-amber-700/50 rounded-lg p-3">
                                    <p className="text-sm text-amber-200/80">
                                        <strong className="text-amber-300">⚠️ Bezpieczeństwo:</strong> Klucze API są wyświetlane tylko raz podczas tworzenia.
                                        Zapisz je w bezpiecznym miejscu zaraz po wygenerowaniu.
                                    </p>
                                </div>
                            </div>
                            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
                                <h3 className="text-sm font-semibold text-blue-300 mb-1">💡 Wskazówka</h3>
                                <p className="text-sm text-blue-200/80">
                                    Widget automatycznie pobierze konfigurację (kolory, teksty, pozycję) z serwera.
                                    Możesz ją zmienić w dowolnym momencie bez modyfikacji kodu na stronie.
                                </p>
                            </div>
                        </div>
                        <div className="p-6 border-t border-slate-700">
                            <button
                                onClick={() => setShowInstallModal(false)}
                                className="w-full py-2.5 px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
                            >
                                Zamknij
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </Layout>
    );
}
