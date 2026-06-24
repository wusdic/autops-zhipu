import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import prettier from 'eslint-config-prettier'

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  // 先应用 Vue 推荐规则
  ...pluginVue.configs['flat/recommended'],
  // 关键：用 vue-eslint-parser 作为外层 parser，tseslint.parser 作为内层 script parser
  {
    files: ['*.vue', '**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
      },
    },
  },
  prettier,
  {
    rules: {
      'vue/multi-word-component-names': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      // TS 中 no-undef 由 tseslint 处理，js 的 no-undef 对 browser 全局变量会误报
      'no-undef': 'off',
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', '*.d.ts', 'src/auto-imports.d.ts', 'src/components.d.ts'],
  },
)
