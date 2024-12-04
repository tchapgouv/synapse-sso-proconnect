from unittest.mock import AsyncMock
import aiounittest
from tests import  create_module
from synapse_sso_proconnect.proconnect_mapping import ProConnectMappingProvider


def create_module(
) -> ProConnectMappingProvider:
    module_api = AsyncMock()
    # Adding _store to the module_api object
    module_api._store = AsyncMock()
    module_api.getReplaceMapping = AsyncMock(
        return_value={"numerique.gouv.fr": "beta.gouv.fr"}
    )
    module_api._store.get_user_id_by_threepid.side_effect = lambda typ, email: (
        "test-beta" if email == "test@beta.gouv.fr" 
        else "test-exemple" if email == "test@example.com" 
        else None
    )
    config= {}
    return ProConnectMappingProvider(config, module_api)
    
    
class ProConnectMappingTest(aiounittest.AsyncTestCase):
    def setUp(self) -> None:
        self.module = create_module()
    

    async def test_with_email_replacement(self):

        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@numerique.gouv.fr")

        # Assertions
        self.assertEqual(user_id, "test-beta")  # Should match the replaced email
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@numerique.gouv.fr")
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@beta.gouv.fr")