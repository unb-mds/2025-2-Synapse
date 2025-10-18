import React, { useState, useEffect } from "react";
import HeaderNewsPage from "../components/NewsPage/HeaderNewsPage";
import SavedNewsCard from "../components/SavedNews/SavedNewsCard";
import RemoveConfirmationModal from "../components/SavedNews/RemoveConfirmationModal";
import SavedNewsCardSkeleton from "../components/SavedNews/SavedNewsCardSkeleton";

const MOCK_SAVED_NEWS = [
  {
    id: 1,
    title:
      "A resposta oficial da Apple aos arranhões no iPhone 17. Entenda o caso do ScratchGate",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/1e293b/FFFFFF",
    isSaved: true,
  },
  {
    id: 2,
    title:
      "Astrônomos detectam anã branca que 'engoliu' mundo gelado parecido com Plutão",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/2563EB/FFFFFF",
    isSaved: true,
  },
  {
    id: 3,
    title: "Google completa 27 anos com doodle especial",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/ef4444/FFFFFF",
    isSaved: true,
  },
  {
    id: 4,
    title: "12 filmes para acompanhar a disputa pelo Oscar 2026",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/000000/FFFFFF",
    isSaved: true,
  },
  {
    id: 5,
    title: "What's the big deal about AI data centres?",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/84cc16/FFFFFF",
    isSaved: true,
  },
];

const SavedNewsPage = () => {
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newsToRemove, setNewsToRemove] = useState(null);

  useEffect(() => {
    // Simulação de carregamento e população com dados mockados
    setTimeout(() => {
      setSavedNews(MOCK_SAVED_NEWS);
      setLoading(false);
    }, 800);
  }, []);

  // 1. Abre o modal de confirmação
  const handleConfirmRemove = (newsId) => {
    setNewsToRemove(newsId);
    setShowModal(true);
  };

  // 2. Executa a remoção localmente
  const handleRemoveNews = () => {
    if (newsToRemove) {
      // Em produção: chamada DELETE para o backend aqui.

      // Remove localmente do estado para atualização imediata da interface
      setSavedNews((prevNews) =>
        prevNews.filter((news) => news.id !== newsToRemove)
      );

      setNewsToRemove(null);
      setShowModal(false);
    }
  };

  const userEmail = "*@email.com";

  return (
    <div className="bg-gray-50 min-h-screen flex flex-col font-montserrat">
      <HeaderNewsPage userEmail={userEmail} />

      <main className="flex-grow max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-21 py-12 w-full">
        <h1 className="text-3xl font-normal text-gray-900 font-montserrat text-center mb-10">
          Your saved news
        </h1>

        {loading ? (
          // Estado de carregamento
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-11">
            {/* Renderize 3 esqueletos, simulando a visualização inicial */}
            <SavedNewsCardSkeleton />
            <SavedNewsCardSkeleton />
            <SavedNewsCardSkeleton />
          </div>
        ) : savedNews.length === 0 ? (
          // Estado de lista vazia
          <div className="text-center py-16">
            <p className="text-xl text-gray-600 mb-4">
              Você ainda não salvou nenhuma notícia.
            </p>
          </div>
        ) : (
          // Container principal com posicionamento relativo para o efeito de fade
          <div className="relative mt-11">
            {/* Container de Rolagem com altura fixa */}
            {/* Grid de Notícias Salvas com 3 colunas */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {savedNews.map((news) => (
                <SavedNewsCard
                  key={news.id}
                  news={news}
                  onRemove={handleConfirmRemove}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Modal de Confirmação */}
      <RemoveConfirmationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={handleRemoveNews}
      />
    </div>
  );
};

export default SavedNewsPage;
