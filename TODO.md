# Versioning notes

`<phase>_v<major>.<minor>.<bugfix>`

phase
    Can be `alpha` `beta` or blank (which means production).
major
    Customer-facing API version.  Any breaking API changes will bump up this
    version.
minor
    Internal changes version.  Changes at this level do not break
    customer-facing API.  Use for refactoring, optimizations.
bugfix
    Bugfix versioning.


# Demo Requirements

## web

1. `alpha_v1` Prepare Flask API

    - With API key authentication
    - Channel to core services

1. `alpha_v1` Microsoft Azure Functions setup
1. `alpha_v1` Domain name setup

## database

- `alpha_v1` email address
- `alpha_v1` API key
- `alpha_v1` API call counter
- `alpha_v1` payment status

## core

- DONE `alpha_v1` DataFrame postprocessing

    - DONE one transaction reference, multiple lines. i.e. one transaction,
      multiple prices matched

- `alpha_v1.1` Pipeline architecture

    - raw ledger
    - dataframe
    - dataframe postprocessing
    - JSON output

[modeline]: # vim:tw=80 colorcolumn=80
