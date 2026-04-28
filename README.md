GBrain Technical Documentation
================================

A comprehensive technical reference for GBrain — the open-source personal knowledge brain for AI agents, built by Y Combinator CEO Garry Tan.

This book is automatically built and deployed to GitHub Pages via the ``docs.yml`` workflow.

Build Locally
-------------

::

    pip install sphinx myst-parser sphinxcontrib-mermaid sphinx-book-theme --break-system-packages
    sphinx-build -b html . _build/html

Then open ``_build/html/index.html``.

Repository
----------

* Source: https://github.com/pty819/gbrain-book
* GBrain: https://github.com/garrytan/gbrain
* Live Docs: https://pty819.github.io/gbrain-book/
