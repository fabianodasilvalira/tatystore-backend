import React, { useState, useEffect, useCallback } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { Company } from '../types';
import { maskPhone, maskCNPJ, validateEmail, unmask } from '../utils/formatters';
import { logger } from '../utils/logger';
import { getFullUrl } from '../utils/urlUtils';

interface CompanyPageContext {
    companyDetails: Company | null;
    updateCompanyDetails: (companyData: Partial<Company>, logoFile: File | null) => Promise<void>;
    addToast: (message: string, type?: 'success' | 'error') => void;
    serverUrl: string;
}

type CompanyFormData = {
    name: string;
    cnpj: string;
    email: string;
    phone: string;
    address: string;
    pix: {
        pix_key: string;
        pix_type: string;
    } | null;
};

// getFullUrl agora importado de utils/urlUtils.ts

const CompanyPage: React.FC = () => {
    const { companyDetails, updateCompanyDetails, addToast, serverUrl } = useOutletContext<CompanyPageContext>();
    const navigate = useNavigate();

    const [formData, setFormData] = useState<CompanyFormData | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (companyDetails) {
            let parsedPix = null;
            if (typeof companyDetails.pix === 'string') {
                try {
                    parsedPix = JSON.parse(companyDetails.pix);
                } catch (e) {
                    logger.error("Failed to parse PIX data", e, 'CompanyPage');
                    parsedPix = { pix_key: '', pix_type: '' };
                }
            } else if (typeof companyDetails.pix === 'object' && companyDetails.pix !== null) {
                parsedPix = companyDetails.pix;
            } else {
                parsedPix = { pix_key: '', pix_type: '' };
            }

            setFormData({
                name: companyDetails.name,
                cnpj: maskCNPJ(companyDetails.cnpj),
                email: companyDetails.email,
                phone: maskPhone(companyDetails.phone),
                address: companyDetails.address,
                pix: parsedPix,
            });
            setPreviewUrl(getFullUrl(companyDetails.logo_url, serverUrl));
        }
    }, [companyDetails, serverUrl]);

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

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        let { name, value } = e.target;
        if (name === 'pix_key' || name === 'pix_type') {
            setFormData(prev => prev ? {
                ...prev,
                pix: {
                    ...(prev.pix || { pix_key: '', pix_type: '' }),
                    [name]: value
                }
            } : null);
        } else {
            if (name === 'phone') value = maskPhone(value);
            if (name === 'cnpj') value = maskCNPJ(value);
            setFormData(prev => prev ? { ...prev, [name]: value } : null);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData) {
            addToast('Não foi possível carregar os dados da empresa.', 'error');
            return;
        }
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

        setIsLoading(true);
        try {
            const dataToSend = {
                ...formData,
                cnpj: unmask(formData.cnpj),
                phone: unmask(formData.phone),
            };
            await updateCompanyDetails(dataToSend, selectedFile);
        } catch (error) {
            // Error is already handled by the context function
        } finally {
            setIsLoading(false);
        }
    };

    if (!companyDetails || !formData) {
        return <div className="text-center p-8 text-gray-500 dark:text-gray-400">Carregando dados da empresa...</div>;
    }

    return (
        <div className="space-y-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <h2 className="text-xl font-bold mb-1 text-gray-800 dark:text-gray-100">Dados da Empresa</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">Mantenha as informações da sua empresa sempre atualizadas.</p>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="flex flex-col sm:flex-row items-center gap-6 p-4 border rounded-lg dark:border-gray-700">
                        <div className="w-24 h-24 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center border dark:border-gray-600 flex-shrink-0">
                            <img
                                src={previewUrl || 'https://placehold.co/96x96/f1f5f9/9ca3af?text=Logo'}
                                alt="Pré-visualização do logo"
                                className="w-full h-full rounded-lg object-cover"
                            />
                        </div>
                        <div className="flex-1 w-full">
                            <label htmlFor="logo-upload" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Logo da Empresa</label>
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome da Empresa</label>
                            <input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
                            <input type="text" name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email de Contato</label>
                            <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone / WhatsApp</label>
                            <input type="tel" name="phone" value={formData.phone} onChange={handleChange} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço Completo</label>
                        <textarea name="address" value={formData.address} onChange={handleChange} rows={3} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
                    </div>
                    <div className="col-span-1 md:col-span-2 border-t dark:border-gray-700 pt-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Informações de Pagamento (PIX)</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo de Chave PIX</label>
                                <select
                                    name="pix_type"
                                    value={formData.pix?.pix_type || ''}
                                    onChange={handleChange}
                                    className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                                >
                                    <option value="">Não informado</option>
                                    <option value="cpf_cnpj">CPF/CNPJ</option>
                                    <option value="email">E-mail</option>
                                    <option value="phone">Telefone</option>
                                    <option value="random">Chave Aleatória</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Chave PIX</label>
                                <input
                                    type="text"
                                    name="pix_key"
                                    value={formData.pix?.pix_key || ''}
                                    onChange={handleChange}
                                    className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                                    placeholder="Sua chave PIX"
                                />
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-end gap-4 pt-4 mt-4 border-t dark:border-gray-700">
                        <button
                            type="submit"
                            className="bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors disabled:bg-primary-300"
                            disabled={isLoading}
                        >
                            {isLoading ? 'Salvando...' : 'Salvar Alterações'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CompanyPage;