// src/components/RemoveSaveIcon.jsx

import React from "react";

/**
 * Componente de ícone de salvar (marcador), usado aqui como botão de remoção
 * na página de notícias salvas.
 * @param {function} onRemove - Função chamada ao clicar para iniciar a remoção.
 */
const RemoveSaveIcon = ({ onRemove }) => {
  // A função mais importante: evita que o clique no ícone abra a notícia.
  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onRemove(); // Chama a função que inicia o modal de remoção
  };

  return (
    <button
      onClick={handleClick}
      // Estilo do botão: Fundo branco e ícone preto, conforme seu Design System
      className="absolute top-3 right-3 p-1 rounded-full bg-white bg-opacity-90 hover:bg-opacity-100 transition-all duration-200 z-10 shadow-md"
      title="Remover das notícias salvas"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        // Cor do ícone: Preto, sempre preenchido para indicar que está salvo.
        className="h-6 w-6 text-black"
        fill="currentColor"
        viewBox="0 0 24 24"
        stroke="black"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
        />
      </svg>
    </button>
  );
};

export default RemoveSaveIcon;
