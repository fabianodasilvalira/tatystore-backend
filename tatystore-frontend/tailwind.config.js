/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        "./pages/**/*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}",
        "./app/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: {
                    50: 'var(--color-primary-50, #F5F3FF)',
                    100: 'var(--color-primary-100, #EDE9FE)',
                    300: 'var(--color-primary-300, #C4B5FD)',
                    600: 'var(--color-primary-600, #7C3AED)',
                    700: 'var(--color-primary-700, #6D28D9)',
                },
            },
        },
    },
    plugins: [],
}
