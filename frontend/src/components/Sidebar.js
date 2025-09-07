import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  BarChart3, 
  MessageSquare, 
  Settings,
  Zap
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Leads', href: '/leads', icon: Users },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'AI Assistant', href: '/chatbot', icon: MessageSquare },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-white shadow-lg">
      <div className="p-6">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-gray-900">Smart CRM</h1>
        </div>
        <p className="text-sm text-gray-500 mt-1">Lead Scoring Platform</p>
      </div>
      
      <nav className="mt-8">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="absolute bottom-0 w-64 p-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">AI</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">AI Status</p>
              <p className="text-xs text-green-600">Model Active</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
