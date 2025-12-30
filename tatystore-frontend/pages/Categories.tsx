
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useOutletContext, useParams, useNavigate } from 'react-router-dom';
import { Category, User } from '../types';
import { useAuth } from '../App';
import Pagination from '../components/Pagination';

interface CategoriesContext {
    categories: Category[];
    totalCategories: number;
    fetchCategories: (filters: any) => Promise<void>;
    addToast: (message: string, type?: 'success' | 'error') => void;
    user: User | null;
    apiUrl: string;
}

// Back Button Component
const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);

// Form Component
type CategoryFormData = Omit<Category, 'id' | 'company_id' | 'is_active' | 'product_count' | 'created_at' | 'updated_at'>;

const CategoryForm: React.FC<{
    initialData: Category | null;
    onSave: (data: CategoryFormData) => void;
    onCancel: () => void;
}> = ({ initialData, onSave, onCancel }) => {
    const [formData, setFormData] = useState<CategoryFormData>({ name: '', description: '' });

    useEffect(() => {
        if (initialData) {
            setFormData({ name: initialData.name, description: initialData.description || '' });
        } else {
            setFormData({ name: '', description: '' });
        }
    }, [initialData]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name.trim()) {
            alert('O nome da categoria é obrigatório.');
            return;
        }
        onSave(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome da Categoria</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea name="description" value={formData.description || ''} onChange={handleChange} rows={3} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
            </div>
            <div className="flex justify-end gap-4 pt-4 border-t dark:border-gray-700">
                <button type="button" onClick={onCancel} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500">Cancelar</button>
                <button type="submit" className="bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700">Salvar</button>
            </div>
        </form>
    );
};


