import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
    plugins: [react()],
    root: 'frontend/widget', // Set root to widget dir if running from there, OR correct paths if running from root.
    // We will run this config from the PROJECT ROOT (frontend/), so keys should be relative to it.
    // Actually, if we run `vite build -c frontend/widget/vite.config.js`, vite treats CWD as root unless specified.

    // Let's assume we run from `frontend/` directory.
    // We need to resolve paths correctly.

    build: {
        outDir: '../../dist-widget', // Relative to frontend/widget/ if root is set there? 
        // If I don't set root, `frontend/widget/src/main.jsx` is the entry.
        emptyOutDir: true,
        lib: {
            entry: path.resolve(__dirname, 'src/main.jsx'),
            name: 'RoofWidget',
            fileName: 'roof-widget',
            formats: ['iife'], // Standalone script
        },
        rollupOptions: {
            output: {
                assetFileNames: 'roof-widget.[ext]',
                // Ensure globals if submitting to window? iife puts it in window.RoofWidget
                globals: {
                    react: 'React',
                    'react-dom': 'ReactDOM'
                }
                // Wait, if I want it standalone, I SHOULD bundle React! 
                // Standard widget practice: Bundle everything OR require user to provide React.
                // PRD says: "Instalacja przez 1 tag <script>". 
                // So we MUST bundle React.
            },
            // Do NOT externalize react if we want a standalone widget.
            external: [],
        },
    },
    define: {
        'process.env': {} // Fix for some libs expecting process.env
    }
});
