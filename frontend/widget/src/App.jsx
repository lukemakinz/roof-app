import React, { useState, useEffect } from 'react';
import UploadForm from './components/UploadForm';

const App = ({ config }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [widgetConfig, setWidgetConfig] = useState(null);
    const [loading, setLoading] = useState(true);

    // Default styles fallback
    const styles = {
        primaryColor: '#3B82F6',
        position: 'bottom-right'
    };

    useEffect(() => {
        // Fetch configuration from API
        const fetchConfig = async () => {
            try {
                const response = await fetch(`${config.apiUrl}/api/widget/config/`, {
                    headers: {
                        'X-Widget-Public-Key': config.publicKey,
                        'X-Widget-Secret-Key': config.secretKey,
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setWidgetConfig(data);
                }
            } catch (err) {
                console.error('Failed to load widget config', err);
            } finally {
                setLoading(false);
            }
        };

        fetchConfig();
    }, [config]);

    const toggleOpen = () => setIsOpen(!isOpen);

    const primaryColor = widgetConfig?.primary_color || styles.primaryColor;

    if (loading && !widgetConfig) return null; // Or skeleton

    return (
        <div className="roof-widget-root">
            {/* Trigger Button */}
            {!isOpen && (
                <button
                    className="rw-trigger-btn rw-button"
                    onClick={toggleOpen}
                    style={{
                        backgroundColor: primaryColor,
                        [widgetConfig?.position?.split('-')[0] || 'bottom']: '20px',
                        [widgetConfig?.position?.split('-')[1] || 'right']: '20px',
                    }}
                >
                    {widgetConfig?.button_text || 'Wycena dachu'}
                </button>
            )}

            {/* Modal */}
            {isOpen && (
                <div className="rw-modal-overlay">
                    <div className="rw-modal">
                        <div className="rw-header">
                            <h3 style={{ margin: 0, fontSize: '18px' }}>
                                {widgetConfig?.header_text || 'Bezpłatna wycena'}
                            </h3>
                            <button className="rw-close-btn" onClick={toggleOpen}>&times;</button>
                        </div>
                        <div className="rw-body">
                            <p style={{ marginBottom: '20px', color: '#64748b' }}>
                                {widgetConfig?.description_text}
                            </p>
                            <UploadForm
                                config={config}
                                primaryColor={primaryColor}
                                onSuccess={() => setTimeout(toggleOpen, 3000)}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default App;
