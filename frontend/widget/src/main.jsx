import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/widget.css';

// Expose initialization function
window.RoofWidget = {
    init: function (config) {
        const container = document.querySelector(config.container);
        if (!container) {
            console.error('RoofWidget: Container not found', config.container);
            return;
        }

        const root = ReactDOM.createRoot(container);
        root.render(
            <React.StrictMode>
                <App config={config} />
            </React.StrictMode>
        );
    }
};
