import React, { useContext } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthContext } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

// --- Импорт страниц ---
import { LoginPage } from './pages/LoginPage'
// import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { WorkspaceLayout } from './layouts/WorkspaceLayout'

// --- Импорт вкладок Воркспейса ---
import { WorkspaceKnowledge } from './pages/workspace/WorkspaceKnowledge'
import { WorkspaceChat } from './pages/workspace/WorkspaceChat'
import { WorkspaceAnalytics } from './pages/workspace/WorkspaceAnalytics'
import { WorkspaceTickets } from './pages/workspace/WorkspaceTickets'
import { WorkspaceSettings } from './pages/workspace/WorkspaceSettings'

/**
 * Главный компонент приложения
 * Отвечает за основной роутинг
 */
export default function App() {
  const { user, loading } = useContext(AuthContext)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="ml-4 text-lg font-medium text-gray-700">Загрузка...</p>
      </div>
    )
  }

  return (
    <Routes>
      {/* Публичные маршруты */}
      <Route
        path="/login"
        element={user ? <Navigate to="/" /> : <LoginPage />}
      />
      {/* <Route
        path="/register"
        element={user ? <Navigate to="/" /> : <RegisterPage />}
      /> */}

      {/* Приватные маршруты (требуют аутентификации) */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Вложенные маршруты для Воркспейса */}
      <Route
        path="/workspace/:workspaceId"
        element={
          <ProtectedRoute>
            <WorkspaceLayout />
          </ProtectedRoute>
        }
      >
        {/* Редирект по умолчанию на вкладку "Знания" */}
        <Route index element={<Navigate to="knowledge" replace />} />

        <Route path="knowledge" element={<WorkspaceKnowledge />} />
        <Route path="chat" element={<WorkspaceChat />} />
        <Route path="analytics" element={<WorkspaceAnalytics />} />
        <Route path="tickets" element={<WorkspaceTickets />} />
        <Route path="settings" element={<WorkspaceSettings />} />
      </Route>

      {/* Редирект, если страница не найдена */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}