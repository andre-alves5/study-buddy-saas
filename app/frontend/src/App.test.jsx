import { render, screen } from '@testing-library/react';
import App from './src/App';

jest.mock('@aws-amplify/ui-react', () => ({
  Authenticator: ({ children }) => children({ signOut: jest.fn(), user: { username: 'test-user' } }),
}));

test('renders the App component', () => {
  render(<App />);

  expect(screen.getByText('📚 AWS Study Buddy')).toBeInTheDocument();
  expect(screen.getByText('Welcome, test-user')).toBeInTheDocument();
  expect(screen.getByText('1. Upload Document')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Process PDF' })).toBeInTheDocument();
});
