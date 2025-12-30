import React from 'react';
import { useOutletContext } from 'react-router-dom';

interface SettingsContext {
    themeColor: string;
    setThemeColor: (color: string) => void; // This will now be handleThemeChange
    themeMode: 'light' | 'dark';
    toggleThemeMode: () => void;
}

const themeOptions = [
    { name: 'Púrpura', value: 'purple', hex: '#8B5CF6' },
    { name: 'Azul', value: 'blue', hex: '#3B82F6' },
    { name: 'Verde', value: 'green', hex: '#22C55E' },
    { name: 'Rosa', value: 'pink', hex: '#EC4899' },
    { name: 'Branco', value: 'white', hex: '#ffffff' },
    { name: 'Preto', value: 'black', hex: '#111827' },
];

const Settings: React.FC = () => {
    const { themeColor, setThemeColor, themeMode, toggleThemeMode } = useOutletContext<SettingsContext>();
    return (
        <div className="space-y-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">Aparência do Tema</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">Selecione a cor principal do sistema para personalizar sua experiência.</p>
                <div className="flex flex-wrap gap-4">
                    {themeOptions.map(option => (
                        <button
                            key={option.value}
                            onClick={() => setThemeColor(option.value)}
                            className={`flex items-center gap-3 p-4 border-2 rounded-lg transition-all w-full sm:w-auto ${
                                themeColor === option.value 
                                ? `border-primary-600 shadow-lg ring-2 ring-primary-100 dark:ring-primary-700/50` 
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500'
                            }`}
                        >
                            <div className="w-8 h-8 rounded-full border dark:border-gray-600" style={{ backgroundColor: option.hex }}></div>
                            <span className="font-semibold text-lg text-gray-700 dark:text-gray-200">{option.name}</span>
                            {themeColor === option.value && (
                                <span className="material-symbols-outlined text-green-500 ml-auto">check_circle</span>
                            )}
                        </button>
                    ))}
                </div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">Modo de Exibição</h2>
                 <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium">Modo Escuro</p>
                        <p className="text-gray-600 dark:text-gray-300 text-sm">Reduza o brilho da tela para uma visualização mais confortável à noite.</p>
                    </div>
                    <button onClick={toggleThemeMode} className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${themeMode === 'dark' ? 'bg-primary-600' : 'bg-gray-300'}`}>
                        <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${themeMode === 'dark' ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Settings;