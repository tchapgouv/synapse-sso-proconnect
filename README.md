# Synapse SSO Pro Connect

## Installation

```
pip install synapse-sso-proconnect
```

## Config

Add the following to your Synapse config:

```yaml
modules:
  - module: 
    config:
```

## Development and Testing

This repository uses `tox` to run tests.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.
