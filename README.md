# Synapse SSO Pro Connect

## Installation

```
pip install synapse-sso-proconnect
```

## Config

Add the following to your oidc config:

```yaml
oidc_providers:
  - idp_id
    ...
    user_mapping_provider:
      module: synapse_sso_proconnect.proconnect_mapping.ProConnectMappingProvider
      config:
        user_id_lookup_fallback_rules: 
          - match : new_domain.fr
            search : old_domain.fr
          - match : user@another_domain.fr
            search : user@an_old_domain.fr



```

## Development and Testing

This repository uses `tox` to run tests.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.
