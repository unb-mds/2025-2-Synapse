import React from "react";
import ReactDOM from "react-dom/client";
import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
} from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./index.css";

import LoginPage from "./pages/LoginPage";
import AboutPage from "./pages/AboutPage";
import RegisterPage from "./pages/RegisterPage.jsx";
import EditAccount from "./pages/EditAccount.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import AccountPage from "./pages/AccountPage";
import PublicRoute from "./components/PublicRoute.jsx";
import PrivateRoute from "./components/PrivateRoute.jsx";
import FeedPage from "./pages/FeedPage.jsx";
import NewsPage from "./pages/NewsPage.jsx";
import SavedNewsPage from "./pages/SavedNewsPage.jsx";

// Cria o objeto de configuração do roteador
const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/feed" replace />,
  },
  {
    path: "/sobre",
    element: <AboutPage />,
  },
  {
    // Rotas públicas restritas (APENAS para usuários não logados)
    element: <PublicRoute />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/registrar",
        element: <RegisterPage />,
      },
    ],
  },
  {
    // Rotas privadas (apenas para usuários logados)
    element: <PrivateRoute />,
    children: [
      { path: "/feed", element: <FeedPage /> },
      { path: "/article/:id", element: <NewsPage /> },
      { path: "/account", element: <AccountPage /> },
      { path: "/edit-account", element: <EditAccount /> },
      { path: "/change-password", element: <ChangePassword /> },
      { path: "/saved-news", element: <SavedNewsPage /> },
    ],
  },
]);

// Renderiza o "Provedor de Rota" em vez do componente diretamente
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
    <ToastContainer
      position="bottom-right"
      autoClose={5000}
      hideProgressBar={false}
      theme="dark"
    />
  </React.StrictMode>
);
