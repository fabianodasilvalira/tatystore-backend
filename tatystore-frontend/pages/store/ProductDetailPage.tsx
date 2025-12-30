import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Product, Company } from '../../types';
import ProductCard from '../../components/store/ProductCard';
import StoreHeader from '../../components/store/StoreHeader';
import { API_BASE_URL, SERVER_BASE_URL, getFullImageUrl as getFullImageUrlFromConfig } from '../../config/api';
import { logger } from '../../utils/logger';

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const applyTheme = (themeColor: string | null | undefined) => {
    const color = themeColor || 'purple'; // Fallback to purple
    const colors: { [key: string]: { [key: string]: string } } = {
        purple: { '50': '#F5F3FF', '100': '#EDE9FE', '300': '#C4B5FD', '600': '#7C3AED', '700': '#6D28D9' },
        blue: { '50': '#EFF6FF', '100': '#DBEAFE', '300': '#93C5FD', '600': '#2563EB', '700': '#1D4ED8' },
        green: { '50': '#F0FDF4', '100': '#DCFCE7', '300': '#86EFAC', '600': '#16A34A', '700': '#15803D' },
        pink: { '50': '#FDF2F8', '100': '#FCE7F3', '300': '#F9A8D4', '600': '#DB2777', '700': '#BE185D' },
        white: { '50': '#F9FAFB', '100': '#F3F4F6', '300': '#D1D5DB', '600': '#4B5563', '700': '#374151' },
        black: { '50': '#F8FAFC', '100': '#F1F5F9', '300': '#CBD5E1', '600': '#475569', '700': '#334155' }
    };
    const root = document.documentElement;
    const selectedPalette = colors[color] || colors.purple;
    for (const [shade, colorValue] of Object.entries(selectedPalette)) {
        root.style.setProperty(`--color-primary-${shade}`, colorValue);
    }
};

