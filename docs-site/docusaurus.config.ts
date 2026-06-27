import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

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
    colorMode: {
      respectPrefersColorScheme: true,
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
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'yaml', 'python', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
