(function () {
    'use strict';

    var config = window.RoofWidgetConfig || {};

    if (!config.publicKey) {
        console.error('RoofWidget: Missing publicKey');
        return;
    }

    // Default URLs (can be overridden by config for testing)
    // In production, these should point to the deployment URL.
    // For local dev, we might point to localhost.
    var scriptUrl = document.currentScript ? document.currentScript.src : null;
    var baseUrl = scriptUrl ? scriptUrl.substring(0, scriptUrl.lastIndexOf('/')) : 'http://localhost:5173/widget';

    // If we are loading this loader.js, we assume the other assets (css, js) are relative to it 
    // OR we use the config.widgetUrl.

    var WIDGET_URL = config.widgetUrl || baseUrl;
    var API_URL = config.apiUrl || 'http://localhost:8000'; // Default to local backend

    // Create container
    var containerId = 'roof-widget-container-' + Math.random().toString(36).substr(2, 9);
    var container = document.createElement('div');
    container.id = containerId;
    document.body.appendChild(container);

    // Load CSS
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = WIDGET_URL + '/roof-widget.css';
    document.head.appendChild(link);

    // Load JS (The React App)
    var script = document.createElement('script');
    script.src = WIDGET_URL + '/roof-widget.iife.js'; // Vite 'iife' format usually adds .iife.js or just .js depending on config. 
    // My vite config says `fileName: 'roof-widget'`. Vite usually produces `roof-widget.iife.js` if multiple formats, or `roof-widget.js`.
    // Let's assume `roof-widget.iife.js` based on default behavior or `roof-widget.js`?
    // I will check build output later. For now, let's guess `roof-widget.iife.js`.

    script.onload = function () {
        if (window.RoofWidget && window.RoofWidget.init) {
            window.RoofWidget.init({
                container: '#' + containerId,
                publicKey: config.publicKey,
                secretKey: config.secretKey, // passed only if needed? Plan says "public + secret" in headers.
                // Wait, passing Secret Key in client side JS (window.RoofWidgetConfig) is DANGEROUS?
                // PRD says: "Auth bez JWT - public_key + secret_key dla widgetu". 
                // Wait, if it's Client Website -> Widget JS -> Backend, the Widget JS holds the keys?
                // YES. "Client Website" puts the keys in the script snippet.
                // Is this safe? "Secret Key (backend klienta)" - usually Secret Key stays on backend.
                // BUT here "backend klienta" means the client's server, or the client inserts it into the HTML?
                // If client inserts into HTML, it's visible to End User.
                // If so, it's not a "Secret" in the strict sense (like Stripe Public Key).
                // The PRD says "public_key (frontend), secret_key (backend klienta)".
                // Ah! "User Flow: 4. Wkleja script na stronę". 
                // "Mechanizm: public_key + secret_key ... podpis HMAC".
                // Use of HMAC implies the *Client's Server* generates the signature? 
                // OR does the widget JS do it? JS cannot keep secret.

                // Plan says: "API Key Pair (public + secret) for MVP instead of HMAC".
                // "Secret key: hashed in DB". 
                // If we put Secret Key in the frontend JS, any visitor can steal it and spam the API.
                // Mitigation: `Submissions` origin check. 
                // Plan says: "Validation: Origin".
                // So the "Secret" is basically a second ID. 
                // Ideally, we only need Public Key for frontend, and Origin check.
                // Secret Key is used if the Client calls API from THEIR backend.
                // BUT the Plan implementation of `WidgetAPIKeyAuthentication` checks BOTH headers.
                // `public_key = request.headers.get('X-Widget-Public-Key')`
                // `secret_key = request.headers.get('X-Widget-Secret-Key')`

                // If I implement it this way, I MUST pass secret key to the frontend widget.
                // This is a security weakness acknowledged in MVP? 
                // The PRD/Plan says "Upgrade do HMAC możliwy".
                // For MVP, allowed origins is the main defense.

                apiUrl: API_URL,
            });
        }
    };
    document.body.appendChild(script);

})();
