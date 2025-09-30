import LoginPage from '../pages/operations/LoginPage';

export default {
  title: 'Pages/LoginPage',
  component: LoginPage,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

// Default login page
export const Default = {
  args: {},
};

// With error state
export const WithError = {
  args: {},
  decorators: [
    (Story) => {
      // Mock localStorage for this story
      const originalLocalStorage = window.localStorage;
      window.localStorage = {
        ...originalLocalStorage,
        getItem: (key) => {
          if (key === 'login_error') return 'Invalid credentials. Please try again.';
          return originalLocalStorage.getItem(key);
        },
      };
      
      const result = Story();
      
      // Restore localStorage
      window.localStorage = originalLocalStorage;
      
      return result;
    },
  ],
};

// Loading state
export const Loading = {
  args: {},
  decorators: [
    (Story) => {
      // This would require modifying the component to accept a loading prop
      // For now, this demonstrates the structure
      return Story();
    },
  ],
};