import baseConfig from '../../eslint.config.mjs';

export default [
  ...baseConfig,
  { ignores: ['**/.venv/**'] },
  {
    files: ['tests/*.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
];
