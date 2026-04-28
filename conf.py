# GBrain Sphinx Book Configuration

project = 'GBrain'
copyright = '2026, GBrain Contributors'
author = 'GBrain Team'
release = 'v0.22'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    'myst_parser',
    'sphinxcontrib.mermaid',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']

html_theme_options = {
    'repository_url': 'https://github.com/garrytan/gbrain',
    'repository_branch': 'main',
    'use_repository_button': True,
    'use_issues_button': True,
    'home_page_in_toc': True,
    'show_navbar_depth': 2,
    'show_toc_level': 2,
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'typescript': ('https://www.typescriptlang.org/docs/', None),
}

myst_enable_extensions = ['colon_fence', 'dollarmath', 'tasklist']

todo_include_todos = True