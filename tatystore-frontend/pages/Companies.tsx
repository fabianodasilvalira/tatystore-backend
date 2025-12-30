
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useOutletContext, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { Company } from '../types';
import Pagination from '../components/Pagination';
import Modal from '../components/Modal';
import { maskPhone, maskCNPJ, validateEmail, unmask } from '../utils/formatters';
import { logger } from '../utils/logger';

interface CompanyContext {
    addToast: (message: string, type?: 'success' | 'error') => void;
    apiUrl: string;
    serverUrl: string;
}

type CompanyFormData = Omit<Company, 'id' | 'slug' | 'is_active' | 'created_at' | 'access_url' | 'logo_url'>;
const initialFormState: CompanyFormData = {
    name: '',
    cnpj: '',
    email: '',
    phone: '',
    address: ''
};

// --- Back Button Component ---
const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);

const CompanyForm: React.FC<{
    initialData: Company | null;
    onSave: (data: CompanyFormData, file: File | null) => void;
    onCancel: () => void;
    addToast: (message: string, type?: 'success' | 'error') => void;
    serverUrl: string;
}> = ({ initialData, onSave, onCancel, addToast, serverUrl }) => {
    const [formData, setFormData] = useState<CompanyFormData>(initialFormState);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>('');

    useEffect(() => {
        if (initialData) {
            setFormData({
                name: initialData.name,
                cnpj: maskCNPJ(initialData.cnpj),
                email: initialData.email,
                phone: maskPhone(initialData.phone),
                address: initialData.address,
            });
            setPreviewUrl(initialData.logo_url ? `${serverUrl}${initialData.logo_url}` : '');
        } else {
            setFormData(initialFormState);
            setPreviewUrl('');
        }
        setSelectedFile(null);
    }, [initialData, serverUrl]);

    const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            addToast('Tipo de arquivo inválido. Use JPG, PNG ou WEBP.', 'error');
            return;
        }

        const maxSizeInBytes = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSizeInBytes) {
            addToast('O arquivo é muito grande. O tamanho máximo é de 5MB.', 'error');
            return;
        }

        setSelectedFile(file);
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }
        setPreviewUrl(URL.createObjectURL(file));
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let { name, value } = e.target;
        if (name === 'phone') value = maskPhone(value);
        if (name === 'cnpj') value = maskCNPJ(value);
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name || !formData.cnpj || !formData.email) {
            addToast('Nome, CNPJ e Email são obrigatórios.', 'error');
            return;
        }
        if (unmask(formData.cnpj).length !== 14) {
            addToast('O CNPJ deve conter 14 dígitos.', 'error');
            return;
        }
        if (!validateEmail(formData.email)) {
            addToast('O formato do e-mail é inválido.', 'error');
            return;
        }
        const dataToSend = {
            ...formData,
            cnpj: unmask(formData.cnpj),
            phone: unmask(formData.phone),
        };
        onSave(dataToSend, selectedFile);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center gap-4">
                <div className="w-24 h-24 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center border dark:border-gray-600 flex-shrink-0">
                    <img
                        src={previewUrl || 'https://placehold.co/96x96/f1f5f9/9ca3af?text=Logo'}
                        alt="Pré-visualização do logo"
                        className="w-full h-full rounded-lg object-cover"
                    />
                </div>
                <div className="flex-1 w-full">
                    <label htmlFor="logo-upload" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Logo da Empresa</label>
                    <input
                        id="logo-upload"
                        type="file"
                        accept="image/png, image/jpeg, image/webp"
                        onChange={handleLogoChange}
                        className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-700/20 dark:file:text-primary-300 dark:hover:file:bg-primary-700/30 cursor-pointer"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">PNG, JPG, WEBP (Máx 5MB).</p>
                </div>
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome da Empresa</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
                <input type="text" name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                <input type="tel" name="phone" value={formData.phone} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço</label>
                <input type="text" name="address" value={formData.address} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
            </div>
            <div className="flex justify-end gap-4 pt-4 border-t dark:border-gray-700">
                <button type="button" onClick={onCancel} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500">Cancelar</button>
                <button type="submit" className="bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700">Salvar</button>
            </div>
        </form>
    );
};


