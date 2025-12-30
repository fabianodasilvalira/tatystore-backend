
import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { useOutletContext, useParams, useNavigate, useLocation } from 'react-router-dom';
import { Product, Category, ProductProfitAnalysis } from '../types';
import { useAuth } from '../App';
import Pagination from '../components/Pagination';
import { logger } from '../utils/logger';

// Context type from App.tsx
interface ProductsContext {
    products: Product[];
    totalProducts: number;
    fetchProducts: (filters: any) => Promise<void>;
    addToast: (message: string, type?: 'success' | 'error') => void;
    categories: Category[];
    serverUrl: string;
    apiUrl: string;
}

const formatCurrency = (value: number | string | undefined | null) => {
    const num = Number(value);
    if (isNaN(num)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num);
};

// --- Back Button Component ---
const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
    <button onClick={onClick} className="hidden md:flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
        <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
        <span className="ml-2 font-semibold">Voltar</span>
    </button>
);


// --- Form Validation and Sub-component ---
interface FormErrors {
    name?: string;
    brand?: string;
    sale_price?: string;
    cost_price?: string;
    stock_quantity?: string;
    min_stock?: string;
    promotional_price?: string;
    category_id?: string;
}

type ProductFormData = Omit<Product, 'id' | 'company_id'>;

interface ProductFormProps {
    initialData: Product | null;
    onSave: (data: ProductFormData, file: File | null) => void;
    onCancel: () => void;
    addToast: (message: string, type?: 'success' | 'error') => void;
    categories: Category[];
    getFullImageUrl: (url: string | null | undefined) => string | null;
    apiUrl: string;
    tokens: { access_token: string } | null;
}

