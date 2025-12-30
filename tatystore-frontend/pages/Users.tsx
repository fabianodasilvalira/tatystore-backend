
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useOutletContext, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { User, RoleInfo } from '../types';
import Pagination from '../components/Pagination';
import { validateEmail } from '../utils/formatters';

// Context and Form Types
interface UsersContext {
    addToast: (message: string, type?: 'success' | 'error') => void;
    apiUrl: string;
}

type UserFormData = {
    name: string;
    email: string;
    password?: string; // Optional for updates
    role_id: number | '';
};

const initialFormState: UserFormData = {
    name: '',
    email: '',
    password: '',
    role_id: '',
};

// --- Back Button Component ---
const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);

// Form Component
const UserForm: React.FC<{
    initialData: User | null;
    roles: RoleInfo[];
    onSave: (data: UserFormData) => void;
    onCancel: () => void;
    addToast: (message: string, type?: 'success' | 'error') => void;
}> = ({ initialData, roles, onSave, onCancel, addToast }) => {
    const [formData, setFormData] = useState<UserFormData>(initialFormState);
    const [showPassword, setShowPassword] = useState(false);

    useEffect(() => {
        if (initialData) {
            setFormData({
                name: initialData.name,
                email: initialData.email,
                password: '', // Password is not sent back, should be empty for editing
                role_id: initialData.role_id,
            });
        } else {
            setFormData(initialFormState);
        }
    }, [initialData]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: name === 'role_id' ? Number(value) : value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name || !formData.email || !formData.role_id) {
            addToast('Nome, Email e Perfil são obrigatórios.', 'error');
            return;
        }
        if (!validateEmail(formData.email)) {
            addToast('O formato do e-mail é inválido.', 'error');
            return;
        }
        if (!initialData && !formData.password) {
            addToast('A senha é obrigatória para criar um novo usuário.', 'error');
            return;
        }
        onSave(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome Completo</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Senha</label>
                <div className="relative">
                    <input
                        type={showPassword ? "text" : "password"}
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder={initialData ? "Deixe em branco para não alterar" : "Senha forte"}
                        className="w-full p-2 pr-10 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                        required={!initialData}
                    />
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                        title={showPassword ? "Esconder senha" : "Mostrar senha"}
                    >
                        <span className="material-symbols-outlined">
                            {showPassword ? 'visibility_off' : 'visibility'}
                        </span>
                    </button>
                </div>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Perfil</label>
                <select name="role_id" value={formData.role_id} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required>
                    <option value="">Selecione um perfil</option>
                    {roles.map(role => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                </select>
            </div>
            <div className="flex justify-end gap-4 pt-4 border-t dark:border-gray-700">
                <button type="button" onClick={onCancel} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500">Cancelar</button>
                <button type="submit" className="bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700">Salvar</button>
            </div>
        </form>
    );
};

// Main Page Component
const UsersPage: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const roles: RoleInfo[] = useMemo(() => [
        // { id: 2, name: 'Administrador' }, // Ocultado conforme solicitação: Gerente já possui acesso total à loja.
        { id: 3, name: 'Gerente' },
        { id: 4, name: 'Vendedor' },
    ], []);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [view, setView] = useState<'list' | 'form' | 'confirmToggle'>('list');
    const [userToToggle, setUserToToggle] = useState<User | null>(null);

    const [currentPage, setCurrentPage] = useState(1);
    const [totalUsers, setTotalUsers] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil(totalUsers / ITEMS_PER_PAGE), [totalUsers]);

    const { tokens } = useAuth();
    const { addToast, apiUrl } = useOutletContext<UsersContext>();
    const { userId } = useParams<{ userId: string }>();
    const navigate = useNavigate();

    const userForForm = useMemo(() => {
        if (!userId || userId === 'new') return null;
        return users.find(u => String(u.id) === String(userId)) ?? null;
    }, [userId, users]);

    const fetchUsers = useCallback(async (page = 1) => {
        if (!tokens) return;
        setIsLoading(true);
        const skip = (page - 1) * ITEMS_PER_PAGE;
        const params = new URLSearchParams({
            skip: String(skip),
            limit: String(ITEMS_PER_PAGE),
        });
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        try {
            const response = await fetch(`${apiUrl}/users/?${params.toString()}`, {
                headers: {
                    'accept': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Falha ao buscar usuários.');
            }
            const result = await response.json();
            const usersData = result.data || result.items || [];
            const total = result.metadata?.total || result.total || 0;
            setUsers(usersData);
            setTotalUsers(total);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Ocorreu um erro desconhecido.';
            setError(msg);
            addToast(msg, 'error');
        } finally {
            setIsLoading(false);
        }
    }, [tokens, addToast, apiUrl, searchTerm]);

    useEffect(() => {
        if (view === 'list') {
            const debouncedFetch = setTimeout(() => {
                fetchUsers(currentPage);
            }, 300);
            return () => clearTimeout(debouncedFetch);
        }
    }, [fetchUsers, currentPage, view, searchTerm]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm]);

    useEffect(() => {
        if (userId) {
            setView('form');
        } else {
            setView('list');
        }
    }, [userId]);

    const handleSaveUser = async (formData: UserFormData) => {
        if (!tokens) return;
        const isEditing = !!userForForm;
        const method = isEditing ? 'PUT' : 'POST';
        const url = isEditing ? `${apiUrl}/users/${userForForm.id}` : `${apiUrl}/users/`;

        const body: any = { ...formData };
        if (isEditing && userForForm) {
            body.is_active = userForForm.is_active;
        }
        if (method === 'PUT' && !body.password) {
            delete body.password;
        }

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Falha ao ${isEditing ? 'atualizar' : 'criar'} usuário.`);
            }

            addToast(`Usuário ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
            navigate('/users');
            await fetchUsers(1);
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        }
    };

    const handleToggleStatus = async () => {
        if (!userToToggle || !tokens) return;

        const method = userToToggle.is_active ? 'DELETE' : 'PUT';
        const url = `${apiUrl}/users/${userToToggle.id}`;
        let body;
        let headers: HeadersInit = { 'Authorization': `Bearer ${tokens.access_token}` };

        if (method === 'PUT') { // Reactivating
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify({
                ...userToToggle,
                is_active: true
            });
        }

        try {
            const response = await fetch(url, { method, headers, body });

            if (!response.ok && response.status !== 204) { // 204 is OK for DELETE
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Falha ao atualizar status do usuário.');
            }

            addToast('Status do usuário atualizado com sucesso!');
            await fetchUsers(currentPage);
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        } finally {
            setView('list');
            setUserToToggle(null);
        }
    };

    if (isLoading && view === 'list' && users.length === 0) {
        return <div className="text-center p-8 text-gray-500 dark:text-gray-400">Carregando usuários...</div>;
    }

    if (error && users.length === 0) {
        return <div className="text-center p-8 text-red-500">Erro ao carregar dados: {error}</div>;
    }

    if (view === 'confirmToggle' && userToToggle) {
        const actionText = userToToggle.is_active ? 'desativar' : 'ativar';
        const confirmButtonColor = userToToggle.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';
        return (
            <div>
                <BackButton onClick={() => setView('list')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar Ação</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">
                        Tem certeza que deseja {actionText} o usuário "{userToToggle.name}"?
                    </p>
                    <div className="flex justify-center gap-4">
                        <button onClick={() => setView('list')} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors">Cancelar</button>
                        <button onClick={handleToggleStatus} className={`text-white font-bold py-2 px-6 rounded-lg transition-colors ${confirmButtonColor}`}>
                            Sim, {actionText.charAt(0).toUpperCase() + actionText.slice(1)}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (view === 'form') {
        if (userId !== 'new' && !userForForm) {
            return (
                <div>
                    <BackButton onClick={() => navigate('/users')} />
                    <div className="text-center p-8 text-gray-500 dark:text-gray-400">Carregando dados do usuário...</div>
                </div>
            );
        }
        return (
            <div>
                <BackButton onClick={() => navigate('/users')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
                        {userForForm ? 'Editar Usuário' : 'Novo Usuário'}
                    </h1>
                    <UserForm
                        initialData={userForForm}
                        roles={roles}
                        onSave={handleSaveUser}
                        onCancel={() => navigate('/users')}
                        addToast={addToast}
                    />
                </div>
            </div>
        );
    }


    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-6">
                <div className="flex-1 w-full">
                    <div className="relative w-full md:w-80">
                        <input
                            type="text"
                            placeholder="Buscar por nome ou email..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            className="w-full p-3 pr-10 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                        />
                        {searchTerm && (
                            <button
                                type="button"
                                onClick={() => setSearchTerm('')}
                                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                                aria-label="Limpar busca"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        )}
                    </div>
                </div>
                <button onClick={() => navigate('/users/new')} className="flex w-full sm:w-auto items-center justify-center gap-2 bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors">
                    <span className="material-symbols-outlined">person_add</span>
                    Novo Usuário
                </button>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalUsers}</span> usuário(s) encontrada(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {users.map(user => (
                    <div
                        key={user.id}
                        onClick={() => navigate(`/users/${user.id}`)}
                        className={`bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 ${!user.is_active ? 'opacity-60' : ''}`}
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{user.name}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{user.role}</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                {user.is_active ? 'Ativo' : 'Inativo'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
                            <div className="space-x-1">
                                <button onClick={(e) => { e.stopPropagation(); navigate(`/users/${user.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                    <span className="material-symbols-outlined">edit</span>
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); setUserToToggle(user); setView('confirmToggle'); }} className={`${user.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={user.is_active ? 'Desativar' : 'Ativar'}>
                                    <span className="material-symbols-outlined">{user.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>


            {/* Desktop View */}
            <div className="hidden md:block bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Nome</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Email</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Perfil</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr
                                    key={user.id}
                                    onClick={() => navigate(`/users/${user.id}`)}
                                    className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${!user.is_active ? 'opacity-60' : ''}`}
                                >
                                    <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{user.name}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400">{user.email}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400 capitalize">{user.role}</td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${user.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                            {user.is_active ? 'Ativo' : 'Inativo'}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-center space-x-2">
                                        <button onClick={(e) => { e.stopPropagation(); navigate(`/users/${user.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                            <span className="material-symbols-outlined">edit</span>
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setUserToToggle(user); setView('confirmToggle'); }} className={`${user.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={user.is_active ? 'Desativar' : 'Ativar'}>
                                            <span className="material-symbols-outlined">{user.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={(page) => setCurrentPage(page)} />
        </div>
    );
};

export default UsersPage;
