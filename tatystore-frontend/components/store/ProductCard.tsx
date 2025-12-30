import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Product } from '../../types';
import { getFullImageUrl } from '../../config/api';

interface ProductCardProps {
    product: Product;
    companySlug: string;
}

const formatCurrency = (value: number | undefined) => {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
};

const ProductCard: React.FC<ProductCardProps> = ({ product, companySlug }) => {
    const navigate = useNavigate();

    const handleCardClick = () => {
        navigate(`/store/${companySlug}/products/${product.id}`);
    };

    const isPromo = product.is_on_sale && product.promotional_price && product.promotional_price > 0;
    const displayPrice = isPromo ? product.promotional_price! : product.sale_price;
    const originalPrice = isPromo ? product.sale_price : null;

    return (
        <div
            onClick={handleCardClick}
            className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden group transition-all duration-300 ease-in-out cursor-pointer flex flex-col h-full border border-gray-200 dark:border-gray-700 hover:shadow-2xl hover:-translate-y-1"
        >
            <div className="relative">
                <div className="aspect-square w-full overflow-hidden bg-gray-100 dark:bg-gray-700">
                    <img
                        src={getFullImageUrl(product.image_url)}
                        alt={product.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-in-out"
                    />
                </div>
                {product.stock_quantity <= 0 && (
                    <div className="absolute inset-0 bg-white/70 dark:bg-black/70 flex items-center justify-center">
                        <span className="font-bold text-gray-800 dark:text-gray-100">ESGOTADO</span>
                    </div>
                )}
                {isPromo && product.stock_quantity > 0 && (
                    <div className="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-md">
                        OFERTA
                    </div>
                )}
            </div>

            <div className="p-4 flex flex-col flex-grow text-left">
                <p className="text-xs text-gray-500 dark:text-gray-400 uppercase font-medium">
                    {product.brand || product.category?.name || <span className="invisible">placeholder</span>}
                </p>
                <h3 className="font-semibold text-base mt-1 text-gray-800 dark:text-gray-100 flex-grow" title={product.name}>
                    {product.name}
                </h3>

                <div className="mt-3">
                    {originalPrice && (
                        <p className="text-sm text-gray-400 line-through">{formatCurrency(originalPrice)}</p>
                    )}
                    <p className={`font-bold text-lg ${isPromo ? 'text-red-500' : 'text-gray-900 dark:text-gray-50'}`}>
                        {formatCurrency(displayPrice)}
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ProductCard;