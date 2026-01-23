import Layout from '../components/Layout';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
    return (
        <Layout>
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-12 h-12 rounded-xl bg-brand-500/20 flex items-center justify-center">
                        <Settings className="w-6 h-6 text-brand-400" />
                    </div>
                    <h1 className="text-3xl font-bold text-white">Ustawienia</h1>
                </div>

                <div className="glass rounded-2xl border border-dark-700/50 p-8">
                    <div className="text-center py-12">
                        <Settings className="w-16 h-16 text-dark-500 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-dark-300 mb-2">
                            Ustawienia będą dostępne wkrótce
                        </h2>
                        <p className="text-dark-400">
                            Tutaj będziesz mógł zarządzać swoim kontem, powiadomieniami i preferencjami.
                        </p>
                    </div>
                </div>
            </div>
        </Layout>
    );
}