const CategoriesPage: React.FC = () => {
    const { categories, totalCategories, fetchCategories, addToast, user, apiUrl } = useOutletContext<CategoriesContext>();
    const { categoryId } = useParams<{ categoryId: string }>();
    const navigate = useNavigate();
    const { tokens } = useAuth();
    
    const [view, setView] = useState<'list' | 'form' | 'confirmToggle'>('list');
    const [searchTerm, setSearchTerm] = useState('');
    const [showInactive, setShowInactive] = useState(false);
    const [categoryToToggle, setCategoryToToggle] = useState<Category | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil(totalCategories / ITEMS_PER_PAGE), [totalCategories]);

    const categoryForForm = useMemo(() => {
        if (!categoryId || categoryId === 'new') return null;
        return categories.find(c => String(c.id) === String(categoryId)) ?? null;
    }, [categoryId, categories]);
    
    useEffect(() => {
        if (view === 'list') {
            const debouncedFetch = setTimeout(() => {
                fetchCategories({ page: currentPage, searchTerm, showInactive });
            }, 300);
            return () => clearTimeout(debouncedFetch);
        }
    }, [searchTerm, showInactive, fetchCategories, view, currentPage]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, showInactive]);
    
    useEffect(() => {
        if (categoryId) {
            setView('form');
        } else {
            setView('list');
        }
    }, [categoryId]);
    
    const handleSaveCategory = async (formData: CategoryFormData) => {
        if (!tokens) return;
        const isEditing = !!categoryForForm;
        const method = isEditing ? 'PUT' : 'POST';
        const url = isEditing
            ? `${apiUrl}/categories/${categoryForForm.id}`
            : `${apiUrl}/categories/`;

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`,
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Falha ao ${isEditing ? 'salvar' : 'criar'} categoria.`);
            }

            addToast(`Categoria ${isEditing ? 'atualizada' : 'criada'} com sucesso!`);
            navigate('/categories');
            await fetchCategories({ page: 1 });
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        }
    };
    
    const handleToggleStatus = async () => {
        if (!categoryToToggle || !tokens) return;

        const { product_count, ...updatePayload } = categoryToToggle;

        const updatedCategoryData = {
            ...updatePayload,
            is_active: !categoryToToggle.is_active,
        };
        
        try {
            const response = await fetch(`${apiUrl}/categories/${categoryToToggle.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`,
                },
                body: JSON.stringify(updatedCategoryData),
            });

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({}));
                 throw new Error(errorData.detail || 'Falha ao atualizar status da categoria.');
            }

            addToast('Status da categoria atualizado com sucesso!');
            await fetchCategories({ page: currentPage, searchTerm, showInactive });
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        } finally {
            setView('list');
            setCategoryToToggle(null);
        }
    };

    const handlePageChange = (page: number) => {
        if (page > 0 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    if (view === 'confirmToggle' && categoryToToggle) {
        const actionText = categoryToToggle.is_active ? 'desativar' : 'ativar';
        const confirmButtonColor = categoryToToggle.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';
        return (
            <div>
                <BackButton onClick={() => setView('list')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar Ação</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">
                        Tem certeza que deseja {actionText} a categoria "{categoryToToggle.name}"?
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
        return (
             <div>
                <BackButton onClick={() => navigate('/categories')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
                        {categoryForForm ? 'Editar Categoria' : 'Nova Categoria'}
                    </h1>
                    <CategoryForm
                        initialData={categoryForForm}
                        onSave={handleSaveCategory}
                        onCancel={() => navigate('/categories')}
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
                            placeholder="Buscar por nome..."
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
                <div className="flex items-center gap-4">
                    <label className="flex items-center cursor-pointer whitespace-nowrap p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                        <input type="checkbox" checked={showInactive} onChange={() => setShowInactive(!showInactive)} className="mr-2 h-4 w-4 rounded text-primary-600 focus:ring-primary-500" />
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Mostrar inativas</span>
                    </label>
                    <button onClick={() => navigate('/categories/new')} className="flex items-center justify-center gap-2 bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors">
                        <span className="material-symbols-outlined">add</span>
                        Nova Categoria
                    </button>
                </div>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalCategories}</span> categoria(s) encontrada(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {categories.map(category => (
                    <div
                        key={category.id}
                        onClick={() => navigate(`/categories/${category.id}`)}
                        className={`bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 ${!category.is_active ? 'opacity-60' : ''}`}
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{category.name}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">{category.product_count || 0} produtos</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${category.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                {category.is_active ? 'Ativa' : 'Inativa'}
                            </span>
                        </div>
                         <div className="flex justify-end items-center mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                             <div className="space-x-1">
                                <button onClick={(e) => { e.stopPropagation(); navigate(`/categories/${category.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                    <span className="material-symbols-outlined">edit</span>
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); setCategoryToToggle(category); setView('confirmToggle'); }} className={`${category.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800' } p-1 rounded-full`} title={category.is_active ? 'Desativar' : 'Ativar'}>
                                    <span className="material-symbols-outlined">{category.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Desktop View */}
            <div className="hidden md:block bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Nome</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Descrição</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Produtos</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {categories.length === 0 ? (
                                <tr><td colSpan={5} className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhuma categoria encontrada.</td></tr>
                            ) : (
                                categories.map(category => (
                                <tr 
                                    key={category.id} 
                                    onClick={() => navigate(`/categories/${category.id}`)}
                                    className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${!category.is_active ? 'opacity-60' : ''}`}
                                >
                                    <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{category.name}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400 truncate max-w-xs">{category.description}</td>
                                    <td className="py-3 px-4 text-center text-gray-600 dark:text-gray-300">{category.product_count || 0}</td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${category.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                            {category.is_active ? 'Ativa' : 'Inativa'}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-center space-x-2">
                                        <button onClick={(e) => { e.stopPropagation(); navigate(`/categories/${category.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                            <span className="material-symbols-outlined">edit</span>
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setCategoryToToggle(category); setView('confirmToggle'); }} className={`${category.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800' } p-1 rounded-full`} title={category.is_active ? 'Desativar' : 'Ativar'}>
                                             <span className="material-symbols-outlined">{category.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                        </button>
                                    </td>
                                </tr>
                            )))}
                        </tbody>
                    </table>
                </div>
            </div>
            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
        </div>
    );
};

export default CategoriesPage;
