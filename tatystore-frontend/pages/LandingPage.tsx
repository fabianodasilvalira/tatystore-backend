import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const carouselImages = [
    {
        src: '/banners/banner1.jpeg',
        alt: 'Mulher escolhendo produtos de beleza em uma loja bem iluminada',
        title: 'Sua Vitrine Online, Pronta para Vender',
        subtitle: 'Exponha seus produtos, compartilhe o link com seus clientes e alcance um público maior sem esforço.'
    },
    {
        src: '/banners/banner2.jpeg',
        alt: 'Pessoa realizando um pagamento por aproximação em uma máquina de cartão',
        title: 'Crediário e Cobrança Simplificados',
        subtitle: 'Gerencie parcelamentos, identifique atrasos e envie lembretes de cobrança via WhatsApp com apenas um clique.'
    },
    {
        src: '/banners/banner3.jpeg',
        alt: 'Mulher analisando gráficos de dados em um laptop',
        title: 'Decisões Inteligentes com Gráficos Detalhados',
        subtitle: 'Visualize suas vendas diárias, semanais e mensais, e analise suas margens de lucro para impulsionar seu crescimento.'
    },
    {
        src: '/banners/banner4.jpeg',
        alt: 'Coleção de bolsas de couro elegantes em exibição',
        title: 'Controle Total do Seu Estoque',
        subtitle: 'De perfumes a bolsas, gerencie cada item, evite perdas e saiba exatamente quando é hora de recomprar.'
    },
    {
        src: '/banners/banner5.jpeg',
        alt: 'Loja de perfumaria com prateleiras cheias de produtos',
        title: 'Gestão Completa na Palma da Sua Mão',
        subtitle: 'Do estoque ao financeiro, tenha o controle total do seu negócio de onde estiver.'
    },
];

const features = [
    { icon: 'dashboard', title: 'Dashboard em Tempo Real', description: 'Acompanhe suas vendas com gráficos diários, semanais e mensais. Tenha uma visão clara da saúde do seu negócio a qualquer momento.' },
    { icon: 'store', title: 'Sua Vitrine Online', description: 'Exponha seus produtos em uma vitrine digital personalizada e compartilhe facilmente com seus clientes para impulsionar as vendas.' },
    { icon: 'credit_card_off', title: 'Gestão de Crediário', description: 'Controle parcelas, identifique pagamentos em atraso com um clique e gerencie as contas a receber de forma simples e eficaz.' },
    { icon: 'sms', title: 'Cobrança por WhatsApp', description: 'Envie lembretes de pagamento e cobranças de parcelas vencidas diretamente para o WhatsApp do cliente, com mensagens prontas.' },
    { icon: 'inventory_2', title: 'Controle de Estoque', description: 'Gerencie produtos, categorias, preços e níveis de estoque mínimo para nunca mais perder uma venda por falta de mercadoria.' },
    { icon: 'bar_chart', title: 'Relatórios de Lucratividade', description: 'Analise suas margens de lucro, identifique os produtos mais rentáveis e tome decisões estratégicas baseadas em dados concretos.' },
];

const howItWorksSteps = [
    { icon: 'person_add', title: 'Cadastre-se', description: 'Crie sua conta e configure as informações básicas da sua empresa em poucos minutos.' },
    { icon: 'add_business', title: 'Organize seu Negócio', description: 'Importe ou cadastre seus produtos, clientes e categorias para ter tudo sob controle.' },
    { icon: 'shopping_cart', title: 'Comece a Vender', description: 'Utilize nossa frente de caixa para registrar vendas, gerenciar pagamentos e crediários.' },
    { icon: 'monitoring', title: 'Analise e Cresça', description: 'Acompanhe seus resultados através dos relatórios e dashboards para impulsionar seu crescimento.' },
];


