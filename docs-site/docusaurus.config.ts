import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import type {PrismTheme} from 'prism-react-renderer';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

// Gruvbox dark (hard contrast) Prism theme — mirrors tokens/colors.css
// (--code-* syntax tokens). prism-react-renderer applies inline styles, so the
// syntax palette must live here rather than in custom.css.
const gruvboxDark: PrismTheme = {
  plain: {color: '#ebdbb2', backgroundColor: '#282828'},
  styles: [
    {types: ['comment', 'prolog', 'cdata'], style: {color: '#928374', fontStyle: 'italic'}},
    {types: ['punctuation'], style: {color: '#bdae93'}},
    {types: ['keyword', 'atrule', 'selector', 'important'], style: {color: '#fb4934'}},
    {types: ['string', 'char', 'attr-value', 'inserted'], style: {color: '#b8bb26'}},
    {types: ['function', 'function-name'], style: {color: '#b8bb26'}},
    {types: ['number', 'boolean', 'constant', 'symbol'], style: {color: '#d3869b'}},
    {types: ['operator', 'entity', 'url', 'variable'], style: {color: '#fe8019'}},
    {types: ['class-name', 'tag', 'property'], style: {color: '#fabd2f'}},
    {types: ['builtin', 'namespace', 'attr-name'], style: {color: '#8ec07c'}},
    {types: ['deleted'], style: {color: '#fb4934'}},
  ],
};

const config: Config = {
  title: 'SCM CLI',
  tagline:
    'Command-line interface for managing Palo Alto Networks Strata Cloud Manager configurations',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Production url of the site (GitHub Pages).
  url: 'https://cdot65.github.io',
  // Served under /<projectName>/ on GitHub Pages.
  baseUrl: '/pan-scm-cli/',

  // GitHub pages deployment config.
  organizationName: 'cdot65',
  projectName: 'pan-scm-cli',

  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang.
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    // Parse .md as CommonMark and .mdx as MDX. Keeps CLI placeholder syntax
    // (<value>, {json}) from breaking the build in the ported reference pages.
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Serve docs at the site root to mirror the previous mkdocs layout.
          routeBasePath: '/',
          editUrl: 'https://github.com/cdot65/pan-scm-cli/tree/main/docs-site/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/logo.png',
    // The Gruvbox design system is dark, hard-contrast only.
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'SCM CLI',
      logo: {
        alt: 'SCM CLI Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/cdot65/pan-scm-cli',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://pypi.org/project/pan-scm-cli/',
          label: 'PyPI',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Introduction', to: '/about/introduction'},
            {label: 'Installation', to: '/about/installation'},
            {label: 'CLI Reference', to: '/cli/'},
          ],
        },
        {
          title: 'Project',
          items: [
            {label: 'GitHub', href: 'https://github.com/cdot65/pan-scm-cli'},
            {label: 'PyPI', href: 'https://pypi.org/project/pan-scm-cli/'},
            {
              label: 'Issues',
              href: 'https://github.com/cdot65/pan-scm-cli/issues',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} cdot65. Built with Docusaurus.`,
    },
    prism: {
      theme: gruvboxDark,
      darkTheme: gruvboxDark,
      additionalLanguages: ['bash', 'json', 'yaml', 'python', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
