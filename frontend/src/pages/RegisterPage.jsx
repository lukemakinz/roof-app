import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Home, Mail, Lock, Eye, EyeOff, User, Phone, ArrowRight, Loader2 } from 'lucide-react';

export default function RegisterPage() {
    const navigate = useNavigate();
    const { register, isLoading, error, clearError } = useAuthStore();
    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        password_confirm: '',
        first_name: '',
        last_name: '',
        phone: '',
    });
    const [showPassword, setShowPassword] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        clearError();
        const result = await register(formData);
        if (result.success) {
            navigate('/');
        }
    };

    return (
        <div className="min-h-screen flex mesh-bg">
            {/* Left Panel - Branding */}
            <div className="hidden lg:flex lg:w-1/2 xl:w-2/5 flex-col justify-between p-12 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-brand-600/20 to-purple-600/10" />

                <div className="relative z-10">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-brand-500 flex items-center justify-center">
                            <Home className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-2xl font-bold text-white">RoofQuote</span>
                    </div>
                </div>

                <div className="relative z-10 space-y-6">
                    <h1 className="text-4xl xl:text-5xl font-bold text-white leading-tight">
                        Dołącz do<br />
                        <span className="gradient-text">profesjonalistów</span>
                    </h1>
                    <p className="text-lg text-dark-300 max-w-md">
                        Załóż konto i zacznij generować profesjonalne wyceny dachów
                        szybciej niż kiedykolwiek.
                    </p>

                    <div className="space-y-4 pt-4">
                        <div className="flex items-center gap-3 text-dark-200">
                            <div className="w-6 h-6 rounded-full bg-success-500/20 flex items-center justify-center">
                                <span className="text-success-400 text-sm">✓</span>
                            </div>
                            AI analizuje zdjęcia rzutów w sekundach
                        </div>
                        <div className="flex items-center gap-3 text-dark-200">
                            <div className="w-6 h-6 rounded-full bg-success-500/20 flex items-center justify-center">
                                <span className="text-success-400 text-sm">✓</span>
                            </div>
                            Automatyczne kalkulacje materiałów
                        </div>
                        <div className="flex items-center gap-3 text-dark-200">
                            <div className="w-6 h-6 rounded-full bg-success-500/20 flex items-center justify-center">
                                <span className="text-success-400 text-sm">✓</span>
                            </div>
                            Profesjonalne oferty PDF jednym kliknięciem
                        </div>
                    </div>
                </div>

                <div className="relative z-10 text-dark-500 text-sm">
                    © 2026 RoofQuote. Wszelkie prawa zastrzeżone.
                </div>
            </div>

            {/* Right Panel - Register Form */}
            <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
                <div className="w-full max-w-md space-y-6 animate-fade-in py-8">
                    {/* Mobile Logo */}
                    <div className="flex lg:hidden items-center justify-center gap-3 mb-8">
                        <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
                            <Home className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold text-white">RoofQuote</span>
                    </div>

                    <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold text-white">Utwórz konto</h2>
                        <p className="mt-2 text-dark-400">
                            Wypełnij formularz, aby rozpocząć
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {error && (
                            <div className="p-4 bg-error-500/10 border border-error-500/20 rounded-xl text-error-400 text-sm animate-slide-up">
                                {error}
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="first_name" className="label-text">
                                    Imię
                                </label>
                                <input
                                    id="first_name"
                                    name="first_name"
                                    type="text"
                                    value={formData.first_name}
                                    onChange={handleChange}
                                    className="input-field"
                                    placeholder="Jan"
                                />
                            </div>
                            <div>
                                <label htmlFor="last_name" className="label-text">
                                    Nazwisko
                                </label>
                                <input
                                    id="last_name"
                                    name="last_name"
                                    type="text"
                                    value={formData.last_name}
                                    onChange={handleChange}
                                    className="input-field"
                                    placeholder="Kowalski"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="email" className="label-text">
                                Email *
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className="input-field pl-12"
                                    placeholder="jan@firma.pl"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="username" className="label-text">
                                Nazwa użytkownika *
                            </label>
                            <div className="relative">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    id="username"
                                    name="username"
                                    type="text"
                                    value={formData.username}
                                    onChange={handleChange}
                                    className="input-field pl-12"
                                    placeholder="jan.kowalski"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="phone" className="label-text">
                                Telefon
                            </label>
                            <div className="relative">
                                <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    id="phone"
                                    name="phone"
                                    type="tel"
                                    value={formData.phone}
                                    onChange={handleChange}
                                    className="input-field pl-12"
                                    placeholder="+48 123 456 789"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="label-text">
                                Hasło *
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    id="password"
                                    name="password"
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password}
                                    onChange={handleChange}
                                    className="input-field pl-12 pr-12"
                                    placeholder="••••••••"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password_confirm" className="label-text">
                                Potwierdź hasło *
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                <input
                                    id="password_confirm"
                                    name="password_confirm"
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password_confirm}
                                    onChange={handleChange}
                                    className="input-field pl-12"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn-primary w-full flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Zarejestruj się
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="text-center text-dark-400">
                        Masz już konto?{' '}
                        <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">
                            Zaloguj się
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
