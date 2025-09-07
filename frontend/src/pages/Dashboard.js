import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  DollarSign, 
  Phone, 
  Mail, 
  Target,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import LeadCard from '../components/LeadCard';
import { apiService } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalLeads: 0,
    conversionRate: 0,
    totalRevenue: 0,
    highPriorityLeads: 0
  });
  const [topLeads, setTopLeads] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch health status
      const healthResponse = await apiService.getHealth();
      
      // Mock data for demonstration - in production, this would come from your API
      const mockStats = {
        totalLeads: 1247,
        conversionRate: 0.23,
        totalRevenue: 2840000,
        highPriorityLeads: 89
      };
      
      const mockTopLeads = [
        {
          id: 'LEAD_001',
          company: 'TechCorp Inc.',
          contact: 'John Smith',
          industry: 'Technology',
          conversionProb: 0.89,
          revenueImpact: 45000,
          nextAction: 'Call',
          status: 'high'
        },
        {
          id: 'LEAD_002',
          company: 'Finance Solutions',
          contact: 'Sarah Johnson',
          industry: 'Finance',
          conversionProb: 0.76,
          revenueImpact: 32000,
          nextAction: 'Email',
          status: 'high'
        },
        {
          id: 'LEAD_003',
          company: 'HealthTech Ltd',
          contact: 'Mike Davis',
          industry: 'Healthcare',
          conversionProb: 0.68,
          revenueImpact: 28000,
          nextAction: 'Call',
          status: 'medium'
        }
      ];

      const mockChartData = [
        { name: 'Jan', leads: 120, conversions: 28 },
        { name: 'Feb', leads: 150, conversions: 35 },
        { name: 'Mar', leads: 180, conversions: 42 },
        { name: 'Apr', leads: 200, conversions: 48 },
        { name: 'May', leads: 220, conversions: 52 },
        { name: 'Jun', leads: 250, conversions: 58 }
      ];

      setStats(mockStats);
      setTopLeads(mockTopLeads);
      setChartData(mockChartData);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const actionStats = [
    { name: 'Calls Needed', value: 23, icon: Phone, color: 'text-blue-600', bgColor: 'bg-blue-100' },
    { name: 'Emails to Send', value: 45, icon: Mail, color: 'text-green-600', bgColor: 'bg-green-100' },
    { name: 'Nurture Campaign', value: 67, icon: Target, color: 'text-yellow-600', bgColor: 'bg-yellow-100' }
  ];

  const pieData = [
    { name: 'High Priority', value: 89, color: '#ef4444' },
    { name: 'Medium Priority', value: 156, color: '#f59e0b' },
    { name: 'Low Priority', value: 1002, color: '#10b981' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome back! Here's what's happening with your leads.</p>
        </div>
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <span className="text-sm text-gray-600">AI Model Active</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Leads</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalLeads.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
              <p className="text-2xl font-bold text-gray-900">{(stats.conversionRate * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pipeline Value</p>
              <p className="text-2xl font-bold text-gray-900">${(stats.totalRevenue / 1000000).toFixed(1)}M</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Priority</p>
              <p className="text-2xl font-bold text-gray-900">{stats.highPriorityLeads}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads Trend Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Leads & Conversions Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="leads" stroke="#3b82f6" strokeWidth={2} />
              <Line type="monotone" dataKey="conversions" stroke="#10b981" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Priority Distribution */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Priority Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {pieData.map((item, index) => (
              <div key={index} className="flex items-center">
                <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: item.color }}></div>
                <span className="text-sm text-gray-600">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Actions Required</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {actionStats.map((stat, index) => (
            <div key={index} className="flex items-center p-4 border rounded-lg">
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Leads */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Top Performing Leads</h3>
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            View All Leads
          </button>
        </div>
        <div className="space-y-4">
          {topLeads.map((lead) => (
            <LeadCard key={lead.id} lead={lead} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
