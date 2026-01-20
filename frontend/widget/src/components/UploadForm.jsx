import React, { useState } from 'react';

const UploadForm = ({ config, primaryColor, onSuccess }) => {
    const [formData, setFormData] = useState({
        email: '',
        phone: '',
        file: null
    });
    const [status, setStatus] = useState('idle'); // idle, submitting, success, error
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('submitting');

        const data = new FormData();
        data.append('email', formData.email);
        data.append('phone', formData.phone);
        if (formData.file) {
            data.append('file', formData.file);
        }

        try {
            const response = await fetch(`${config.apiUrl}/api/widget/submit/`, {
                method: 'POST',
                headers: {
                    'X-Widget-Public-Key': config.publicKey,
                    'X-Widget-Secret-Key': config.secretKey,
                },
                body: data
            });

            const result = await response.json();

            if (response.ok) {
                setStatus('success');
                setMessage(result.message || 'Wysłano pomyślnie!');
                if (onSuccess) onSuccess();
            } else {
                setStatus('error');
                setMessage(result.error || 'Wystąpił błąd.');
            }
        } catch (err) {
            setStatus('error');
            setMessage('Błąd połączenia.');
        }
    };

    const handleChange = (e) => {
        const { name, value, files } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: files ? files[0] : value
        }));
    };

    if (status === 'success') {
        return (
            <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '48px', color: '#10b981', marginBottom: '16px' }}>✓</div>
                <h4 style={{ margin: '0 0 8px 0' }}>Dziękujemy!</h4>
                <p>{message}</p>
                <p style={{ fontSize: '12px', color: '#64748b' }}>Sprawdź swoją skrzynkę mailową.</p>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', fontWeight: 600 }}>Email</label>
                <input
                    type="email"
                    name="email"
                    required
                    className="rw-input"
                    value={formData.email}
                    onChange={handleChange}
                />
            </div>

            <div>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', fontWeight: 600 }}>Telefon</label>
                <input
                    type="tel"
                    name="phone"
                    required
                    className="rw-input"
                    value={formData.phone}
                    onChange={handleChange}
                />
            </div>

            <div>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', fontWeight: 600 }}>Zdjęcie dachu / Rzut</label>
                <input
                    type="file"
                    name="file"
                    required
                    accept="image/*,.pdf"
                    className="rw-input"
                    onChange={handleChange}
                    style={{ padding: '6px' }}
                />
            </div>

            {status === 'error' && (
                <div style={{ color: '#ef4444', marginBottom: '12px', fontSize: '14px' }}>
                    {message}
                </div>
            )}

            <button
                type="submit"
                className="rw-submit-btn rw-button"
                disabled={status === 'submitting'}
                style={{ backgroundColor: primaryColor }}
            >
                {status === 'submitting' ? 'Wysyłanie...' : 'Wyślij do wyceny'}
            </button>
        </form>
    );
};

export default UploadForm;
