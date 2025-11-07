# DeskMate Frontend Development Guide

This document outlines the development infrastructure and tools set up for the DeskMate frontend.

## 🛠️ Development Infrastructure

### Code Quality Tools

#### ESLint Configuration
- **File**: `.eslintrc.js`
- **Features**:
  - React and TypeScript rules
  - Import organization and sorting
  - Accessibility checks (jsx-a11y)
  - Code quality enforcement
  - Prettier integration

#### Prettier Configuration
- **File**: `.prettierrc`
- **Features**:
  - Consistent code formatting
  - Single quotes, 2-space indentation
  - 100-character line width
  - Automatic formatting on save

#### TypeScript Configuration
- **File**: `tsconfig.json`
- **Enhanced Features**:
  - Path mapping for cleaner imports (`@/components/*`, `@/utils/*`, etc.)
  - Improved IDE support
  - Better module resolution
  - Gradual strict type checking adoption

### Development Scripts

```bash
# Code Quality
npm run lint              # Check for linting issues
npm run lint:fix           # Fix auto-fixable linting issues
npm run format            # Format all code with Prettier
npm run format:check      # Check if code is properly formatted
npm run typecheck         # TypeScript type checking

# Combined Workflows
npm run quality           # Run all quality checks (typecheck + lint + format:check)
npm run quality:fix       # Run all quality checks with auto-fixes

# Testing
npm run test              # Run tests in watch mode
npm run test:coverage     # Run tests with coverage report
npm run test:ci           # Run tests in CI mode (no watch, with coverage)

# Standard React Scripts
npm start                 # Development server
npm run build             # Production build
```

### VS Code Integration

#### Workspace Settings (`.vscode/settings.json`)
- Auto-format on save
- Auto-fix ESLint issues on save
- Organize imports automatically
- Optimized for TypeScript/React development

#### Recommended Extensions (`.vscode/extensions.json`)
- ESLint and Prettier
- TypeScript language support
- React development tools
- Path IntelliSense
- GitLens for enhanced Git integration

#### Debug Configuration (`.vscode/launch.json`)
- React app debugging
- Test debugging
- Chrome debugging setup

### Testing Infrastructure

#### Jest Configuration (`jest.config.js`)
- Enhanced module resolution with path mapping
- File mocking for assets and styles
- Coverage reporting with HTML output
- TypeScript support
- Watch plugins for better development experience

#### Coverage Thresholds
- **Current**: 50% (branches, functions, lines, statements)
- **Target**: Gradual improvement toward 80%

## 📁 Project Structure

```
src/
├── components/          # React components
├── hooks/              # Custom React hooks
├── stores/             # Zustand state management
├── services/           # API and service layer
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
├── contexts/           # React contexts
├── styles/             # CSS and styling
└── __mocks__/          # Jest mocks for testing
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm start
   ```

3. **Run quality checks**:
   ```bash
   npm run quality
   ```

4. **Auto-fix issues**:
   ```bash
   npm run quality:fix
   ```

## 📋 Development Workflow

### Daily Development
1. Pull latest changes: `git pull`
2. Install any new dependencies: `npm install`
3. Start development server: `npm start`
4. Make your changes
5. Run quality checks: `npm run quality:fix`
6. Commit and push changes

### Before Committing
Always run the complete quality check:
```bash
npm run quality:fix
```

This ensures:
- TypeScript compilation succeeds
- All ESLint rules are followed
- Code is properly formatted with Prettier

### VS Code Setup

1. Install recommended extensions when prompted
2. Restart VS Code to activate settings
3. Enjoy automatic formatting and linting on save!

## 🎯 Benefits Achieved

### Developer Experience
- **Consistent Code Style**: Automatic formatting eliminates style discussions
- **Early Error Detection**: TypeScript and ESLint catch issues before runtime
- **Better IDE Support**: Enhanced IntelliSense and debugging
- **Reduced Manual Work**: Auto-fix and format-on-save features

### Code Quality
- **Maintainable Code**: Consistent patterns and structure
- **Fewer Bugs**: Type checking and linting catch common mistakes
- **Easier Onboarding**: Clear standards and automated tools
- **Better Collaboration**: Consistent code style across team members

### Future Benefits
- **Easier Refactoring**: Better tooling support for large changes
- **Improved Testing**: Foundation for comprehensive test coverage
- **Scalability**: Solid foundation for growing the codebase
- **Documentation**: Self-documenting code with TypeScript interfaces

## 🔧 Troubleshooting

### Common Issues

#### ESLint/TypeScript Conflicts
If you see conflicting rules, check:
1. `.eslintrc.js` extends include `'prettier'` at the end
2. VS Code is using the workspace TypeScript version

#### Import Path Issues
- Use the configured path mappings (e.g., `@/components/Button` instead of `../../components/Button`)
- Ensure `tsconfig.json` path mapping is correct

#### Prettier Not Working
1. Install the Prettier VS Code extension
2. Set Prettier as the default formatter in VS Code settings
3. Enable format on save

### Getting Help

1. Check this documentation
2. Review the ESLint/Prettier/TypeScript documentation
3. Check VS Code extension documentation
4. Ask team members for guidance

---

This infrastructure provides a solid foundation for scalable, maintainable frontend development! 🎉