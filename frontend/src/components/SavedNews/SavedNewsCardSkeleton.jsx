// src/components/SavedNews/SavedNewsCardSkeleton.jsx

import React from "react";

const SavedNewsCardSkeleton = () => {
  return (
    <div className="rounded-lg overflow-hidden shadow-md bg-white animate-pulse">
      {/* Imagem */}
      <div className="w-full h-48 bg-gray-300"></div>

      {/* Container de Texto */}
      <div className="p-4">
        {/* Título */}
        <div className="h-4 bg-gray-300 rounded w-3/4 mb-3"></div>
        <div className="h-4 bg-gray-300 rounded w-1/2 mb-4"></div>
        {/* Resumo */}
        <div className="h-3 bg-gray-300 rounded w-full mb-2"></div>
        <div className="h-3 bg-gray-300 rounded w-full"></div>
      </div>
    </div>
  );
};

export default SavedNewsCardSkeleton;