const ProductDetailPage: React.FC = () => {
    const { companySlug, productId } = useParams<{ companySlug: string; productId: string }>();
    const navigate = useNavigate();

    const [product, setProduct] = useState<Product | null>(null);
    const [company, setCompany] = useState<Company | null>(null);
    const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isHeaderVisible, setIsHeaderVisible] = useState(true);
    const lastScrollY = useRef(0);

    useEffect(() => {
        const handleScroll = () => {
            const currentScrollY = window.scrollY;
            if (currentScrollY > lastScrollY.current && currentScrollY > 100) {
                setIsHeaderVisible(false); // Scrolling down
            } else {
                setIsHeaderVisible(true); // Scrolling up or at the top
            }
            lastScrollY.current = currentScrollY;
        };

        window.addEventListener('scroll', handleScroll, { passive: true });

        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    useEffect(() => {
        if (company?.theme_color) {
            applyTheme(company.theme_color);
        }
    }, [company]);

    useEffect(() => {
        const fetchDetails = async () => {
            if (!companySlug || !productId) return;
            setIsLoading(true);
            setError(null);
            setSimilarProducts([]);
            try {
                const productPromise = fetch(`${API_BASE_URL}/public/companies/${companySlug}/products/${productId}`);
                const companyPromise = fetch(`${API_BASE_URL}/public/companies/slug/${companySlug}`);

                const [productRes, companyRes] = await Promise.all([productPromise, companyPromise]);

                if (!productRes.ok || !companyRes.ok) {
                    throw new Error('Não foi possível encontrar o produto ou a loja.');
                }

                const productData = await productRes.json();
                const companyData = await companyRes.json();

                setProduct(productData);
                setCompany(companyData);

                // Fetch similar products after getting the main product's category
                if (productData.category?.id) {
                    fetch(`${API_BASE_URL}/public/companies/${companySlug}/products?category_id=${productData.category.id}&limit=11`)
                        .then(res => res.ok ? res.json() : Promise.resolve([]))
                        .then(similarData => {
                            const similarList = Array.isArray(similarData) ? similarData : (similarData.data || similarData.items || []);
                            const filteredList = similarList
                                .filter((p: Product) => String(p.id) !== String(productId))
                                .slice(0, 10);
                            setSimilarProducts(filteredList);
                        })
                        .catch(err => logger.error("Failed to fetch similar products", err, 'ProductDetailPage')); // Non-critical
                }

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Ocorreu um erro inesperado.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchDetails();
        window.scrollTo(0, 0); // Scroll to top when product changes
    }, [companySlug, productId]);

    const handleWhatsAppContact = () => {
        if (!company?.phone || !product) return;
        const phone = company.phone.replace(/\D/g, '');
        const message = encodeURIComponent(`Olá, ${company.name}! Tenho interesse no produto "${product.name}". Poderia me dar mais informações?`);
        window.open(`https://wa.me/55${phone}?text=${message}`, '_blank');
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-screen bg-gray-100 dark:bg-gray-900">
                <p className="text-gray-600 dark:text-gray-300">Carregando produto...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen text-center p-4">
                <span className="material-symbols-outlined text-7xl text-red-500">error</span>
                <h1 className="text-3xl font-bold mt-4 text-gray-800 dark:text-gray-100">Oops! Algo deu errado.</h1>
                <p className="text-gray-600 dark:text-gray-300 mt-2">{error}</p>
                <button onClick={() => navigate(`/store/${companySlug}`)} className="mt-6 bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700">Voltar para a Loja</button>
            </div>
        );
    }

    if (!product) return null;

    return (
        <>
            <StoreHeader company={company} companySlug={companySlug!} isVisible={isHeaderVisible} />
            <main className="container mx-auto p-4 sm:p-6 lg:p-8">
                <button onClick={() => navigate(`/store/${companySlug}`)} className="flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-6 group">
                    <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
                    <span className="ml-2 font-semibold">Voltar para a loja</span>
                </button>
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                    <div className="grid grid-cols-1 md:grid-cols-2">
                        {/* Imagem do Produto */}
                        <div className="p-4 sm:p-6">
                            <div className="aspect-square rounded-xl overflow-hidden relative group">
                                <img
                                    src={getFullImageUrlFromConfig(product.image_url)}
                                    alt={product.name}
                                    className="w-full h-full object-cover transition-transform duration-500 ease-in-out group-hover:scale-105"
                                />
                                {product.is_on_sale && product.promotional_price && (
                                    <div className="absolute top-4 right-4 bg-red-500 text-white text-sm font-bold px-3 py-1.5 rounded-full shadow-lg">
                                        PROMOÇÃO!
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Detalhes do Produto */}
                        <div className="p-6 sm:p-8 flex flex-col">
                            <div className="flex-grow">
                                {product.category && (
                                    <p className="text-sm font-semibold text-primary-600 dark:text-primary-400 uppercase tracking-wider">{product.category.name}</p>
                                )}
                                <h1 className="text-3xl lg:text-4xl font-extrabold text-gray-800 dark:text-gray-100 mt-2">{product.name}</h1>
                                {product.brand && <p className="text-lg text-gray-500 dark:text-gray-400 mt-1">{product.brand}</p>}

                                <div className="my-6">
                                    {product.is_on_sale && product.promotional_price ? (
                                        <div className="flex items-baseline gap-3">
                                            <p className="text-4xl font-bold text-red-500">{formatCurrency(product.promotional_price)}</p>
                                            <p className="text-2xl font-semibold text-gray-400 line-through">{formatCurrency(product.sale_price)}</p>
                                        </div>
                                    ) : (
                                        <p className="text-4xl font-bold text-gray-800 dark:text-gray-100">{formatCurrency(product.sale_price)}</p>
                                    )}
                                </div>

                                <div className="border-t border-gray-200 dark:border-gray-700 pt-6 mt-6">
                                    {product.stock_quantity > 0 ? (
                                        <div className={`flex items-center gap-2 p-3 rounded-lg ${product.stock_quantity <= product.min_stock
                                            ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200'
                                            : 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200'
                                            }`}>
                                            <span className="material-symbols-outlined">inventory_2</span>
                                            <p className="font-semibold">
                                                {product.stock_quantity <= product.min_stock
                                                    ? `Corra, últimas ${product.stock_quantity} unidades!`
                                                    : `${product.stock_quantity} unidades disponíveis`}
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200">
                                            <span className="material-symbols-outlined">production_quantity_limits</span>
                                            <p className="font-semibold">Produto Esgotado</p>
                                        </div>
                                    )}
                                </div>

                                {product.description && (
                                    <div className="prose dark:prose-invert text-gray-600 dark:text-gray-300 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                                        <h3 className="font-semibold text-gray-800 dark:text-gray-200">Sobre o produto:</h3>
                                        <p>{product.description}</p>
                                    </div>
                                )}
                            </div>

                            <div className="mt-8">
                                <button
                                    onClick={handleWhatsAppContact}
                                    disabled={!company?.phone || product.stock_quantity <= 0}
                                    className="w-full flex items-center justify-center gap-3 bg-primary-600 text-white font-bold py-4 px-6 rounded-lg shadow-lg hover:bg-primary-700 transition-transform hover:scale-105 disabled:bg-gray-400 disabled:cursor-not-allowed"
                                >
                                    <span className="material-symbols-outlined">call</span>
                                    {product.stock_quantity > 0 ? 'Chamar no WhatsApp' : 'Produto Esgotado'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {!isLoading && similarProducts.length > 0 && (
                    <section className="mt-16">
                        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Produtos Similares</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
                            {similarProducts.map(p => (
                                <ProductCard key={p.id} product={p} companySlug={companySlug!} />
                            ))}
                        </div>
                    </section>
                )}
            </main>
        </>
    );
};

export default ProductDetailPage;