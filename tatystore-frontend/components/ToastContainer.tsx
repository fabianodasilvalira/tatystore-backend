import React from 'react';

interface ToastProps {
    message: string;
    type: 'success' | 'error';
}

const Toast: React.FC<ToastProps> = ({ message, type }) => {
    const baseClasses = "flex items-center w-full p-4 space-x-4 text-gray-800 bg-white rounded-2xl shadow-2xl dark:text-gray-100 dark:bg-gray-800 ring-1 ring-black ring-opacity-5 transform transition-all duration-300 animate-slide-in";
    const typeClasses = {
        success: "text-green-600 bg-green-100 dark:bg-green-900/50 dark:text-green-300",
        error: "text-red-600 bg-red-100 dark:bg-red-900/50 dark:text-red-300",
    };
    const icon = {
        success: "check_circle",
        error: "error",
    };

    return (
        <div className={baseClasses} role="alert">
            <div className={`flex-shrink-0 p-3 rounded-full ${typeClasses[type]}`}>
                <span className="material-symbols-outlined text-2xl">{icon[type]}</span>
            </div>
            <div className="flex-1 text-base font-medium">{message}</div>
        </div>
    );
};


interface ToastContainerProps {
    toasts: { id: number; message: string; type: 'success' | 'error' }[];
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts }) => {
    return (
        <>
            <div className="fixed bottom-5 sm:top-5 sm:bottom-auto left-1/2 -translate-x-1/2 z-[100] space-y-3 w-full max-w-md px-4">
                {toasts.map(toast => (
                    <Toast key={toast.id} message={toast.message} type={toast.type} />
                ))}
            </div>
            <style>{`
                /* Animation for mobile (from bottom) */
                @keyframes slide-in-from-bottom {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                /* Animation for desktop (from top) */
                @keyframes slide-in-from-top {
                    from {
                        opacity: 0;
                        transform: translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .animate-slide-in {
                    animation: slide-in-from-bottom 0.3s ease-out forwards;
                }

                @media (min-width: 640px) { /* Tailwind's sm breakpoint */
                    .animate-slide-in {
                        animation-name: slide-in-from-top;
                    }
                }
            `}</style>
        </>
    );
};

export default ToastContainer;