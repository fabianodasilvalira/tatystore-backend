import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { API_BASE_URL } from '../config/api';

interface ImportResult {
    total_linhas: number;
    sucessos: number;
    erros: number;
    detalhes: {
        criados: Array<{ linha: number; nome: string; sku: string }>;
        erros: Array<{ linha: number; erro: string }>;
    };
}

const ProductImport: React.FC = () => {
    const navigate = useNavigate();
    const { tokens } = useAuth();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [importResult, setImportResult] = useState<ImportResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileSelect = (file: File) => {
        if (!file.name.endsWith('.csv')) {
            setError('Apenas arquivos CSV são permitidos');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            setError('Arquivo muito grande. Máximo 5MB');
            return;
        }

        setSelectedFile(file);
        setError(null);
        setImportResult(null);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileSelect(file);
        }
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            handleFileSelect(file);
        }
    };

    const handleDownloadTemplate = async () => {
        if (!tokens) return;

        try {
            const response = await fetch(`${API_BASE_URL}/products/import/template`, {
                headers: {
                    'Authorization': `Bearer ${tokens.access_token}`
                }
            });

            if (!response.ok) {
                throw new Error('Falha ao baixar template');
            }

            const data = await response.json();

            // Criar e baixar arquivo CSV
            const blob = new Blob([data.content], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = data.filename;
            link.click();
            URL.revokeObjectURL(link.href);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao baixar template');
        }
    };

    const handleImport = async () => {
        if (!selectedFile || !tokens) return;

        setIsUploading(true);
        setError(null);
        setImportResult(null);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const response = await fetch(`${API_BASE_URL}/products/import`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${tokens.access_token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Falha ao importar produtos');
            }

            const result: ImportResult = await response.json();
            setImportResult(result);
            setSelectedFile(null);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao importar produtos');
        } finally {
            setIsUploading(false);
        }
    };

    const handleExportErrors = () => {
        if (!importResult || importResult.detalhes.erros.length === 0) return;

        const csvContent = 'Linha,Erro\n' +
            importResult.detalhes.erros.map(e => `${e.linha},"${e.erro}"`).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'erros_importacao.csv';
        link.click();
        URL.revokeObjectURL(link.href);
    };

    return (
        <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <button
                    onClick={() => navigate('/products')}
                    className="flex items-center text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-300 mb-4 group"
                >
                    <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
                    <span className="ml-2 font-semibold">Voltar para Produtos</span>
                </button>

                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">Importação em Massa de Produtos</h1>
                <p className="text-gray-600 dark:text-gray-300 mt-2">
                    Importe centenas de produtos de uma vez usando arquivo CSV
                </p>
            </div>

            {/* Instruções */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 mt-0.5">info</span>
                    <div className="flex-1">
                        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Como usar:</h3>
                        <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800 dark:text-blue-200">
                            <li>Baixe o template CSV clicando no botão abaixo</li>
                            <li>Preencha com os dados dos seus produtos</li>
                            <li>Use <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">ativo=false</code> para produtos que precisam de ajuste de preço</li>
                            <li>Faça upload do arquivo preenchido</li>
                            <li>Revise o relatório de importação</li>
                        </ol>
                    </div>
                </div>
            </div>

            {/* Download Template */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 mb-6">
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary-600">download</span>
                    Template CSV
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-4">
                    Baixe o template com exemplos e categorias da sua empresa
                </p>
                <button
                    onClick={handleDownloadTemplate}
                    className="flex items-center gap-2 bg-primary-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-primary-700 transition-colors"
                >
                    <span className="material-symbols-outlined">file_download</span>
                    Baixar Template CSV
                </button>
            </div>

            {/* Upload Area */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 mb-6">
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary-600">upload_file</span>
                    Upload do Arquivo
                </h2>

                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragging
                            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'
                        }`}
                >
                    <span className="material-symbols-outlined text-6xl text-gray-400 dark:text-gray-500 mb-4">cloud_upload</span>
                    <p className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
                        {selectedFile ? selectedFile.name : 'Arraste o arquivo CSV aqui'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        ou clique para selecionar (máximo 5MB)
                    </p>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv"
                        onChange={handleFileInputChange}
                        className="hidden"
                    />
                </div>

                {selectedFile && (
                    <div className="mt-4 flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-green-600 dark:text-green-400">check_circle</span>
                            <div>
                                <p className="font-semibold text-gray-800 dark:text-gray-100">{selectedFile.name}</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    {(selectedFile.size / 1024).toFixed(2)} KB
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedFile(null);
                            }}
                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                        >
                            <span className="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                )}

                {error && (
                    <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
                            <span className="material-symbols-outlined">error</span>
                            <p className="font-semibold">{error}</p>
                        </div>
                    </div>
                )}

                <div className="mt-6 flex gap-4">
                    <button
                        onClick={handleImport}
                        disabled={!selectedFile || isUploading}
                        className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isUploading ? (
                            <>
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                Importando...
                            </>
                        ) : (
                            <>
                                <span className="material-symbols-outlined">upload</span>
                                Importar Produtos
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Resultado da Importação */}
            {importResult && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6">
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary-600">assessment</span>
                        Relatório de Importação
                    </h2>

                    {/* Resumo */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-center">
                            <p className="text-sm text-blue-600 dark:text-blue-400 mb-1">Total de Linhas</p>
                            <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">{importResult.total_linhas}</p>
                        </div>
                        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg text-center">
                            <p className="text-sm text-green-600 dark:text-green-400 mb-1">Sucessos</p>
                            <p className="text-3xl font-bold text-green-700 dark:text-green-300">{importResult.sucessos}</p>
                        </div>
                        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg text-center">
                            <p className="text-sm text-red-600 dark:text-red-400 mb-1">Erros</p>
                            <p className="text-3xl font-bold text-red-700 dark:text-red-300">{importResult.erros}</p>
                        </div>
                    </div>

                    {/* Produtos Criados */}
                    {importResult.detalhes.criados.length > 0 && (
                        <div className="mb-6">
                            <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
                                <span className="material-symbols-outlined text-green-600">check_circle</span>
                                Produtos Criados ({importResult.detalhes.criados.length})
                            </h3>
                            <div className="max-h-60 overflow-y-auto bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                {importResult.detalhes.criados.slice(0, 10).map((item, index) => (
                                    <div key={index} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 py-1">
                                        <span className="text-gray-400">Linha {item.linha}:</span>
                                        <span className="font-semibold">{item.nome}</span>
                                        <span className="text-gray-500">({item.sku})</span>
                                    </div>
                                ))}
                                {importResult.detalhes.criados.length > 10 && (
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 italic">
                                        ... e mais {importResult.detalhes.criados.length - 10} produtos
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Erros */}
                    {importResult.detalhes.erros.length > 0 && (
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-red-600">error</span>
                                    Erros Encontrados ({importResult.detalhes.erros.length})
                                </h3>
                                <button
                                    onClick={handleExportErrors}
                                    className="text-sm flex items-center gap-1 text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                                >
                                    <span className="material-symbols-outlined text-sm">download</span>
                                    Exportar Erros
                                </button>
                            </div>
                            <div className="max-h-60 overflow-y-auto bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                                {importResult.detalhes.erros.map((item, index) => (
                                    <div key={index} className="text-sm text-red-800 dark:text-red-200 py-2 border-b border-red-200 dark:border-red-800 last:border-0">
                                        <span className="font-semibold">Linha {item.linha}:</span> {item.erro}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Ações */}
                    <div className="mt-6 flex gap-4">
                        <button
                            onClick={() => navigate('/products')}
                            className="flex-1 bg-primary-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-primary-700 transition-colors"
                        >
                            Ver Produtos Importados
                        </button>
                        <button
                            onClick={() => {
                                setImportResult(null);
                                setSelectedFile(null);
                            }}
                            className="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 font-bold py-3 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                        >
                            Nova Importação
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProductImport;
