import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Company } from '../../types';
import { useAuth } from '../../App';
import { getFullUrl } from '../../config/api';

interface StoreHeaderProps {
    company: Company | null;
    companySlug: string;
    isVisible: boolean;
}

const StoreHeader: React.FC<StoreHeaderProps> = ({ company, companySlug, isVisible }) => {
    const navigate = useNavigate();
    const { isAuthenticated, user } = useAuth();

    // Determine if the logged-in user is the owner of this storefront
    const isOwnerViewing = isAuthenticated && user?.company_slug === companySlug;

    const headerClasses = `bg-white dark:bg-gray-800 shadow-md h-20 sticky top-0 z-20 transition-transform duration-300 ${isVisible ? 'translate-y-0' : '-translate-y-full'}`;

    // Skeleton loader for when company data is not yet available
    if (!company) {
        return (
            <header className={`${headerClasses} animate-pulse`}>
                <div className="container mx-auto flex items-center justify-between h-full px-4">
                    <div className="h-12 w-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                    <div className="hidden sm:block h-6 w-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-10 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                </div>
            </header>
        );
    }

    const logoSrc = getFullUrl(company.logo_url);

    return (
        <header className={headerClasses}>
            <div className="container mx-auto flex items-center justify-between h-full px-4 gap-4">

                {/* Left: Logo or Name + Icon */}
                <div className="flex-1 min-w-0">
                    <div
                        className="group flex items-center gap-3 cursor-pointer w-fit"
                        onClick={() => navigate(`/store/${companySlug}`)}
                        title="Ir para a página inicial da loja"
                    >
                        {logoSrc ? (
                            <img
                                src={logoSrc}
                                alt={`${company.name} logo`}
                                className="h-14 w-auto max-w-[180px] rounded-lg object-contain"
                            />
                        ) : (
                            <>
                                <span className="material-symbols-outlined text-4xl text-primary-600 dark:text-primary-300">storefront</span>
                                <h1 className="text-2xl sm:text-3xl font-bold text-primary-600 dark:text-primary-300 truncate">{company.name}</h1>
                            </>
                        )}
                    </div>
                </div>

                {/* Center: Details (Desktop only) */}
                <div className="hidden sm:flex flex-col items-center text-sm text-gray-500 dark:text-gray-400 mx-4 flex-shrink-0">
                    {company.address && (
                        <p className="flex items-center gap-1.5 whitespace-nowrap">
                            <span className="material-symbols-outlined text-base">location_on</span>
                            <span>{company.address}</span>
                        </p>
                    )}
                    {company.phone && (
                        <p className="flex items-center gap-1.5 whitespace-nowrap">
                            <span className="material-symbols-outlined text-base">call</span>
                            <span>{company.phone}</span>
                        </p>
                    )}
                </div>

                {/* Right: Back Button */}
                <div className="flex-1 min-w-0 flex justify-end">
                    {isOwnerViewing && (
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="flex items-center gap-2 bg-primary-50 dark:bg-primary-900/50 text-primary-600 dark:text-primary-300 font-semibold px-3 sm:px-4 py-2 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900 transition-colors text-sm sm:text-base whitespace-nowrap"
                        >
                            <span className="material-symbols-outlined text-xl">arrow_back</span>
                            <span className="hidden sm:inline">Voltar ao Sistema</span>
                            <span className="sm:hidden">Voltar</span>
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
};

export default StoreHeader;