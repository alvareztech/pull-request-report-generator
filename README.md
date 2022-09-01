# Pull Request report generator

A python script to generate PDF (and HTML) Pull Request reports.

The report includes:

- Approvers for each PR with the approval date
- Modified files
- Merged time
- Commit hash
- Direct links to Github commits, users, and pull requests

<!-- [This is a sample of the output](/samples/a.pdf) with the current script. -->

## Dependencies

[wkhtmltopdf](https://wkhtmltopdf.org) needs to be installed on the machine prior to running this script.

### Install wkhtmltopdf:

macOS:

```
brew install homebrew/cask/wkhtmltopdf
```

Debian/Ubuntu:

```shell
sudo apt-get install wkhtmltopdf
```

## Running

It is possible to generate one or more repository reports with a command line with the following parameters:

```script
python3 main.py --since v2.0 --until v2.8 --repos repo1,repo2
```

- `since`: Tag name of the penultimate version from which the report will be generated.
- `until`: Tag name of the latest version or the one from which the report is to be generated.
- `repos`: List of repositories (slug only) separated by a single comma (no spaces)
- `token`: Token or PAT (Personal Access Token) from Github. This parameter is optional if the `config.py` file is used.

The `repos` parameter can be set the following values to automatically generate reports from all repos in `util.py`.

__`REPOS`__

```
python3 main.py --since v2.0 --until v2.8 --repos REPOS
```

> Another list of repositories can be defined in file `util.py`

The files or reports generated are located in the **dist/** folder.

Additionally, reports are also generated in HTML that are used to generate the report in PDF.

## Troubleshooting

To run the script locally, a PAT (Personal Access Token) must be generated at [github.com/settings/tokens](https://github.com/settings/tokens) and must be authorized for your organization.

<!-- ![Screenshot](/screenshots/github-dev-settings.png) -->

Authorization may be required every 24 hours depending on organization policy.

> For an automated CI/CD environment you should have a variable like `secrets.GITHUB_TOKEN`