# Optional CI: build both PDFs on every push

`build.yml` is the GitHub Actions workflow that compiles `en/main.pdf` and
`zh/main-zh.pdf` with XeLaTeX and uploads them as artifacts.

It is **not** active in this repository, for one boring reason: the `gh` token
used to create the repo has the `repo`, `read:org` and `gist` scopes but **not**
`workflow`, and GitHub refuses to let an OAuth App create or update files under
`.github/workflows/` without it.

## Enable it

Either grant the scope and let the file move itself:

```bash
gh auth refresh -s workflow
git mv pipeline/ci/build.yml .github/workflows/build.yml
git commit -m "ci: build both editions on every push"
git push
```

Or do it entirely in the browser: on GitHub, open **Add file → Create new file**,
name it `.github/workflows/build.yml`, paste the contents of `build.yml`, commit.
The web UI is not subject to the token scope restriction.

## What it runs

```yaml
xu-cheng/latex-action@v3   with  latexmk_use_xelatex: true
```

Two independent jobs — one per edition — each uploading the finished PDF as a
build artifact. TeX Live in that image is a full scheme, so `ctex`, `fontspec`,
`tcolorbox`, `longtable` and the Fandol CJK fonts are all present.
