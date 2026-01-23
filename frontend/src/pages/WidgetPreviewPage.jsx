import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { ArrowLeft, Home, Zap, Shield, Phone, Mail, MapPin } from 'lucide-react';

export default function WidgetPreviewPage() {
    const [searchParams] = useSearchParams();
    const [isWidgetOpen, setIsWidgetOpen] = useState(false);

    // Get widget config from URL params
    const config = {
        primaryColor: searchParams.get('color') || '#3B82F6',
        position: searchParams.get('position') || 'bottom-right',
        headerText: searchParams.get('header') || 'Bezpłatna wycena',
        buttonText: searchParams.get('button') || 'Wycena dachu',
        descriptionText: searchParams.get('description') || 'Prześlij zdjęcie lub rzut dachu, a my przygotujemy dla Ciebie bezpłatną wycenę.'
    };

    const [vPos, hPos] = config.position.split('-');

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            {/* Back to config link */}
            <div className="fixed top-4 left-4 z-50">
                <Link
                    to="/widget-config"
                    className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-lg text-slate-700 hover:bg-slate-50 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Powrót do konfiguracji
                </Link>
            </div>

            {/* Hero Section */}
            <section className="relative overflow-hidden bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIyIi8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
                <div className="max-w-6xl mx-auto px-6 py-24 relative">
                    <div className="flex items-center gap-3 mb-6">
                        <Home className="w-10 h-10" />
                        <span className="text-2xl font-bold">DachPro</span>
                    </div>
                    <h1 className="text-5xl font-bold mb-6 leading-tight">
                        Profesjonalne pokrycia<br />dachowe dla Twojego domu
                    </h1>
                    <p className="text-xl text-blue-100 mb-8 max-w-2xl">
                        Od 15 lat budujemy dachy, które chronią polskie domy.
                        Zaufaj ekspertom i zyskaj spokój na lata.
                    </p>
                    <div className="flex gap-4">
                        <button className="px-8 py-4 bg-white text-blue-600 rounded-xl font-bold hover:bg-blue-50 transition-colors shadow-lg">
                            Zobacz ofertę
                        </button>
                        <button className="px-8 py-4 bg-blue-500/30 text-white rounded-xl font-bold hover:bg-blue-500/40 transition-colors border border-white/20">
                            Kontakt
                        </button>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-white">
                <div className="max-w-6xl mx-auto px-6">
                    <h2 className="text-3xl font-bold text-center text-slate-800 mb-4">
                        Dlaczego my?
                    </h2>
                    <p className="text-slate-600 text-center mb-12 max-w-2xl mx-auto">
                        Wybierz sprawdzonego partnera do budowy dachu
                    </p>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100">
                            <div className="w-14 h-14 rounded-xl bg-blue-500 flex items-center justify-center mb-6">
                                <Zap className="w-7 h-7 text-white" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-3">Szybka realizacja</h3>
                            <p className="text-slate-600">
                                Realizujemy projekty w ekspresowym tempie bez kompromisów w jakości.
                            </p>
                        </div>
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100">
                            <div className="w-14 h-14 rounded-xl bg-emerald-500 flex items-center justify-center mb-6">
                                <Shield className="w-7 h-7 text-white" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-3">Gwarancja jakości</h3>
                            <p className="text-slate-600">
                                10-letnia gwarancja na wszystkie wykonane prace i materiały.
                            </p>
                        </div>
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100">
                            <div className="w-14 h-14 rounded-xl bg-amber-500 flex items-center justify-center mb-6">
                                <Home className="w-7 h-7 text-white" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-3">Doświadczenie</h3>
                            <p className="text-slate-600">
                                Ponad 2000 zrealizowanych projektów na terenie całej Polski.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Contact Section */}
            <section className="py-20 bg-slate-800 text-white">
                <div className="max-w-6xl mx-auto px-6">
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div>
                            <h2 className="text-3xl font-bold mb-6">Skontaktuj się z nami</h2>
                            <p className="text-slate-300 mb-8">
                                Masz pytania? Chętnie odpowiemy na wszystkie Twoje wątpliwości.
                            </p>
                            <div className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                                        <Phone className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-400">Telefon</div>
                                        <div className="font-semibold">+48 123 456 789</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                                        <Mail className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-400">Email</div>
                                        <div className="font-semibold">kontakt@dachpro.pl</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center">
                                        <MapPin className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-400">Adres</div>
                                        <div className="font-semibold">ul. Dachowa 15, 00-001 Warszawa</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-slate-700 rounded-2xl p-8">
                            <h3 className="text-xl font-bold mb-6">Wyślij wiadomość</h3>
                            <form className="space-y-4">
                                <input
                                    type="text"
                                    placeholder="Imię i nazwisko"
                                    className="w-full px-4 py-3 rounded-lg bg-slate-600 border border-slate-500 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                                />
                                <input
                                    type="email"
                                    placeholder="Email"
                                    className="w-full px-4 py-3 rounded-lg bg-slate-600 border border-slate-500 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400"
                                />
                                <textarea
                                    placeholder="Wiadomość"
                                    rows={4}
                                    className="w-full px-4 py-3 rounded-lg bg-slate-600 border border-slate-500 text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 resize-none"
                                />
                                <button
                                    type="button"
                                    className="w-full py-3 bg-blue-500 text-white rounded-lg font-bold hover:bg-blue-600 transition-colors"
                                >
                                    Wyślij
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </section>

            {/* Interactive Widget Preview */}
            <div
                className="fixed z-40"
                style={{
                    [vPos]: '20px',
                    [hPos]: '20px'
                }}
            >
                {/* Widget Button - visible when widget is closed */}
                {!isWidgetOpen && (
                    <button
                        onClick={() => setIsWidgetOpen(true)}
                        className="px-6 py-3 rounded-full text-white font-bold shadow-2xl transition-all hover:scale-105 hover:shadow-xl"
                        style={{ backgroundColor: config.primaryColor }}
                    >
                        {config.buttonText}
                    </button>
                )}
            </div>

            {/* Widget Modal - visible when widget is open */}
            {isWidgetOpen && (
                <div
                    className="fixed z-30 bg-white rounded-xl shadow-2xl w-80 overflow-hidden"
                    style={{
                        [vPos]: '20px',
                        [hPos]: '20px',
                        borderTop: `4px solid ${config.primaryColor}`
                    }}
                >
                    <div className="p-4">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="font-bold text-gray-900">{config.headerText}</h3>
                            <button
                                onClick={() => setIsWidgetOpen(false)}
                                className="text-gray-400 hover:text-gray-600 text-2xl leading-none transition-colors"
                            >
                                &times;
                            </button>
                        </div>
                        <p className="text-sm text-gray-600 mb-4">{config.descriptionText}</p>

                        <div className="space-y-3 mb-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    className="w-full text-sm border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:border-blue-400"
                                    placeholder="twoj@email.pl"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-700 mb-1">Telefon</label>
                                <input
                                    type="tel"
                                    className="w-full text-sm border border-gray-300 rounded px-3 py-2 text-gray-900 focus:outline-none focus:border-blue-400"
                                    placeholder="+48 123 456 789"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-700 mb-1">Zdjęcie dachu / Rzut</label>
                                <div className="w-full text-sm border border-dashed border-gray-300 rounded px-3 py-4 text-gray-400 text-center cursor-pointer hover:border-gray-400 transition-colors">
                                    Wybierz plik (PNG, JPG, PDF)
                                </div>
                            </div>
                        </div>

                        <button
                            className="w-full py-3 rounded-lg text-white font-medium transition-opacity hover:opacity-90"
                            style={{ backgroundColor: config.primaryColor }}
                        >
                            Wyślij
                        </button>
                    </div>
                </div>
            )}

            {/* Info badge */}
            <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white px-6 py-3 rounded-full shadow-lg z-50">
                <span className="text-sm">
                    👆 Kliknij przycisk "{config.buttonText}" aby otworzyć/zamknąć widget
                </span>
            </div>
        </div>
    );
}
