import type { Monaco } from '@monaco-editor/react';

export function setupModelScriptLanguage(monaco: Monaco) {
  // Check if language already registered
  if (monaco.languages.getLanguages().some((l: any) => l.id === 'modelscript')) {
    return;
  }

  monaco.languages.register({ id: 'modelscript' });

  // Monarch Token Provider
  monaco.languages.setMonarchTokensProvider('modelscript', {
    keywords: [
      'model', 'scenario', 'for', 'in', 'to', 'if', 'else', 'output', 'and', 'or', 'not'
    ],
    builtins: [
      'PMT', 'FV', 'NPV', 'GROWTH', 'COMPOUND', 'ROUND', 'MIN', 'MAX', 'ABS',
      'pmt', 'fv', 'npv', 'growth', 'compound', 'round', 'min', 'max', 'abs'
    ],
    operators: [
      '=', '+', '-', '*', '/', '%', '^', '==', '!=', '<', '<=', '>', '>='
    ],
    symbols: /[=><!~?:&|+\-*\/\^%]+/,

    tokenizer: {
      root: [
        // Identifiers and keywords
        [/[a-zA-Z_]\w*/, {
          cases: {
            '@keywords': 'keyword',
            '@builtins': 'predefined',
            '@default': 'identifier'
          }
        }],

        // Whitespace
        { include: '@whitespace' },

        // Delimiters and operators
        [/[{}()\[\]]/, '@brackets'],
        [/@symbols/, {
          cases: {
            '@operators': 'operator',
            '@default': ''
          }
        }],

        // Numbers
        [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
        [/\d+([eE][\-+]?\d+)?/, 'number'],

        // Strings
        [/"([^"\\]|\\.)*$/, 'string.invalid'],  // non-teminated string
        [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],
      ],

      string: [
        [/[^\\"]+/, 'string'],
        [/\\./, 'string.escape'],
        [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
      ],

      whitespace: [
        [/[ \t\r\n]+/, 'white'],
        [/\/\*/, 'comment', '@comment'],
        [/\/\/.*$/, 'comment'],
        [/#.*$/, 'comment'],
      ],

      comment: [
        [/[^\/*]+/, 'comment'],
        [/\*\//, 'comment', '@pop'],
        [/[\/*]/, 'comment']
      ],
    }
  });

  // Autocomplete suggestions
  monaco.languages.registerCompletionItemProvider('modelscript', {
    provideCompletionItems: (model: any, position: any) => {
      const suggestions = [
        // Keywords
        {
          label: 'model',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'model "${1:Model Name}" {\n\t$0\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Declare a top-level financial model'
        },
        {
          label: 'scenario',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'scenario "${1:Scenario Name}" {\n\t$0\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Declare a scenario with parameter overrides'
        },
        {
          label: 'for',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'for ${1:month} in 1 to ${2:24} {\n\t$0\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Time-series projection loop'
        },
        {
          label: 'output',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'output ${1:month}, ${2:revenue}, ${3:profit}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Record periodic row values to output dataset'
        },
        {
          label: 'if',
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: 'if (${1:condition}) {\n\t$2\n} else {\n\t$3\n}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Conditional financial branch'
        },
        // Builtin Financial Functions
        {
          label: 'PMT',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'PMT(${1:rate}, ${2:nper}, ${3:pv})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'PMT(rate, nper, pv) - Computes loan periodic payment'
        },
        {
          label: 'FV',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'FV(${1:rate}, ${2:nper}, ${3:pmt}, ${4:pv})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'FV(rate, nper, pmt, [pv]) - Future value of cashflows'
        },
        {
          label: 'GROWTH',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'GROWTH(${1:base}, ${2:rate}, ${3:period})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'GROWTH(base, rate, period) = base * (1 + rate)^period'
        },
        {
          label: 'COMPOUND',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'COMPOUND(${1:principal}, ${2:rate}, ${3:periods})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'COMPOUND(principal, rate, periods) = principal * (1 + rate)^periods'
        },
        {
          label: 'NPV',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'NPV(${1:discount_rate}, ${2:cf1}, ${3:cf2})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'NPV(rate, cf1, cf2, ...) - Net Present Value of series'
        },
        {
          label: 'ROUND',
          kind: monaco.languages.CompletionItemKind.Function,
          insertText: 'ROUND(${1:value}, ${2:2})',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'ROUND(value, decimals)'
        }
      ];
      return { suggestions };
    }
  });

  // Custom Dark Theme for ModelScript
  monaco.editor.defineTheme('finrule-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '10b981', fontStyle: 'bold' },
      { token: 'predefined', foreground: '06b6d4', fontStyle: 'bold' },
      { token: 'identifier', foreground: 'e2e8f0' },
      { token: 'number', foreground: 'f59e0b' },
      { token: 'number.float', foreground: 'f59e0b' },
      { token: 'string', foreground: 'a78bfa' },
      { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
      { token: 'operator', foreground: '38bdf8' }
    ],
    colors: {
      'editor.background': '#0b111c',
      'editor.foreground': '#f8fafc',
      'editor.lineHighlightBackground': '#121a2d',
      'editorCursor.foreground': '#10b981',
      'editorLineNumber.foreground': '#475569',
      'editorLineNumber.activeForeground': '#10b981',
      'editor.selectionBackground': '#10b98133',
    }
  });

  // Custom Light Theme for ModelScript
  monaco.editor.defineTheme('finrule-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '059669', fontStyle: 'bold' },
      { token: 'predefined', foreground: '0891b2', fontStyle: 'bold' },
      { token: 'identifier', foreground: '0f172a' },
      { token: 'number', foreground: 'd97706' },
      { token: 'number.float', foreground: 'd97706' },
      { token: 'string', foreground: '7c3aed' },
      { token: 'comment', foreground: '94a3b8', fontStyle: 'italic' },
      { token: 'operator', foreground: '0284c7' }
    ],
    colors: {
      'editor.background': '#ffffff',
      'editor.foreground': '#0f172a',
      'editor.lineHighlightBackground': '#f1f5f9',
      'editorCursor.foreground': '#059669',
      'editorLineNumber.foreground': '#94a3b8',
      'editorLineNumber.activeForeground': '#059669',
      'editor.selectionBackground': '#05966933',
    }
  });
}