const CompaniesPage: React.FC = () => {
    const [companies, setCompanies] = useState<Company[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [view, setView] = useState<'list' | 'form' | 'confirmToggle'>('list');
    const [companyToToggle, setCompanyToToggle] = useState<Company | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCompanies, setTotalCompanies] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [newCompanyInfo, setNewCompanyInfo] = useState<any | null>(null);
    const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);

    const ITEMS_PER_PAGE = 20;
    const totalPages = useMemo(() => Math.ceil(totalCompanies / ITEMS_PER_PAGE), [totalCompanies]);

    const { tokens } = useAuth();
    const { addToast, apiUrl, serverUrl } = useOutletContext<CompanyContext>();
    const { companyId } = useParams<{ companyId: string }>();
    const navigate = useNavigate();

    const companyForForm = useMemo(() => {
        if (!companyId || companyId === 'new') return null;
        return companies.find(c => String(c.id) === String(companyId)) ?? null;
    }, [companyId, companies]);

    const fetchCompanies = useCallback(async (page = 1) => {
        if (!tokens) return;
        setIsLoading(true);
        setError('');
        const skip = (page - 1) * ITEMS_PER_PAGE;
        const params = new URLSearchParams({
            skip: String(skip),
            limit: String(ITEMS_PER_PAGE),
        });
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        try {
            const response = await fetch(`${apiUrl}/companies/?${params.toString()}`, {
                headers: {
                    'accept': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Falha ao buscar empresas.');
            }
            const result = await response.json();
            setCompanies(result.data || result.items || []);
            setTotalCompanies(result.metadata?.total || result.total || 0);
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
                fetchCompanies(currentPage);
            }, 300);
            return () => clearTimeout(debouncedFetch);
        }
    }, [fetchCompanies, currentPage, view, searchTerm]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm]);

    useEffect(() => {
        if (companyId) {
            setView('form');
        } else {
            setView('list');
        }
    }, [companyId]);

    const handleSaveCompany = async (formData: CompanyFormData, file: File | null) => {
        if (!tokens) return;
        const isEditing = !!companyForForm;
        const method = isEditing ? 'PUT' : 'POST';
        const url = isEditing ? `${apiUrl}/companies/${companyForForm.id}` : `${apiUrl}/companies/`;

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.detail || `Falha ao ${isEditing ? 'atualizar' : 'criar'} empresa.`;
                throw new Error(errorMessage);
            }

            if (isEditing) {
                const savedCompany = await response.json();
                const companyIdForLogo = companyForForm?.id;

                if (file && companyIdForLogo) {
                    const logoFormData = new FormData();
                    logoFormData.append("file", file);

                    const logoUploadUrl = `${apiUrl}/companies/${companyIdForLogo}/logo`;
                    const logoResponse = await fetch(logoUploadUrl, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${tokens.access_token}` },
                        body: logoFormData
                    });

                    if (!logoResponse.ok) {
                        const errorData = await logoResponse.json();
                        throw new Error(errorData.detail || 'Dados salvos, mas falha ao enviar o logo.');
                    }
                }
                addToast(`Empresa atualizada com sucesso!`);
                navigate('/companies');
                await fetchCompanies(1);
            } else { // Creating
                const savedCompanyData = await response.json();
                const companyIdForLogo = savedCompanyData.id;

                if (file && companyIdForLogo) {
                    const logoFormData = new FormData();
                    logoFormData.append("file", file);
                    const logoUploadUrl = `${apiUrl}/companies/${companyIdForLogo}/logo`;
                    const logoResponse = await fetch(logoUploadUrl, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${tokens.access_token}` },
                        body: logoFormData
                    });
                    if (!logoResponse.ok) {
                        const errorData = await logoResponse.json();
                        addToast(errorData.detail || 'Dados salvos, mas falha ao enviar o logo.', 'error');
                    }
                }
                setNewCompanyInfo(savedCompanyData);
                setIsInfoModalOpen(true);
                await fetchCompanies(1);
            }
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        }
    };

    const handleToggleStatus = async () => {
        if (!companyToToggle || !tokens) return;

        const body = {
            ...companyToToggle,
            cnpj: unmask(companyToToggle.cnpj),
            phone: unmask(companyToToggle.phone),
            is_active: !companyToToggle.is_active,
        };

        try {
            const response = await fetch(`${apiUrl}/companies/${companyToToggle.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error('Falha ao atualizar status da empresa.');
            }

            addToast('Status da empresa atualizado com sucesso!');
            await fetchCompanies(currentPage);
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        } finally {
            setView('list');
            setCompanyToToggle(null);
        }
    };

    const handlePageChange = (page: number) => {
        if (page > 0 && page <= totalPages) {
            setCurrentPage(page);
        }
    };

    const handleCopyInfo = () => {
        if (!newCompanyInfo) return;
        const textToCopy = `
URL da Vitrine: ${window.location.origin}/#/store/${newCompanyInfo.slug}
URL de Login: ${window.location.origin}/#/login
Email do Gerente: ${newCompanyInfo.admin_email}
Senha Temporária: ${newCompanyInfo.admin_password}
        `.trim();
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                addToast('Informações copiadas para a área de transferência!', 'success');
            })
            .catch(err => {
                addToast('Falha ao copiar informações.', 'error');
                logger.error('Copy failed', err, 'Companies - handleCopyInfo');
            });
    };

    if (isLoading && view === 'list' && companies.length === 0) {
        return <div className="text-center p-8">Carregando empresas...</div>;
    }

    if (error && companies.length === 0) {
        return <div className="text-center p-8 text-red-500">Erro ao carregar dados: {error}</div>;
    }

    if (view === 'confirmToggle' && companyToToggle) {
        const actionText = companyToToggle.is_active ? 'desativar' : 'ativar';
        const confirmButtonColor = companyToToggle.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';
        return (
            <div>
                <BackButton onClick={() => setView('list')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar Ação</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">
                        Tem certeza que deseja {actionText} a empresa "{companyToToggle.name}"?
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
        if (companyId !== 'new' && !companyForForm) {
            return (
                <div>
                    <BackButton onClick={() => navigate('/companies')} />
                    <div className="text-center p-8 text-gray-500 dark:text-gray-400">Carregando dados da empresa...</div>
                </div>
            );
        }
        return (
            <div>
                <BackButton onClick={() => navigate('/companies')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
                        {companyForForm ? 'Editar Empresa' : 'Nova Empresa'}
                    </h1>
                    <CompanyForm
                        initialData={companyForForm}
                        onSave={handleSaveCompany}
                        onCancel={() => navigate('/companies')}
                        addToast={addToast}
                        serverUrl={serverUrl}
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
                <button onClick={() => navigate('/companies/new')} className="flex w-full sm:w-auto items-center justify-center gap-2 bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors">
                    <span className="material-symbols-outlined">add_business</span>
                    Nova Empresa
                </button>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalCompanies}</span> empresa(s) encontrada(s).
                </p>
            </div>

            {/* Mobile View */}
            <div className="md:hidden space-y-4">
                {companies.map(company => (
                    <div
                        key={company.id}
                        onClick={() => navigate(`/companies/${company.id}`)}
                        className={`bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 ${!company.is_active ? 'opacity-60' : ''}`}
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="font-bold text-lg text-gray-800 dark:text-gray-100">{company.name}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">{company.email}</p>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${company.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                {company.is_active ? 'Ativa' : 'Inativa'}
                            </span>
                        </div>
                        <div className="flex justify-end items-center mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                            <div className="space-x-1">
                                <button onClick={(e) => { e.stopPropagation(); navigate(`/companies/${company.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                    <span className="material-symbols-outlined">edit</span>
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); setCompanyToToggle(company); setView('confirmToggle'); }} className={`${company.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={company.is_active ? 'Desativar' : 'Ativar'}>
                                    <span className="material-symbols-outlined">{company.is_active ? 'toggle_off' : 'toggle_on'}</span>
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
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Nome da Empresa</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Contato</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {companies.map(company => (
                                <tr
                                    key={company.id}
                                    onClick={() => navigate(`/companies/${company.id}`)}
                                    className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${!company.is_active ? 'opacity-60' : ''}`}
                                >
                                    <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{company.name}</td>
                                    <td className="py-3 px-4 text-gray-500 dark:text-gray-400">
                                        <div>{company.email}</div>
                                        <div className="text-xs">{maskPhone(company.phone)}</div>
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${company.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                            {company.is_active ? 'Ativa' : 'Inativa'}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-center space-x-2">
                                        <button onClick={(e) => { e.stopPropagation(); navigate(`/companies/${company.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                            <span className="material-symbols-outlined">edit</span>
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setCompanyToToggle(company); setView('confirmToggle'); }} className={`${company.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={company.is_active ? 'Desativar' : 'Ativar'}>
                                            <span className="material-symbols-outlined">{company.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
            <Modal
                isOpen={isInfoModalOpen}
                onClose={() => {
                    setIsInfoModalOpen(false);
                    setNewCompanyInfo(null);
                    navigate('/companies');
                }}
                title="Empresa Criada com Sucesso!"
            >
                {newCompanyInfo && (
                    <div className="space-y-4">
                        <p className="text-green-600 dark:text-green-400 font-semibold">{newCompanyInfo.message}</p>
                        <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg space-y-2 text-sm">
                            <p><strong>URL da Vitrine:</strong> <a href={`#/store/${newCompanyInfo.slug}`} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline break-all">{`${window.location.origin}/#/store/${newCompanyInfo.slug}`}</a></p>
                            <p><strong>URL de Login:</strong> <a href={`#/login`} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline break-all">{`${window.location.origin}/#/login`}</a></p>
                            <p><strong>Email do Gerente:</strong> {newCompanyInfo.admin_email}</p>
                            <p><strong>Senha Temporária:</strong> {newCompanyInfo.admin_password}</p>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            <span className="font-bold">Importante:</span> Copie e envie essas credenciais para o gerente da nova empresa. A senha deverá ser alterada no primeiro login.
                        </p>
                        <div className="flex justify-end gap-2 pt-4">
                            <button
                                type="button"
                                onClick={handleCopyInfo}
                                className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500"
                            >
                                Copiar Dados
                            </button>
                            <button
                                onClick={() => {
                                    setIsInfoModalOpen(false);
                                    setNewCompanyInfo(null);
                                    navigate('/companies');
                                }}
                                className="bg-primary-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-700"
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default CompaniesPage;
