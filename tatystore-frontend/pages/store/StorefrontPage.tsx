
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Product, Category, Company } from '../../types';
import ProductCard from '../../components/store/ProductCard';
import Pagination from '../../components/Pagination';
import StoreHeader from '../../components/store/StoreHeader';
import { API_BASE_URL } from '../../config/api';

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

const StorefrontPage: React.FC = () => {
    const { companySlug } = useParams<{ companySlug: string }>();
    const navigate = useNavigate();

    const [company, setCompany] = useState<Company | null>(null);
    const [categories, setCategories] = useState<Category[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [promotionalProducts, setPromotionalProducts] = useState<Product[]>([]);

    const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [totalProducts, setTotalProducts] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [isHeaderVisible, setIsHeaderVisible] = useState(true);
    const lastScrollY = useRef(0);

    const ITEMS_PER_PAGE = 15; // Increased items per page for the denser layout
    const totalPages = Math.ceil(totalProducts / ITEMS_PER_PAGE);

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

    const fetchInitialData = useCallback(async () => {
        if (!companySlug) return;
        setIsLoading(true);
        setError(null);
        try {
            const companyPromise = fetch(`${API_BASE_URL}/public/companies/slug/${companySlug}`);
            const categoriesPromise = fetch(`${API_BASE_URL}/public/companies/${companySlug}/categories`);
            // Fetch products. This endpoint now returns a 'promocao' array with all promotions.
            const promoProductsPromise = fetch(`${API_BASE_URL}/public/companies/${companySlug}/products?limit=15`);

            const [companyRes, categoriesRes, promoRes] = await Promise.all([companyPromise, categoriesPromise, promoProductsPromise]);

            if (!companyRes.ok) throw new Error('Não foi possível encontrar a loja.');
            const companyData = await companyRes.json();
            setCompany(companyData);

            if (categoriesRes.ok) {
                const categoriesData = await categoriesRes.json();
                setCategories(categoriesData.data || categoriesData.items || []);
            }

            if (promoRes.ok) {
                const promoData = await promoRes.json();

                // Check if the API returns a specific 'promocao' array
                if (promoData.promocao && Array.isArray(promoData.promocao)) {
                    // Strictly filter valid promotions: active, on sale, and price > 0
                    const validPromos = promoData.promocao.filter((p: Product) =>
                        p.is_active && p.is_on_sale && (p.promotional_price ?? 0) > 0
                    );
                    setPromotionalProducts(validPromos);
                } else {
                    // Fallback: Filter from the fetched items if 'promocao' array is missing
                    const rawPromoProducts = promoData.data || promoData.items || [];
                    const trulyPromotionalProducts = rawPromoProducts
                        .filter((p: Product) => p.is_active && p.is_on_sale && (p.promotional_price ?? 0) > 0)
                        .slice(0, 8);
                    setPromotionalProducts(trulyPromotionalProducts);
                }
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ocorreu um erro inesperado.');
        } finally {
            setIsLoading(false);
        }
    }, [companySlug]);

    const fetchProducts = useCallback(async () => {
        if (!companySlug) return;
        setIsLoading(true);
        try {
            const params = new URLSearchParams();
            params.append('skip', String((currentPage - 1) * ITEMS_PER_PAGE));
            params.append('limit', String(ITEMS_PER_PAGE));
            if (searchTerm) {
                params.append('search', searchTerm);
            }
            if (selectedCategory) {
                params.append('category_id', String(selectedCategory));
            }

            const response = await fetch(`${API_BASE_URL}/public/companies/${companySlug}/products?${params.toString()}`);
            if (!response.ok) throw new Error('Falha ao buscar produtos.');
            const data = await response.json();

            // Corrected: Handle both 'data' and 'items' structure
            const productList = data.data || data.items || [];

            setProducts(productList);
            setTotalProducts(data.metadata?.total || data.total || 0);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Não foi possível carregar os produtos.');
        } finally {
            setIsLoading(false);
        }
    }, [companySlug, currentPage, selectedCategory, searchTerm]);


    useEffect(() => {
        fetchInitialData();
    }, [fetchInitialData]);

    useEffect(() => {
        const debouncedFetch = setTimeout(() => {
            fetchProducts();
        }, 300);
        return () => clearTimeout(debouncedFetch);
    }, [fetchProducts]);

    useEffect(() => {
        setCurrentPage(1);
    }, [selectedCategory, searchTerm]);

    const handleCategoryClick = (categoryId: number | null) => {
        setSelectedCategory(categoryId);
    };

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen text-center p-4">
                <span className="material-symbols-outlined text-7xl text-red-500">error</span>
                <h1 className="text-3xl font-bold mt-4 text-gray-800 dark:text-gray-100">Oops! Algo deu errado.</h1>
                <p className="text-gray-600 dark:text-gray-300 mt-2">{error}</p>
                <button onClick={() => navigate('/')} className="mt-6 bg-primary-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-primary-700">Voltar ao Início</button>
            </div>
        );
    }

    return (
        <>
            <StoreHeader company={company} companySlug={companySlug!} isVisible={isHeaderVisible} />
            <main className="container mx-auto p-4 sm:p-6">
                {/* Seção de Promoções - Só aparece se houver produtos em promoção */}
                {promotionalProducts.length > 0 && (
                    <section className="mb-12">
                        <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary-600">local_fire_department</span>
                            Nossas Promoções
                        </h2>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">Aproveite nossas ofertas especiais por tempo limitado!</p>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
                            {promotionalProducts.map(product => (
                                <ProductCard key={product.id} product={product} companySlug={companySlug!} />
                            ))}
                        </div>
                    </section>
                )}

                {/* Seção de Todos os Produtos */}
                <section>
                    <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-6">Todos os Produtos</h2>

                    {/* Filtros e Busca */}
                    <div className="mb-6 space-y-4">
                        <div className="flex items-center gap-2 overflow-x-auto pb-2 -mx-2 px-2">
                            <button
                                onClick={() => handleCategoryClick(null)}
                                className={`flex-shrink-0 px-4 py-2 rounded-full whitespace-nowrap text-sm font-semibold transition-colors ${!selectedCategory ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600'}`}
                            >
                                Todas
                            </button>
                            {categories.map(cat => (
                                <button
                                    key={cat.id}
                                    onClick={() => handleCategoryClick(cat.id)}
                                    className={`flex-shrink-0 px-4 py-2 rounded-full whitespace-nowrap text-sm font-semibold transition-colors ${selectedCategory === cat.id ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600'}`}
                                >
                                    {cat.name}
                                </button>
                            ))}
                        </div>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Buscar por nome do produto..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                                className="w-full p-3 pl-10 border rounded-lg shadow-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
                            />
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">search</span>
                        </div>
                    </div>

                    {/* Lista de Produtos */}
                    <div>
                        {isLoading ? (
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
                                {Array.from({ length: 10 }).map((_, i) => (
                                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg animate-pulse border border-gray-200 dark:border-gray-700">
                                        <div className="aspect-square bg-gray-200 dark:bg-gray-700"></div>
                                        <div className="p-4 space-y-3">
                                            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
                                            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                                            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mt-3"></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : products.length > 0 ? (
                            <>
                                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
                                    {products.map(product => (
                                        <ProductCard key={product.id} product={product} companySlug={companySlug!} />
                                    ))}
                                </div>
                                <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
                            </>
                        ) : (
                            <div className="text-center py-16">
                                <span className="material-symbols-outlined text-6xl text-gray-400">search_off</span>
                                <h3 className="text-2xl font-semibold mt-4 text-gray-700 dark:text-gray-200">Nenhum produto encontrado</h3>
                                <p className="text-gray-500 dark:text-gray-400 mt-2">Tente ajustar sua busca ou selecionar outra categoria.</p>
                            </div>
                        )}
                    </div>
                </section>
            </main>
        </>
    );
};

export default StorefrontPage;
