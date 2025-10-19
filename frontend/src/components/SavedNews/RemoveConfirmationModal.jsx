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
      <div className="bg-white rounded-sm shadow-xl p-6 w-full max-w-sm relative font-montserrat">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-red-500 hover:text-red-700 rounded-full hover:bg-gray-100 p-0.2"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Confirm Removal
        </h2>
        <p className="text-sm text-gray-700 mb-6">
          Do you want to remove this item from your saved news?
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="w-24 h-11 flex items-center justify-center bg-gray-200 text-gray-800 text-xs font-bold px-2 rounded-sm hover:bg-gray-300 transition-colors font-montserrat"
          >
            Cancel
          </button>
          {/* Botão de remoção com estilo primário (preto) */}
          <button
            onClick={onConfirm}
            className="w-24 h-11 flex items-center justify-center bg-black text-white text-xs font-bold px-2 rounded-sm hover:bg-gray-800 transition-colors font-montserrat"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  );
};

export default RemoveConfirmationModal;