const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    const [currentSlide, setCurrentSlide] = useState(0);
    const sectionsRef = useRef<(HTMLElement | null)[]>([]);
    const [isHeaderVisible, setIsHeaderVisible] = useState(true);
    const lastScrollY = useRef(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % carouselImages.length);
        }, 5000);
        return () => clearInterval(timer);
    }, []);

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
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                    }
                });
            },
            { threshold: 0.1 }
        );

        sectionsRef.current.forEach((section) => {
            if (section) observer.observe(section);
        });

        return () => {
            sectionsRef.current.forEach((section) => {
                if (section) observer.unobserve(section);
            });
        };
    }, []);

    return (
        <div className="bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 font-sans">
            <style>{`
                .fade-in-section {
                    opacity: 0;
                    transform: translateY(20px);
                    transition: opacity 0.6s ease-out, transform 0.6s ease-out;
                }
                .fade-in-section.is-visible {
                    opacity: 1;
                    transform: translateY(0);
                }
            `}</style>

            {/* Header */}
            <header className={`fixed top-0 left-0 right-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm shadow-md transition-transform duration-300 ${isHeaderVisible ? 'translate-y-0' : '-translate-y-full'}`}>
                <div className="container mx-auto px-6 py-2 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <img src="/app-logo.png" alt="Taty Store Logo" className="max-h-16 w-auto" />
                    </div>
                    <button
                        onClick={() => navigate('/login')}
                        className="group relative inline-flex items-center justify-center px-6 py-2 text-sm font-bold text-white bg-primary-600 rounded-lg overflow-hidden shadow-lg transition-all duration-300 ease-in-out hover:shadow-primary-300/50"
                    >
                        <span className="absolute left-0 top-0 w-full h-full bg-gradient-to-r from-primary-700 to-primary-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                        <span className="relative z-10 flex items-center gap-2">
                            <span className="material-symbols-outlined">login</span>
                            Acessar Sistema
                        </span>
                    </button>
                </div>
            </header>

            <main>
                {/* Hero Carousel Section */}
                <section className="relative w-full h-[80vh] md:h-screen text-white overflow-hidden">
                    {carouselImages.map((image, index) => (
                        <div
                            key={index}
                            className={`absolute top-0 left-0 w-full h-full transition-opacity duration-1000 ease-in-out ${index === currentSlide ? 'opacity-100' : 'opacity-0'}`}
                        >
                            <img src={image.src} alt={image.alt} className="w-full h-full object-cover" />
                            <div className="absolute top-0 left-0 w-full h-full bg-black/60"></div>
                        </div>
                    ))}
                    <div className="relative z-10 flex flex-col items-center justify-center h-full text-center px-6">
                        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight">
                            {carouselImages[currentSlide].title}
                        </h1>
                        <p className="mt-4 max-w-2xl text-lg md:text-xl text-gray-300">
                            {carouselImages[currentSlide].subtitle}
                        </p>
                        <button onClick={() => navigate('/login')} className="mt-8 bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition-transform hover:scale-105 shadow-lg">
                            Comece a Gerenciar Agora
                        </button>
                    </div>
                </section>

                {/* Features Section */}
                <section ref={el => { sectionsRef.current[0] = el; }} className="py-20 bg-white dark:bg-gray-800 fade-in-section">
                    <div className="container mx-auto px-6 text-center">
                        <h2 className="text-4xl font-bold mb-4">A solução completa para o seu negócio</h2>
                        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-12">Tudo o que você precisa para gerenciar sua loja de forma eficiente, aumentar suas vendas e encantar seus clientes.</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {features.map((feature, index) => (
                                <div key={index} className="p-8 bg-gray-50 dark:bg-gray-700/50 rounded-xl shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300">
                                    <span className="material-symbols-outlined text-5xl text-primary-600">{feature.icon}</span>
                                    <h3 className="text-2xl font-bold mt-4 mb-2">{feature.title}</h3>
                                    <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* How It Works Section */}
                <section ref={el => { sectionsRef.current[1] = el; }} className="py-20 fade-in-section">
                    <div className="container mx-auto px-6 text-center">
                        <h2 className="text-4xl font-bold mb-12">Simples de Começar, Poderoso para Crescer</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
                            {howItWorksSteps.map((step, index) => (
                                <div key={index} className="flex flex-col items-center">
                                    <div className="bg-primary-100 dark:bg-primary-900/50 text-primary-600 dark:text-primary-300 rounded-full p-5 mb-4">
                                        <span className="material-symbols-outlined text-4xl">{step.icon}</span>
                                    </div>
                                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                                    <p className="text-gray-600 dark:text-gray-400">{step.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Contact Section */}
                <section ref={el => { sectionsRef.current[2] = el; }} className="py-20 bg-primary-600 text-white fade-in-section">
                    <div className="container mx-auto px-6 text-center">
                        <h2 className="text-4xl font-bold mb-4">Pronto para transformar sua gestão?</h2>
                        <p className="text-lg text-primary-100 max-w-2xl mx-auto mb-8">Entre em contato conosco para tirar suas dúvidas ou solicitar uma demonstração.</p>
                        <a href="https://wa.me/5586998181489" target="_blank" rel="noopener noreferrer" className="bg-white text-primary-600 font-bold py-3 px-8 rounded-lg text-lg transition-transform hover:scale-105 shadow-lg">
                            Fale Conosco
                        </a>
                    </div>
                </section>
            </main>

            {/* Footer */}
            <footer className="bg-gray-800 text-gray-400">
                <div className="container mx-auto px-6 py-8 text-center">
                    <p>&copy; {new Date().getFullYear()} PrimeStore. Todos os direitos reservados.</p>
                    <p className="text-sm mt-2">Uma solução de Fabiano Lira</p>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;