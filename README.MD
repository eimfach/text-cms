# Text-CMS

A custom text format to html compiler serving as a blog tool to create content. Embedded in my Website. Test Driven developed. Needs more work to run standalone.

Uses: 
- Python, Pydantic for Parsing and Tokenizing.
- nltk for seo analysing the the tokenized content (json)
- yattag for generating html with Python

Usage:

```bash
pip install pipenv
pipenv install

# run tests:
pipenv run python -m pytest -vv

# compile:
pipenv run python compile.py
```