const ProductForm: React.FC<ProductFormProps> = ({ initialData, onSave, onCancel, addToast, categories, getFullImageUrl, apiUrl, tokens }) => {
    const initialFormState: ProductFormData = {
        name: '', brand: '', description: '', sale_price: 0, cost_price: 0,
        stock_quantity: 0, min_stock: 0, sku: '', barcode: '', image_url: '', is_active: true,
        is_on_sale: false, promotional_price: 0, category_id: null
    };
    const [formData, setFormData] = useState(initialFormState);
    const [errors, setErrors] = useState<FormErrors>({});
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>('');
    const cameraInputRef = useRef<HTMLInputElement>(null);
    const galleryInputRef = useRef<HTMLInputElement>(null);

    const [profitAnalysis, setProfitAnalysis] = useState<ProductProfitAnalysis | null>(null);
    const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);

    useEffect(() => {
        if (initialData) {
            setFormData({
                ...initialFormState,
                ...initialData,
            });
            setPreviewUrl(getFullImageUrl(initialData.image_url) || '');
        } else {
            setFormData(initialFormState);
            setPreviewUrl('');
        }
        setSelectedFile(null);
        setErrors({});
    }, [initialData, getFullImageUrl]);

    useEffect(() => {
        if (initialData && tokens) {
            const fetchProfitAnalysis = async () => {
                setIsLoadingAnalysis(true);
                setProfitAnalysis(null);
                try {
                    const response = await fetch(`${apiUrl}/products/${initialData.id}/profit-analysis`, {
                        headers: { 'Authorization': `Bearer ${tokens.access_token}` },
                    });
                    if (!response.ok) {
                        throw new Error('Não foi possível carregar a análise de lucro.');
                    }
                    const data: ProductProfitAnalysis = await response.json();
                    setProfitAnalysis(data);
                } catch (error) {
                    logger.error("Failed to load profit analysis", error, 'ProductForm');
                } finally {
                    setIsLoadingAnalysis(false);
                }
            };

            fetchProfitAnalysis();
        }
    }, [initialData, apiUrl, tokens]);

    const recommendationStyle = useMemo(() => {
        if (!profitAnalysis) return { icon: 'info', color: 'text-gray-500', bgColor: 'bg-gray-100 dark:bg-gray-700' };
        const rec = profitAnalysis.recommendation.toLowerCase();
        if (rec.includes('muito baixa')) return { icon: 'dangerous', color: 'text-red-600 dark:text-red-300', bgColor: 'bg-red-100 dark:bg-red-900/50' };
        if (rec.includes('margem baixa')) return { icon: 'warning', color: 'text-orange-600 dark:text-orange-300', bgColor: 'bg-orange-100 dark:bg-orange-900/50' };
        if (rec.includes('saudável')) return { icon: 'check_circle', color: 'text-green-600 dark:text-green-300', bgColor: 'bg-green-100 dark:bg-green-900/50' };
        if (rec.includes('aceitável')) return { icon: 'info', color: 'text-blue-600 dark:text-blue-300', bgColor: 'bg-blue-100 dark:bg-blue-900/50' };
        return { icon: 'info', color: 'text-gray-500 dark:text-gray-300', bgColor: 'bg-gray-100 dark:bg-gray-700' };
    }, [profitAnalysis]);

    const validate = (): boolean => {
        const newErrors: FormErrors = {};
        if (!formData.name?.trim()) newErrors.name = "O nome do produto é obrigatório.";
        if (!formData.brand?.trim()) newErrors.brand = "A marca é obrigatória.";
        if (isNaN(formData.sale_price) || formData.sale_price <= 0) newErrors.sale_price = "Deve ser um número positivo.";
        if (isNaN(formData.cost_price) || formData.cost_price < 0) newErrors.cost_price = "Deve ser um número não-negativo.";
        if (!Number.isInteger(formData.stock_quantity) || formData.stock_quantity < 0) newErrors.stock_quantity = "Deve ser um número inteiro não-negativo.";
        if (!Number.isInteger(formData.min_stock) || formData.min_stock < 0) newErrors.min_stock = "Deve ser um número inteiro não-negativo.";
        if (formData.is_on_sale && (!formData.promotional_price || formData.promotional_price <= 0)) {
            newErrors.promotional_price = "Preço promocional deve ser um número positivo.";
        }
        if (!formData.category_id) {
            newErrors.category_id = "A categoria é obrigatória.";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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


    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;

        const isNumeric = ['sale_price', 'cost_price', 'promotional_price'].includes(name);
        const isInteger = ['stock_quantity', 'min_stock'].includes(name);

        setFormData(prev => ({
            ...prev,
            [name]: isNumeric ? parseFloat(value) || 0 : isInteger ? parseInt(value, 10) || 0 : value
        }));
    };

    const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setFormData(prev => ({ ...prev, category_id: Number(e.target.value) || null }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (validate()) {
            onSave(formData, selectedFile);
        }
    };

    const getInputClass = (fieldName: keyof FormErrors) =>
        `w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${errors[fieldName] ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`;

    return (
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome do Produto</label>
                <input type="text" name="name" value={formData.name} onChange={handleChange} className={getInputClass('name')} required />
                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Marca</label>
                <input type="text" name="brand" value={formData.brand || ''} onChange={handleChange} className={getInputClass('brand')} required />
                {errors.brand && <p className="text-red-500 text-xs mt-1">{errors.brand}</p>}
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                <select
                    name="category_id"
                    value={formData.category_id || ''}
                    onChange={handleCategoryChange}
                    className={getInputClass('category_id')}
                >
                    <option value="">Selecione uma categoria</option>
                    {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                </select>
                {errors.category_id && <p className="text-red-500 text-xs mt-1">{errors.category_id}</p>}
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea name="description" value={formData.description} onChange={handleChange} rows={3} className="w-full p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600" />
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-4">
                <div className="w-24 h-24 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center border dark:border-gray-600 flex-shrink-0">
                    <img
                        src={previewUrl || 'https://placehold.co/96x96/f1f5f9/9ca3af?text=Foto'}
                        alt="Pré-visualização"
                        className="w-full h-full rounded-lg object-cover"
                    />
                </div>
                <div className="flex-1 w-full">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Foto do Produto</label>
                    <input
                        id="photo-upload-desktop"
                        type="file"
                        accept="image/png, image/jpeg, image/webp"
                        onChange={handlePhotoChange}
                        className="hidden md:block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-700/20 dark:file:text-primary-300 dark:hover:file:bg-primary-700/30 cursor-pointer"
                    />
                    <div className="block md:hidden space-y-2 w-full">
                        <button
                            type="button"
                            onClick={() => cameraInputRef.current?.click()}
                            className="w-full flex items-center justify-center gap-2 p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                        >
                            <span className="material-symbols-outlined">photo_camera</span>
                            Tirar Foto
                        </button>
                        <button
                            type="button"
                            onClick={() => galleryInputRef.current?.click()}
                            className="w-full flex items-center justify-center gap-2 p-2 border rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                        >
                            <span className="material-symbols-outlined">photo_library</span>
                            Escolher da Galeria
                        </button>
                    </div>
                    <input
                        ref={cameraInputRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handlePhotoChange}
                        className="hidden"
                    />
                    <input
                        ref={galleryInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handlePhotoChange}
                        className="hidden"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">PNG, JPG, WEBP (Máx 5MB).</p>
                </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço de Custo</label>
                    <input type="number" step="0.01" name="cost_price" value={formData.cost_price} onChange={handleChange} className={getInputClass('cost_price')} required />
                    {errors.cost_price && <p className="text-red-500 text-xs mt-1">{errors.cost_price}</p>}
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço de Venda</label>
                    <input type="number" step="0.01" name="sale_price" value={formData.sale_price} onChange={handleChange} className={getInputClass('sale_price')} required />
                    {errors.sale_price && <p className="text-red-500 text-xs mt-1">{errors.sale_price}</p>}
                </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estoque Atual</label>
                    <input type="number" name="stock_quantity" value={formData.stock_quantity} onChange={handleChange} className={getInputClass('stock_quantity')} required />
                    {errors.stock_quantity && <p className="text-red-500 text-xs mt-1">{errors.stock_quantity}</p>}
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estoque Mínimo</label>
                    <input type="number" name="min_stock" value={formData.min_stock} onChange={handleChange} className={getInputClass('min_stock')} required />
                    {errors.min_stock && <p className="text-red-500 text-xs mt-1">{errors.min_stock}</p>}
                </div>
            </div>

            <div className="border-t dark:border-gray-700 pt-4 mt-4">
                <div className="flex items-center justify-between">
                    <div>
                        <label htmlFor="is_on_sale" className="font-medium text-gray-700 dark:text-gray-300">Produto em Promoção</label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Ative para definir um preço promocional.</p>
                    </div>
                    <button type="button" id="is_on_sale" onClick={() => setFormData(prev => ({ ...prev, is_on_sale: !prev.is_on_sale }))} className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors ${formData.is_on_sale ? 'bg-primary-600' : 'bg-gray-300'}`}>
                        <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform ${formData.is_on_sale ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                </div>
                {formData.is_on_sale && (
                    <div className="mt-4 animate-fade-in">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço Promocional</label>
                        <input type="number" step="0.01" name="promotional_price" value={formData.promotional_price || ''} onChange={handleChange} className={getInputClass('promotional_price')} required />
                        {errors.promotional_price && <p className="text-red-500 text-xs mt-1">{errors.promotional_price}</p>}
                    </div>
                )}
            </div>

            {initialData && (
                <div className="border-t dark:border-gray-700 pt-4 mt-4 space-y-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary-600">query_stats</span>
                        Análise de Lucratividade
                    </h3>
                    {isLoadingAnalysis ? (
                        <div className="text-center py-4">
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
                            <p className="text-sm text-gray-500 mt-2">Calculando...</p>
                        </div>
                    ) : profitAnalysis ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                                <div className="bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Lucro (Normal)</p>
                                    <p className="font-bold text-gray-800 dark:text-gray-200">{formatCurrency(profitAnalysis.normal_profit)}</p>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Margem (Normal)</p>
                                    <p className="font-bold text-gray-800 dark:text-gray-200">{profitAnalysis.normal_margin_percentage.toFixed(1)}%</p>
                                </div>
                                {profitAnalysis.promotional_profit !== null && (
                                    <>
                                        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                                            <p className="text-xs text-blue-600 dark:text-blue-400">Lucro (Promo)</p>
                                            <p className="font-bold text-blue-700 dark:text-blue-300">{formatCurrency(profitAnalysis.promotional_profit)}</p>
                                        </div>
                                        <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                                            <p className="text-xs text-blue-600 dark:text-blue-400">Margem (Promo)</p>
                                            <p className="font-bold text-blue-700 dark:text-blue-300">{profitAnalysis.promotional_margin_percentage?.toFixed(1)}%</p>
                                        </div>
                                    </>
                                )}
                            </div>
                            <div className={`flex items-start gap-3 p-4 rounded-lg ${recommendationStyle.bgColor}`}>
                                <span className={`material-symbols-outlined mt-0.5 ${recommendationStyle.color}`}>{recommendationStyle.icon}</span>
                                <div>
                                    <h4 className={`font-semibold text-sm ${recommendationStyle.color}`}>Recomendação do Sistema</h4>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{profitAnalysis.recommendation}</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <p className="text-sm text-gray-500 dark:text-gray-400 italic">Análise indisponível.</p>
                    )}
                </div>
            )}

            <div className="flex justify-end gap-4 pt-4 border-t dark:border-gray-700">
                <button type="button" onClick={onCancel} className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-2 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors">Cancelar</button>
                <button type="submit" className="bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700 transition-colors">Salvar Produto</button>
            </div>
        </form>
    );
};


const Products: React.FC = () => {
    const { products, totalProducts, fetchProducts, addToast, categories, serverUrl, apiUrl } = useOutletContext<ProductsContext>();
    const { productId } = useParams<{ productId: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { tokens } = useAuth();

    const [view, setView] = useState<'list' | 'form' | 'confirmToggle'>('list');
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCategory, setFilterCategory] = useState('');
    const [showInactive, setShowInactive] = useState(false);
    const [productToToggle, setProductToToggle] = useState<Product | null>(null);
    const [currentPage, setCurrentPage] = useState(1);

    const ITEMS_PER_PAGE = 20;
    const totalPages = Math.ceil(totalProducts / ITEMS_PER_PAGE);

    const productForForm = useMemo(() => {
        if (!productId || productId === 'new') return null;
        return products.find(p => String(p.id) === String(productId)) ?? null;
    }, [productId, products]);

    const getFullImageUrl = useCallback((relativeOrFullUrl: string | undefined | null): string => {
        const placeholder = 'https://placehold.co/400x400/f1f5f9/9ca3af?text=PrimeStore';
        if (!relativeOrFullUrl) return placeholder;
        if (relativeOrFullUrl.startsWith('http://') || relativeOrFullUrl.startsWith('https://')) {
            return relativeOrFullUrl;
        }
        return `${serverUrl.replace(/\/$/, '')}/${relativeOrFullUrl.replace(/^\//, '')}`;
    }, [serverUrl]);

    useEffect(() => {
        if (view === 'list') {
            const debouncedFetch = setTimeout(() => {
                fetchProducts({
                    page: currentPage,
                    searchTerm,
                    showInactive,
                    category_id: filterCategory
                });
            }, 300);
            return () => clearTimeout(debouncedFetch);
        }
    }, [fetchProducts, currentPage, view, searchTerm, showInactive, filterCategory]);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, showInactive, filterCategory]);

    useEffect(() => {
        if (productId) {
            setView('form');
        } else {
            setView('list');
        }
    }, [productId]);

    const handleSaveProduct = async (formData: ProductFormData, file: File | null) => {
        if (!tokens) return;
        const isEditing = !!productForForm;
        const method = isEditing ? 'PUT' : 'POST';
        const url = isEditing ? `${apiUrl}/products/${productForForm.id}` : `${apiUrl}/products/`;

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
                throw new Error(errorData.detail || `Falha ao ${isEditing ? 'atualizar' : 'criar'} produto.`);
            }

            let savedProduct = await response.json();

            if (file) {
                const formDataImage = new FormData();
                formDataImage.append('file', file);

                const imageResponse = await fetch(`${apiUrl}/products/${savedProduct.id}/image`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${tokens.access_token}` },
                    body: formDataImage
                });

                if (!imageResponse.ok) {
                    addToast('Produto salvo, mas falha ao enviar imagem.', 'error');
                }
            }

            addToast(`Produto ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
            navigate('/products');
            await fetchProducts({ page: 1, showInactive });
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        }
    };

    const handleToggleStatus = async () => {
        if (!productToToggle || !tokens) return;

        const method = productToToggle.is_active ? 'DELETE' : 'PUT';
        const url = `${apiUrl}/products/${productToToggle.id}`;

        // For activating, we might need to send body. For deactivating (DELETE), usually no body.
        // Assuming backend handles PUT for reactivation with body or simple toggle.
        // Based on other pages, let's send full body for PUT.

        let fetchOptions: RequestInit = {
            method,
            headers: { 'Authorization': `Bearer ${tokens.access_token}` }
        };

        if (method === 'PUT') {
            fetchOptions.headers = {
                ...fetchOptions.headers,
                'Content-Type': 'application/json'
            };
            // Construct body excluding ID and read-only fields if necessary, 
            // but assuming backend accepts the object and we just flip is_active.
            // Usually DELETE disables, PUT updates. To re-enable, we likely need to PUT with is_active=true.
            const body = {
                ...productToToggle,
                is_active: true,
                category_id: productToToggle.category_id || productToToggle.category?.id // Ensure category_id is set
            };
            // Remove complex objects if backend expects IDs
            delete (body as any).category;

            fetchOptions.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, fetchOptions);

            if (!response.ok && response.status !== 204) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Falha ao atualizar status do produto.');
            }

            addToast('Status do produto atualizado com sucesso!');
            await fetchProducts({ page: currentPage, searchTerm, showInactive });
        } catch (err) {
            addToast(err instanceof Error ? err.message : 'Ocorreu um erro.', 'error');
        } finally {
            setView('list');
            setProductToToggle(null);
        }
    };

    if (view === 'confirmToggle' && productToToggle) {
        const actionText = productToToggle.is_active ? 'desativar' : 'ativar';
        const confirmButtonColor = productToToggle.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700';
        return (
            <div>
                <BackButton onClick={() => setView('list')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">Confirmar Ação</h1>
                    <p className="text-gray-600 dark:text-gray-300 mb-6">
                        Tem certeza que deseja {actionText} o produto "{productToToggle.name}"?
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
        if (productId !== 'new' && !productForForm) {
            return (
                <div>
                    <BackButton onClick={() => navigate('/products')} />
                    <div className="text-center p-8 text-gray-500 dark:text-gray-400">Carregando dados do produto...</div>
                </div>
            );
        }
        return (
            <div>
                <BackButton onClick={() => navigate('/products')} />
                <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                    <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
                        {productForForm ? 'Editar Produto' : 'Novo Produto'}
                    </h1>
                    <ProductForm
                        initialData={productForForm}
                        onSave={handleSaveProduct}
                        onCancel={() => navigate('/products')}
                        addToast={addToast}
                        categories={categories}
                        getFullImageUrl={getFullImageUrl}
                        apiUrl={apiUrl}
                        tokens={tokens}
                    />
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-6">
                <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto flex-1">
                    <div className="relative w-full md:w-80">
                        <input
                            type="text"
                            placeholder="Buscar por nome, marca..."
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
                    <select
                        value={filterCategory}
                        onChange={e => setFilterCategory(e.target.value)}
                        className="w-full sm:w-48 p-3 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                    >
                        <option value="">Todas Categorias</option>
                        {categories.map(cat => (
                            <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                    </select>
                </div>
                <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
                    <label className="flex items-center cursor-pointer whitespace-nowrap p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
                        <input type="checkbox" checked={showInactive} onChange={() => setShowInactive(!showInactive)} className="mr-2 h-4 w-4 rounded text-primary-600 focus:ring-primary-500" />
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Mostrar inativos</span>
                    </label>
                    <button onClick={() => navigate('/products/import')} className="flex w-full sm:w-auto items-center justify-center gap-2 bg-blue-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-blue-700 transition-colors">
                        <span className="material-symbols-outlined">upload_file</span>
                        Importar CSV
                    </button>
                    <button onClick={() => navigate('/products/new')} className="flex w-full sm:w-auto items-center justify-center gap-2 bg-primary-600 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:bg-primary-700 transition-colors">
                        <span className="material-symbols-outlined">add</span>
                        Novo Produto
                    </button>
                </div>
            </div>

            <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-300">
                    <span className="font-bold">{totalProducts}</span> produto(s) encontrado(s).
                </p>
            </div>

            {/* Mobile List View */}
            <div className="md:hidden space-y-4">
                {products.map(product => (
                    <div
                        key={product.id}
                        onClick={() => navigate(`/products/${product.id}`)}
                        className={`bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 flex gap-4 ${!product.is_active ? 'opacity-60' : ''}`}
                    >
                        <div className="w-20 h-20 flex-shrink-0 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                            <img
                                src={getFullImageUrl(product.image_url)}
                                alt={product.name}
                                className="w-full h-full object-cover"
                            />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start">
                                <h3 className="font-bold text-gray-800 dark:text-gray-100 truncate pr-2">{product.name}</h3>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0 ${product.stock_quantity > 0 ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                    {product.stock_quantity > 0 ? `${product.stock_quantity} un` : 'Esgotado'}
                                </span>
                            </div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{product.brand}</p>
                            <div className="flex justify-between items-end mt-2">
                                <div>
                                    {product.is_on_sale && product.promotional_price && product.promotional_price > 0 ? (
                                        <div className="flex flex-col">
                                            <span className="font-bold text-lg text-red-600 dark:text-red-400">
                                                {formatCurrency(product.promotional_price)}
                                            </span>
                                            <span className="text-xs text-gray-400 line-through">
                                                {formatCurrency(product.sale_price)}
                                            </span>
                                        </div>
                                    ) : (
                                        <p className="font-bold text-lg text-primary-600 dark:text-primary-400">
                                            {formatCurrency(product.sale_price)}
                                        </p>
                                    )}
                                </div>
                                <div className="space-x-1">
                                    <button onClick={(e) => { e.stopPropagation(); navigate(`/products/${product.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                        <span className="material-symbols-outlined">edit</span>
                                    </button>
                                    <button onClick={(e) => { e.stopPropagation(); setProductToToggle(product); setView('confirmToggle'); }} className={`${product.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={product.is_active ? 'Desativar' : 'Ativar'}>
                                        <span className="material-symbols-outlined">{product.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Desktop Table View */}
            <div className="hidden md:block bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-md">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="border-b-2 border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 w-16">Foto</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Produto</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300">Categoria</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Preço</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Estoque</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Status</th>
                                <th className="py-3 px-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products.length === 0 ? (
                                <tr><td colSpan={7} className="text-center py-10 text-gray-500 dark:text-gray-400">Nenhum produto encontrado.</td></tr>
                            ) : (
                                products.map(product => (
                                    <tr
                                        key={product.id}
                                        onClick={() => navigate(`/products/${product.id}`)}
                                        className={`border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${!product.is_active ? 'opacity-60' : ''}`}
                                    >
                                        <td className="py-2 px-4">
                                            <div className="w-10 h-10 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                                                <img src={getFullImageUrl(product.image_url)} alt="" className="w-full h-full object-cover" />
                                            </div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="font-medium text-gray-800 dark:text-gray-200">{product.name}</div>
                                            <div className="text-xs text-gray-500 dark:text-gray-400">{product.brand}</div>
                                        </td>
                                        <td className="py-3 px-4 text-gray-600 dark:text-gray-300">{product.category?.name || '-'}</td>
                                        <td className="py-3 px-4 text-right font-semibold text-gray-800 dark:text-gray-200">
                                            {product.is_on_sale && product.promotional_price && product.promotional_price > 0 ? (
                                                <div className="flex flex-col items-end">
                                                    <span className="text-red-600 dark:text-red-400 font-bold">
                                                        {formatCurrency(product.promotional_price)}
                                                    </span>
                                                    <span className="text-xs text-gray-400 line-through">
                                                        {formatCurrency(product.sale_price)}
                                                    </span>
                                                </div>
                                            ) : (
                                                formatCurrency(product.sale_price)
                                            )}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${product.stock_quantity > product.min_stock ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'}`}>
                                                {product.stock_quantity}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${product.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300'}`}>
                                                {product.is_active ? 'Ativo' : 'Inativo'}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-center space-x-2">
                                            <button onClick={(e) => { e.stopPropagation(); navigate(`/products/${product.id}`); }} className="text-blue-600 hover:text-blue-800 p-1 rounded-full" title="Editar">
                                                <span className="material-symbols-outlined">edit</span>
                                            </button>
                                            <button onClick={(e) => { e.stopPropagation(); setProductToToggle(product); setView('confirmToggle'); }} className={`${product.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'} p-1 rounded-full`} title={product.is_active ? 'Desativar' : 'Ativar'}>
                                                <span className="material-symbols-outlined">{product.is_active ? 'toggle_off' : 'toggle_on'}</span>
                                            </button>
                                        </td>
                                    </tr>
                                )))}
                        </tbody>
                    </table>
                </div>
            </div>

            <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
        </div>
    );
};

export default Products;
