import React, { useState, useEffect } from "react";
import HeaderFeedPage from "../components/FeedPage/HeaderFeedPage";
import SavedNewsCard from "../components/SavedNews/SavedNewsCard";
import RemoveConfirmationModal from "../components/SavedNews/RemoveConfirmationModal";
import SavedNewsCardSkeleton from "../components/SavedNews/SavedNewsCardSkeleton";
import { usersAPI } from "../services/api";

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
  {
    id: 6,
    title: "Novo estudo revela benefícios do café para a memória a longo prazo",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
    image: "https://via.placeholder.com/400x250/a16207/FFFFFF",
    isSaved: true,
  },
];

const SavedNewsPage = () => {
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newsToRemove, setNewsToRemove] = useState(null);
  const [userData, setUserData] = useState({ email: "" });

  useEffect(() => {
    const fetchPageData = async () => {
      setLoading(true);

      try {
        // Busca os dados do usuário e as notícias salvas (simulação)
        const userProfile = await usersAPI.getUserProfile();
        setUserData(userProfile.data);
      } catch (error) {
        console.error("Failed to fetch user data:", error);
        // Opcional: exibir uma notificação de erro para o usuário
      }

      // Simulação de carregamento das notícias salvas
      setSavedNews(MOCK_SAVED_NEWS);
      setLoading(false);
    };

    fetchPageData();
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

  return (
    <div className="bg-gray-50 min-h-screen flex flex-col font-montserrat">
      <HeaderFeedPage userEmail={userData.email} />

      <main className="flex-grow max-w-6xl mx-auto sm:px-6 lg:px-8 mt-12 w-full">
        <h1 className="p-3 text-3xl font-medium text-gray-900 font-montserrat text-center">
          Your saved news
        </h1>

        {loading ? (
          // Estado de carregamento
          <div className="flex flex-wrap justify-center gap-8 mt-12 p-4">
            {/* Renderize 6 esqueletos para corresponder ao layout */}
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="w-full sm:w-1/2 md:w-1/3 lg:w-[30%] xl:w-1/4"
              >
                <SavedNewsCardSkeleton />
              </div>
            ))}
          </div>
        ) : savedNews.length === 0 ? (
          // Estado de lista vazia
          <div className="text-center py-16">
            <p className="text-xl text-gray-600 mb-4">
              Você ainda não salvou nenhuma notícia.
            </p>
          </div>
        ) : (
          // Lista de notícias salvas
          <div className="p-4 flex flex-wrap justify-center gap-8 mt-12">
            {savedNews.map((news) => (
              <div
                key={news.id}
                className="w-full sm:w-1/2 md:w-1/3 lg:w-[30%] xl:w-1/4"
              >
                <SavedNewsCard news={news} onRemove={handleConfirmRemove} />
              </div>
            ))}
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
