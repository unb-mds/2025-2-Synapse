import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import BackIcon from "../../icons/back-svgrepo-com.svg";
import ArrowDownIcon from "../../icons/arrow-down.svg";
import { usersAPI } from "../../services/api";

// Função auxiliar para ler um cookie pelo nome
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

const HeaderNewsPage = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const navigate = useNavigate();

  // Buscar dados do usuário
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await usersAPI.getUserProfile();
        setUserEmail(response.data.email || "");
      } catch (err) {
        console.error("Failed to fetch user data:", err);
      }
    };

    fetchUserData();
  }, []);

  // Função de logout
  const handleLogout = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL;
      const csrfToken = getCookie("csrf_access_token");

      await fetch(`${apiUrl}/users/logout`, {
        method: "POST",
        headers: { "X-CSRF-TOKEN": csrfToken },
        credentials: "include",
      });
    } finally {
      navigate("/login"); // redireciona para login, mesmo se a chamada falhar
    }
  };

  return (
    <>
      <header className="flex justify-between items-center p-6 bg-white border-b border-gray-100 relative">
        {/* Lado esquerdo: Botão "Back to feed" */}
        <Link
          to="/feed"
          className="flex items-center text-gray-800 hover:text-gray-600"
        >
          <img src={BackIcon} alt="Ícone de Voltar" className="w-5 h-5 mr-2" />
          <span className="font-medium font-montserrat">Back to feed</span>
        </Link>

        {/* Meio: Logo Synapse */}
        <h1 className="text-lg font-bold text-black font-rajdhani">Synapse</h1>

        {/* Lado direito: Menu do usuário */}
        <div className="relative">
          <button
            className="flex items-center rounded-md text-gray-800 hover:text-gray-600 focus:outline-none text-sm font-montserrat"
            onClick={() => setDropdownOpen((open) => !open)}
          >
            <span className="font-medium font-montserrat">{userEmail}</span>
            <img
              src={ArrowDownIcon}
              alt="Ícone de Seta para Baixo"
              className="ml-2 w-4 h-4"
            />
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-xl shadow-lg z-10 text-xs font-montserrat">
              <Link
                to="/account"
                className="block px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                onClick={() => setDropdownOpen(false)}
              >
                My Account
              </Link>
              <button>
                <Link
                  to="/saved-news"
                  className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                  onClick={() => setDropdownOpen(false)}
                >
                  Saved News
                </Link>
              </button>
              <hr className="border-gray-200" />
              <button
                onClick={handleLogout}
                className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
      <div className="w-full h-px bg-gray-200"></div>
    </>
  );
};

export default HeaderNewsPage;
