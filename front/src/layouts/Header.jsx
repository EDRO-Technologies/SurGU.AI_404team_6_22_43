import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { LogOut, BrainCircuit, UserCircle, ChevronDown } from 'lucide-react';
import 'tailwindcss/tailwind.css'; // Убедитесь, что Tailwind импортирован

/**
 * Глобальный Хедер (шапка)
 */
export const Header = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm sticky top-0 z-40">
      <div className="container max-w-6xl px-4 py-4 mx-auto">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <BrainCircuit className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-900">KnowledgeBot</span>
          </Link>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-800">{user?.full_name}</div>
              <div className="text-xs text-gray-500">{user?.email}</div>
            </div>
             <UserCircle className="w-8 h-8 text-gray-400" />
            <button
              onClick={handleLogout}
              title="Выйти"
              className="flex items-center justify-center w-10 h-10 text-sm font-medium text-gray-700 bg-gray-100 rounded-full hover:bg-gray-200"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};