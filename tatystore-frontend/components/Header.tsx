import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { User, Company } from '../types';

interface HeaderProps {
    onMenuClick: () => void;
    pageTitle: string;
    user: User | null;
    company: Company | null;
    themeColor: string;
    serverUrl: string;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, pageTitle, user, company, themeColor, serverUrl }) => {
    const { logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    const isWhiteTheme = themeColor === 'white';
    
    const headerBgColor = isWhiteTheme ? 'bg-white' : 'bg-primary-600';
    const headerTextColor = isWhiteTheme ? 'text-gray-800' : 'text-white';
    const headerBorderColor = isWhiteTheme ? 'border-gray-200' : 'border-primary-700/50';
    const emailTextColor = isWhiteTheme ? 'text-gray-500' : 'text-primary-100';
    const avatarBgColor = isWhiteTheme ? 'bg-gray-100' : 'bg-black/20';
    const avatarIconColor = isWhiteTheme ? 'text-gray-700' : 'text-white';
    
    const showBackButton = location.pathname !== '/dashboard';

    return (
        <>
            {/* Mobile Header */}
            <header className={`lg:hidden h-20 px-4 flex items-center justify-between shadow-md sticky top-0 z-20 ${headerBgColor}`}>
                <div className="flex items-center gap-2 flex-1 min-w-0">
                     {showBackButton && (
                        <button 
                            onClick={() => navigate(-1)} 
                            className={`-ml-2 p-2 rounded-full ${headerTextColor}`}
                            aria-label="Voltar"
                        >
                            <span className="material-symbols-outlined text-3xl">arrow_back</span>
                        </button>
                    )}
                    <h1 className={`text-xl font-bold truncate ${headerTextColor}`}>{pageTitle}</h1>
                </div>
                <button onClick={onMenuClick} className={headerTextColor} aria-label="Abrir menu">
                    <span className="material-symbols-outlined text-3xl">menu</span>
                </button>
            </header>

            {/* Desktop Header */}
            <header className={`hidden lg:flex h-20 px-8 items-center justify-between border-b sticky top-0 z-20 ${headerBgColor} ${headerTextColor} ${headerBorderColor}`}>
                <h1 className="text-3xl font-bold">{pageTitle}</h1>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="font-semibold">{user?.name || 'Usuário'}</p>
                        <p className={`text-xs ${emailTextColor}`}>{user?.email || 'email@exemplo.com'}</p>
                    </div>
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${avatarBgColor}`}>
                        <span className={`material-symbols-outlined text-3xl ${avatarIconColor}`}>
                            person
                        </span>
                    </div>
                    <button 
                        onClick={logout} 
                        className="p-2 rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
                        title="Sair"
                    >
                        <span className="material-symbols-outlined">logout</span>
                    </button>
                </div>
            </header>
        </>
    );
};

export default Header;