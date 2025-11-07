module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    jest: true,
    node: true
  },
  extends: [
    'react-app',
    'react-app/jest',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: './tsconfig.json'
  },
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'jsx-a11y',
    'import'
  ],
  rules: {
    // TypeScript specific rules
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        ignoreRestSiblings: true
      }
    ],
    '@typescript-eslint/no-explicit-any': 'warn',

    // React specific rules
    'react/jsx-key': 'error',
    'react/no-array-index-key': 'warn',

    // Import organization rules (simplified)
    'import/order': [
      'warn',
      {
        'groups': [
          'builtin',
          'external',
          'internal',
          ['parent', 'sibling', 'index']
        ],
        'newlines-between': 'always',
        'alphabetize': {
          'order': 'asc',
          'caseInsensitive': true
        }
      }
    ],

    // General code quality rules
    'no-console': 'warn',
    'no-debugger': 'error',
    'no-var': 'error',
    'prefer-const': 'error'
  },
  overrides: [
    {
      // Test files can be more lenient
      files: [
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/__tests__/**/*.{ts,tsx}',
        'src/setupTests.ts'
      ],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        'no-console': 'off'
      }
    }
  ],
  settings: {
    react: {
      version: 'detect'
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json'
      }
    }
  },
  ignorePatterns: [
    'build/',
    'node_modules/',
    '*.config.js',
    'public/'
  ]
};