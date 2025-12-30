import React from 'react';

interface DashboardCardProps {
    icon: string;
    title: string;
    value: string | number;
    color: string;
    children?: React.ReactNode;
    tooltipText?: string;
}

const DashboardCard: React.FC<DashboardCardProps> = ({ icon, title, value, color, children, tooltipText }) => {
    const colorClasses = {
        purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-300',
        green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-300',
        red: 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-300',
        blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-300',
    };

    const iconBgClasses = {
        purple: 'bg-purple-100 dark:bg-purple-900/50',
        green: 'bg-green-100 dark:bg-green-900/50',
        red: 'bg-red-100 dark:bg-red-900/50',
        blue: 'bg-blue-100 dark:bg-blue-900/50',
    };

    const bgColor = colorClasses[color as keyof typeof colorClasses] || colorClasses.purple;
    const iconBg = iconBgClasses[color as keyof typeof iconBgClasses] || iconBgClasses.purple;

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md flex flex-col justify-between hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100 dark:border-gray-700/50 group">
            <div>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{title}</h3>
                            {tooltipText && (
                                <div className="relative group/tooltip flex items-center">
                                    <span className="material-symbols-outlined text-gray-400 cursor-help text-base hover:text-gray-600 dark:hover:text-gray-300 transition-colors">info</span>
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-60 p-3 text-sm font-normal text-left text-white bg-gray-900 rounded-lg shadow-xl opacity-0 group-hover/tooltip:opacity-100 transition-opacity duration-200 pointer-events-none z-50 dark:bg-gray-700">
                                        {tooltipText}
                                        <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-x-4 border-x-transparent border-t-4 border-t-gray-900 dark:border-t-gray-700"></div>
                                    </div>
                                </div>
                            )}
                        </div>
                        <p className="text-3xl sm:text-4xl font-extrabold text-gray-800 dark:text-gray-100 tracking-tight">{value}</p>
                    </div>
                    <div className={`flex-shrink-0 p-3 rounded-xl ${iconBg} ${bgColor} transition-colors duration-300 group-hover:scale-110`}>
                        <span className="material-symbols-outlined text-3xl">{icon}</span>
                    </div>
                </div>
            </div>
            {children && <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700/50 text-sm text-gray-600 dark:text-gray-300">{children}</div>}
        </div>
    );
};

export default DashboardCard;