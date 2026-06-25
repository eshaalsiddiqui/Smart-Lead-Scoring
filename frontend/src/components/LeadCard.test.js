import React from 'react';
import { render, screen } from '@testing-library/react';
import LeadCard from './LeadCard';

// Regression test: LeadCard used to read camelCase props (company, conversionProb,
// revenueImpact, nextAction) while the API returns snake_case fields, so real data
// rendered as blank/undefined. Assert it reads the API's actual field names.
test('renders a lead using the snake_case fields returned by the API', () => {
  const lead = {
    company_name: 'Acme Corp',
    contact_name: 'Jane Doe',
    industry: 'Technology',
    conversion_probability: 0.755,
    revenue_impact: 19416.45,
    next_best_action: 'Call',
    status: 'high',
  };

  render(<LeadCard lead={lead} />);

  expect(screen.getByText('Acme Corp')).toBeInTheDocument();
  expect(screen.getByText('Jane Doe')).toBeInTheDocument();
  expect(screen.getByText('75.5%')).toBeInTheDocument();
  expect(screen.getByText('$19,416')).toBeInTheDocument();
  expect(screen.getByText('HIGH')).toBeInTheDocument();
  expect(screen.getByText('Call')).toBeInTheDocument();
});
