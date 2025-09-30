// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
// The `eslint-plugin-react-refresh` is likely not needed for a Vite project.
// The `@vitejs/plugin-react` should handle Fast Refresh setup, including linting.
// import reactRefresh from 'eslint-plugin-react-refresh'

// The new ESLint flat config format is an array of config objects.
export default [
  {
    // `ignores` is the standard way to ignore files/directories in flat config.
    ignores: ['dist/'],
  },
  // Apply recommended ESLint rules.
  js.configs.recommended,
  {
    // Custom configuration for your project files.
    files: ['src/**/*.{js,jsx,mjs,ts,tsx}'],
    plugins: {
      react,
      'react-hooks': reactHooks,
    },
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
      },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,
      // The `react-refresh/only-export-components` rule is handled by `@vitejs/plugin-react`.
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      'react/prop-types': 'off',
    },
  },
  // Storybook configuration
  ...storybook.configs['flat/recommended'],
]
