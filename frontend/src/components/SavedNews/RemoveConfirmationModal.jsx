// src/components/RemoveConfirmationModal.jsx

import React from "react";

// Ícone simples de fechar (X)
const CloseIcon = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className="w-6 h-6"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M6 18L18 6M6 6l12 12"
    />
  </svg>
);

const RemoveConfirmationModal = ({ isOpen, onClose, onConfirm }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 font-montserrat">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
          title="Fechar"
        >
          <CloseIcon className="h-6 w-6" />
        </button>

        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Confirmar Remoção
        </h2>
        <p className="text-gray-700 mb-6">
          Deseja remover este item das notícias salvas?
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Cancelar
          </button>
          {/* Botão de remoção com estilo primário (preto) */}
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            Remover
          </button>
        </div>
      </div>
    </div>
  );
};

export default RemoveConfirmationModal;
