import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

/**
 * Компонент-обертка для защиты маршрутов.
 * Если пользователь не аутентифицирован, он
 * перенаправляется на страницу /login.
 */
const ProtectedRoute = ({ children }) => {
  const { user } = useContext(AuthContext);

  if (!user) {
    // Перенаправляем на /login, если пользователя нет
    return <Navigate to="/login" replace />;
  }

  // Если пользователь есть, рендерим дочерний компонент
  return children;
};

export default ProtectedRoute;