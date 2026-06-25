// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom doesn't implement ResizeObserver, which recharts' ResponsiveContainer
// needs to measure its container. Stub it so chart-bearing pages don't crash
// when rendered in tests.
global.ResizeObserver = global.ResizeObserver || class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
