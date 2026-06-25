import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { apiService } from './services/api';

// Mock the API layer so this stays a pure component smoke test - it
// shouldn't depend on a running backend or on axios's real module graph.
jest.mock('./services/api', () => ({
  apiService: {
    getHealth: jest.fn(),
    getAnalytics: jest.fn(),
    getTopLeads: jest.fn(),
    getLeads: jest.fn(),
  },
}));

// CRA's Jest config sets resetMocks: true, which clears any mockResolvedValue
// set inside the jest.mock() factory before each test runs - so the resolved
// values have to be (re)applied here instead.
beforeEach(() => {
  apiService.getHealth.mockResolvedValue({ data: {} });
  apiService.getAnalytics.mockResolvedValue({
    data: {
      totalLeads: 1000,
      conversionRate: 0.5,
      totalRevenue: 1200000,
      highPriorityLeads: 126,
      monthlyTrend: [],
      actionStats: { callsNeeded: 0, emailsNeeded: 0, nurtureNeeded: 0 },
      priorityDistribution: { high: 0, medium: 0, low: 0 },
    },
  });
  apiService.getTopLeads.mockResolvedValue({ data: { leads: [] } });
  apiService.getLeads.mockResolvedValue({ data: { leads: [] } });
});

test('renders the app shell with sidebar branding and nav links', async () => {
  render(<App />);

  expect(await screen.findByText('Smart CRM')).toBeInTheDocument();
  expect(screen.getByText('Lead Scoring Platform')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Leads' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'AI Assistant' })).toBeInTheDocument();

  // wait for Dashboard's async fetch to resolve so the update is flushed
  // inside act() instead of warning after the test completes
  expect(await screen.findByText('Total Leads')).toBeInTheDocument();
});
