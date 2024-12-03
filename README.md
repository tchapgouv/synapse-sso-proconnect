# Pro Connect

## Installation

```
pip install synapse-room-access-rules
```

## Config

Add the following to your Synapse config:

```yaml
modules:
  - module: room_access_rules.RoomAccessRules
    config:
        # List of domains (server names) that can't be invited to rooms if the
        # "restricted" rule is set. Defaults to an empty list.
        domains_forbidden_when_restricted: []
    
        # Identity server to use when checking the homeserver an email address belongs to
        # using the /info endpoint. Required.
        id_server: "vector.im"
        # Disable access rules for this list of users
        bypass_for_users: []
```

## Development and Testing

This repository uses `tox` to run tests.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.

### Making a release

```
git tag -s vX.Y
python3 setup.py sdist
twine upload dist/synapse-room-access-rules-X.Y.tar.gz
git push origin vX.Y
```