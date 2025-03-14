<h1 align="center">mkdocs-ipynb</h1>

Lighweight MkDocs plugin for loading Jupyter notebooks.

Interoperates with all other MkDocs features: admonitions, reference links, etc.

## Installation

```bash
pip install mkdocs_ipynb
```

Requires MkDocs 1.6.1+

## Usage

In `mkdocs.yml`:
```yml
...

plugins:
    - ipynb

nav:
    - some_notebook.ipynb
```

Under-the-hood it will be converted into markdown and then passed to MkDocs.

## Other similar libaries

- [`mkdocs-jupyter`](https://github.com/danielfrg/mkdocs-jupyter) converts Jupyter notebooks directly into HTML using `nbconvert`. It doesn't support admonitions, reference links (e.g. to [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings) references), etc.
- [`mknotebooks`](https://github.com/greenape/mknotebooks) also uses `nbconvert`. It has since fallen out of date with modern MkDocs.

Due to these limitations I wrote my own tiny plugin.

## Further work?

Jupyter cells can output many kinds of MIME types (`text/plain`, `image/png`, ...). It's fairly trivial to add support for them; right now we support just `text/plain` and `image/png` because those are my use-cases. Happy to take PRs extending this if you have use-cases for others.

This plugin doesn't use `nbconvert`, mainly because that in turn depends on many other libraries, and I object to that kind of dependency sprawl.
