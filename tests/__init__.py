from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock

import attr
from synapse.module_api import ModuleApi, UserID

from synapse_sso_proconnect.proconnect_mapping import ProConnectMappingProvider

class MockHomeserver:
    def get_datastores(self):
        return Mock(spec=["main"])

    def get_task_scheduler(self):
        return Mock(spec=["register_action"])

def create_module(
    config_override: Optional[Dict[str, Any]] = None, server_name: str = "example.com"
) -> ProConnectMappingProvider:
    # Create a mock based on the ModuleApi spec, but override some mocked functions
    # because some capabilities are needed for running the tests.
    module_api = Mock(spec=ModuleApi)

    if config_override is None:
        config_override = {}
    config_override["id_server"] = "example.com"

    config = ProConnectMappingProvider.parse_config(config_override)

    return ProConnectMappingProvider(config, module_api)