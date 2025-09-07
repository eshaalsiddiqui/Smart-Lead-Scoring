import React from 'react';
import { Settings as SettingsIcon, User, Bell, Shield, Database } from 'lucide-react';

const Settings = () => {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account and application preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center space-x-3 mb-4">
            <User className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Profile</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                defaultValue="John Doe"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                defaultValue="john@example.com"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
              Save Changes
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center space-x-3 mb-4">
            <Bell className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Notifications</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Email notifications</span>
              <input type="checkbox" defaultChecked className="rounded" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">High priority alerts</span>
              <input type="checkbox" defaultChecked className="rounded" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Weekly reports</span>
              <input type="checkbox" className="rounded" />
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Security</h2>
          </div>
          <div className="space-y-4">
            <button className="w-full text-left px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
              Change Password
            </button>
            <button className="w-full text-left px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
              Two-Factor Authentication
            </button>
            <button className="w-full text-left px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
              API Keys
            </button>
          </div>
        </div>

        {/* Data & Model */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center space-x-3 mb-4">
            <Database className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Data & Model</h2>
          </div>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p>Model Status: <span className="text-green-600 font-medium">Active</span></p>
              <p>Last Training: 2 hours ago</p>
              <p>Accuracy: 89.2%</p>
            </div>
            <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
              Retrain Model
            </button>
            <button className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50">
              Export Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
