
# MkDocs based documentation for Github project pages

## Setup/Installation
    pip install mkdocs
    pip install mkdocs-bootswatch

## Project layout for the documentation markdowns

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The Bisque documentation homepage.
        ...       # Other markdown pages, images and other files.

## Commands (serve docs on http://127.0.0.1:8000 for testing locally)

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs help` - Print this help message.

## Deploy to a branch gh-deploy in the github repository
cd ~/git-repository-home
mkdocs gh-deploy

> For full MkDocs documentation visit [mkdocs.org](https://mkdocs.org).