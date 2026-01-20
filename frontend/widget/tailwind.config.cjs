/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [],
    // Use a prefix to avoid collision with site styles?
    // Or scoped CSS handled by shadow DOM or just unique classes?
    // We used `rw-` classes and scoped container.
    // Tailwind adds reset by default (preflight). We might want to disable preflight for widget to not break host site!
    corePlugins: {
        preflight: false,
    },
    // Prefix for utility classes?
    // If we assume we embed css, we might affect host site if they use tailwind too!
    // Prefix 'rw-' is good practice.
    prefix: 'rw-',
}
