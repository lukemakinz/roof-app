import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Home, Mail, Lock, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const navigate = useNavigate();
    const { login, isLoading, error, clearError } = useAuthStore();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        clearError();
        const result = await login(email, password);
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
                        Profesjonalne wyceny<br />
                        <span className="gradient-text">w 2 minuty</span>
                    </h1>
                    <p className="text-lg text-dark-300 max-w-md">
                        Wykorzystaj AI do ekstrakcji wymiarów z rzutów dachów i generuj
                        profesjonalne oferty PDF automatycznie.
                    </p>

                    <div className="flex gap-8 pt-4">
                        <div>
                            <div className="text-3xl font-bold text-white">70%</div>
                            <div className="text-dark-400 text-sm">Szybsze wyceny</div>
                        </div>
                        <div>
                            <div className="text-3xl font-bold text-white">500+</div>
                            <div className="text-dark-400 text-sm">Wygenerowanych ofert</div>
                        </div>
                    </div>
                </div>

                <div className="relative z-10 text-dark-500 text-sm">
                    © 2026 RoofQuote. Wszelkie prawa zastrzeżone.
                </div>
            </div>

            {/* Right Panel - Login Form */}
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="w-full max-w-md space-y-8 animate-fade-in">
                    {/* Mobile Logo */}
                    <div className="flex lg:hidden items-center justify-center gap-3 mb-8">
                        <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
                            <Home className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold text-white">RoofQuote</span>
                    </div>

                    <div className="text-center lg:text-left">
                        <h2 className="text-3xl font-bold text-white">Witaj ponownie</h2>
                        <p className="mt-2 text-dark-400">
                            Zaloguj się do swojego konta
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-4 bg-error-500/10 border border-error-500/20 rounded-xl text-error-400 text-sm animate-slide-up">
                                {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label htmlFor="email" className="label-text">
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                    <input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="input-field pl-12"
                                        placeholder="jan@firma.pl"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label htmlFor="password" className="label-text">
                                    Hasło
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
                                    <input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
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
                        </div>

                        <div className="flex items-center justify-between">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-brand-500 focus:ring-brand-500"
                                />
                                <span className="text-sm text-dark-400">Zapamiętaj mnie</span>
                            </label>
                            <Link to="/forgot-password" className="text-sm text-brand-400 hover:text-brand-300">
                                Zapomniałeś hasła?
                            </Link>
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
                                    Zaloguj się
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="text-center text-dark-400">
                        Nie masz konta?{' '}
                        <Link to="/register" className="text-brand-400 hover:text-brand-300 font-medium">
                            Zarejestruj się
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
