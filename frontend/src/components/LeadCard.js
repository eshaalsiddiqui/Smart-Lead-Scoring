import React from 'react';
import { Phone, Mail, Target, TrendingUp, Building2 } from 'lucide-react';

const LeadCard = ({ lead }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'Call':
        return <Phone className="w-4 h-4" />;
      case 'Email':
        return <Mail className="w-4 h-4" />;
      case 'Nurture':
        return <Target className="w-4 h-4" />;
      default:
        return <Target className="w-4 h-4" />;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'Call':
        return 'bg-blue-100 text-blue-800';
      case 'Email':
        return 'bg-green-100 text-green-800';
      case 'Nurture':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-4">
        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
          <Building2 className="w-5 h-5 text-gray-600" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{lead.company_name}</h4>
          <p className="text-sm text-gray-600">{lead.contact_name}</p>
          <p className="text-xs text-gray-500">{lead.industry}</p>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="text-center">
          <p className="text-sm text-gray-600">Conversion</p>
          <p className="font-semibold text-gray-900">
            {(lead.conversion_probability * 100).toFixed(1)}%
          </p>
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">Revenue Impact</p>
          <p className="font-semibold text-gray-900">
            ${Math.round(lead.revenue_impact).toLocaleString()}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
            {lead.status.toUpperCase()}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getActionColor(lead.next_best_action)}`}>
            {getActionIcon(lead.next_best_action)}
            <span>{lead.next_best_action}</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors">
            <Phone className="w-4 h-4" />
          </button>
          <button className="p-2 text-gray-400 hover:text-green-600 transition-colors">
            <Mail className="w-4 h-4" />
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <TrendingUp className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default LeadCard;
