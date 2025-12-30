import React, { useState, useEffect } from 'react';
import { useAuth } from '../App';
import { handleApiError } from '../utils/errorHandler';
import { logger } from '../utils/logger';
import { API_BASE_URL } from '../config/api';

interface ProfileFormData {
    name: string;
    email: string;
}

interface PasswordFormData {
    old_password: string;
    new_password: string;
    confirm_password: string;
}

interface FormErrors {
    name?: string;
    email?: string;
    old_password?: string;
    new_password?: string;
    confirm_password?: string;
}

const Profile: React.FC = () => {
    const { user, setUser } = useAuth();

    const [profileData, setProfileData] = useState<ProfileFormData>({ name: '', email: '' });
    const [passwordData, setPasswordData] = useState<PasswordFormData>({
        old_password: '',
        new_password: '',
        confirm_password: ''
    });

    const [loadingProfile, setLoadingProfile] = useState(false);
    const [loadingPassword, setLoadingPassword] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [showOldPassword, setShowOldPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [errors, setErrors] = useState<FormErrors>({});
    const [showPasswordForm, setShowPasswordForm] = useState(false);

    useEffect(() => {
        if (user) {
            setProfileData({
                name: user.name || '',
                email: user.email || ''
            });
        }
    }, [user]);

    const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setProfileData(prev => ({ ...prev, [name]: value }));
        if (errors[name as keyof FormErrors]) {
            setErrors(prev => ({ ...prev, [name]: undefined }));
        }
    };

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setPasswordData(prev => ({ ...prev, [name]: value }));
        if (errors[name as keyof FormErrors]) {
            setErrors(prev => ({ ...prev, [name]: undefined }));
        }
    };

    const validateProfile = (): boolean => {
        const newErrors: FormErrors = {};
        let isValid = true;

        if (!profileData.name.trim()) {
            newErrors.name = 'Nome é obrigatório';
            isValid = false;
        } else if (profileData.name.length < 3) {
            newErrors.name = 'Nome deve ter pelo menos 3 caracteres';
            isValid = false;
        }

        if (!profileData.email.trim()) {
            newErrors.email = 'Email é obrigatório';
            isValid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileData.email)) {
            newErrors.email = 'Email inválido';
            isValid = false;
        }

        setErrors(newErrors);
        return isValid;
    };

    const validatePassword = (): boolean => {
        const newErrors: FormErrors = {};
        let isValid = true;

        if (!passwordData.old_password) {
            newErrors.old_password = 'Senha atual é obrigatória';
            isValid = false;
        }

        if (!passwordData.new_password) {
            newErrors.new_password = 'Nova senha é obrigatória';
            isValid = false;
        } else if (passwordData.new_password.length < 8) {
            newErrors.new_password = 'Senha deve ter no mínimo 8 caracteres';
            isValid = false;
        }

        if (passwordData.new_password !== passwordData.confirm_password) {
            newErrors.confirm_password = 'As senhas não coincidem';
            isValid = false;
        }

        setErrors(newErrors);
        return isValid;
    };

    const handleProfileSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);
        setErrors({});

        if (!validateProfile()) return;

        setLoadingProfile(true);

        try {
            const tokensData = localStorage.getItem('tokens');
            if (!tokensData) {
                throw new Error('Sessão expirada. Faça login novamente.');
            }
            const { access_token } = JSON.parse(tokensData);

            const response = await fetch(`${API_BASE_URL}/users/me`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${access_token}`
                },
                body: JSON.stringify(profileData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao atualizar perfil');
            }

            const userData = await response.json();

            if (user) {
                setUser({ ...user, ...userData });
            }

            setMessage({ type: 'success', text: 'Perfil atualizado com sucesso!' });
            logger.info('Perfil atualizado', { userId: user?.id }, 'Profile');

        } catch (error: any) {
            const errorMessage = handleApiError(error, 'ProfileUpdate');
            setMessage({ type: 'error', text: errorMessage });
        } finally {
            setLoadingProfile(false);
        }
    };

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);
        setErrors({});

        if (!validatePassword()) return;

        setLoadingPassword(true);

        try {
            const tokensData = localStorage.getItem('tokens');
            if (!tokensData) {
                throw new Error('Sessão expirada. Faça login novamente.');
            }
            const { access_token } = JSON.parse(tokensData);

            const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${access_token}`
                },
                body: JSON.stringify({
                    old_password: passwordData.old_password,
                    new_password: passwordData.new_password
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao alterar senha');
            }

            setMessage({ type: 'success', text: 'Senha alterada com sucesso!' });

            setPasswordData({
                old_password: '',
                new_password: '',
                confirm_password: ''
            });
            setShowPasswordForm(false);

            logger.info('Senha alterada', { userId: user?.id }, 'Profile');

        } catch (error: any) {
            const errorMessage = handleApiError(error, 'PasswordChange');
            setMessage({ type: 'error', text: errorMessage });
        } finally {
            setLoadingPassword(false);
        }
    };

    if (!user) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {message && (
                <div className={`p-4 rounded-lg flex items-start gap-3 shadow-sm ${message.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800'
                    : 'bg-red-50 text-red-800 border border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800'
                    }`}>
                    <span className="material-symbols-outlined shrink-0 mt-0.5">
                        {message.type === 'success' ? 'check_circle' : 'error'}
                    </span>
                    <span className="font-medium">{message.text}</span>
                </div>
            )}

            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-100">Informações Pessoais</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">Gerencie suas informações básicas e de contato.</p>

                <form onSubmit={handleProfileSubmit} className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Nome Completo
                            </label>
                            <input
                                type="text"
                                name="name"
                                value={profileData.name}
                                onChange={handleProfileChange}
                                className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                                    }`}
                            />
                            {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Email
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={profileData.email}
                                onChange={handleProfileChange}
                                className={`w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                                    }`}
                            />
                            {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email}</p>}
                        </div>
                    </div>

                    <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg grid grid-cols-2 gap-4">
                        <div>
                            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Função</span>
                            <span className="inline-block px-2 py-1 rounded bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 text-xs font-semibold">
                                {user.role}
                            </span>
                        </div>
                        {user.company_name && (
                            <div>
                                <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Empresa</span>
                                <span className="text-sm font-medium text-gray-900 dark:text-white">
                                    {user.company_name}
                                </span>
                            </div>
                        )}
                    </div>

                    <div className="flex justify-end border-t dark:border-gray-700 pt-4">
                        <button
                            type="submit"
                            disabled={loadingProfile}
                            className="bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loadingProfile ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    <span>Salvando...</span>
                                </>
                            ) : (
                                <span>Salvar Alterações</span>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold mb-1 text-gray-800 dark:text-gray-100">Segurança da Conta</h2>
                        <p className="text-gray-600 dark:text-gray-300 text-sm">Atualize sua senha periodicamente.</p>
                    </div>
                    {!showPasswordForm && (
                        <button
                            onClick={() => setShowPasswordForm(true)}
                            className="text-primary-600 dark:text-primary-400 font-semibold hover:text-primary-800 dark:hover:text-primary-300 text-sm"
                        >
                            Alterar Senha
                        </button>
                    )}
                </div>

                {showPasswordForm && (
                    <form onSubmit={handlePasswordSubmit} className="space-y-4 mt-6 border-t dark:border-gray-700 pt-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Senha Atual
                            </label>
                            <div className="relative">
                                <input
                                    type={showOldPassword ? "text" : "password"}
                                    name="old_password"
                                    value={passwordData.old_password}
                                    onChange={handlePasswordChange}
                                    className={`w-full p-2 pr-10 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.old_password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                                        }`}
                                    placeholder="Digite sua senha atual"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowOldPassword(!showOldPassword)}
                                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                >
                                    <span className="material-symbols-outlined text-xl">
                                        {showOldPassword ? 'visibility_off' : 'visibility'}
                                    </span>
                                </button>
                            </div>
                            {errors.old_password && <p className="mt-1 text-xs text-red-500">{errors.old_password}</p>}
                        </div>

                        <div className="grid md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Nova Senha
                                </label>
                                <div className="relative">
                                    <input
                                        type={showNewPassword ? "text" : "password"}
                                        name="new_password"
                                        value={passwordData.new_password}
                                        onChange={handlePasswordChange}
                                        className={`w-full p-2 pr-10 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.new_password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                                            }`}
                                        placeholder="Mínimo 8 caracteres"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowNewPassword(!showNewPassword)}
                                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                    >
                                        <span className="material-symbols-outlined text-xl">
                                            {showNewPassword ? 'visibility_off' : 'visibility'}
                                        </span>
                                    </button>
                                </div>
                                {errors.new_password && <p className="mt-1 text-xs text-red-500">{errors.new_password}</p>}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Confirmar Nova Senha
                                </label>
                                <div className="relative">
                                    <input
                                        type={showConfirmPassword ? "text" : "password"}
                                        name="confirm_password"
                                        value={passwordData.confirm_password}
                                        onChange={handlePasswordChange}
                                        className={`w-full p-2 pr-10 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors.confirm_password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                                            }`}
                                        placeholder="Confirme a nova senha"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                    >
                                        <span className="material-symbols-outlined text-xl">
                                            {showConfirmPassword ? 'visibility_off' : 'visibility'}
                                        </span>
                                    </button>
                                </div>
                                {errors.confirm_password && <p className="mt-1 text-xs text-red-500">{errors.confirm_password}</p>}
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-2">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowPasswordForm(false);
                                    setErrors({});
                                    setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
                                }}
                                className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                disabled={loadingPassword}
                                className="bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loadingPassword ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        <span>Processando...</span>
                                    </>
                                ) : (
                                    <span>Atualizar Senha</span>
                                )}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
};

export default Profile;
