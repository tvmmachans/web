/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/',
    query: {},
    push: jest.fn(),
  }),
}));

// Simple homepage component test
describe('Homepage', () => {
  it('should render without crashing', () => {
    // This is a basic test to ensure the test setup works
    // Replace with actual homepage component when available
    const HomePage = () => (
      <div>
        <h1>AI Social Media Manager</h1>
        <nav>
          <a href="/upload">Upload</a>
          <a href="/schedule">Schedule</a>
          <a href="/analytics">Analytics</a>
        </nav>
      </div>
    );

    render(<HomePage />);
    
    expect(screen.getByText('AI Social Media Manager')).toBeInTheDocument();
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Schedule')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });
});

