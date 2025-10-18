// src/components/SavedNewsCard.jsx

import React from "react";
import { Link } from "react-router-dom";
import fallbackImage from "../../assets/news-placeholder.jpg"; // Importa a imagem de fallback

const SavedNewsCard = ({ news, onRemove }) => {
  // Função para lidar com o clique na remoção.
  // Previne a navegação para a página da notícia.
  const handleRemoveClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onRemove(news.id);
  };

  return (
    <div
      className="
        relative group rounded-lg overflow-hidden 
        transition-all duration-300 ease-in-out
        hover:scale-[1.02]
        font-montserrat
      "
    >
      {/* A etiqueta de salvo e botão de remoção */}
      <button
        onClick={handleRemoveClick}
        title="Remover das notícias salvas"
        className="absolute top-2 left-0 px-1.5 py-1 bg-gray-300 text-black z-10 transition-colors hover:bg-gray-400"
      >
        <svg className="h-4 w-5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
        </svg>
      </button>

      {/* Link para a página da notícia */}
      <Link to={`/article/${news.id}`} className="block">
        {/* Imagem */}
        <img
          src={news.image}
          alt={news.title}
          // Se a imagem da API falhar, o navegador tentará carregar o fallbackImage
          onError={(e) => (e.currentTarget.src = fallbackImage)}
          className="w-full h-48 object-cover"
        />

        {/* Container de Texto */}
        <div className="mt-3">
          <h3 className="text-base font-bold text-gray-900 mb-2 font-montserrat">
            {news.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-3 font-montserrat">
            {news.summary}
          </p>
        </div>
      </Link>
    </div>
  );
};

export default SavedNewsCard;
