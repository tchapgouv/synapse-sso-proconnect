from unittest.mock import AsyncMock
import aiounittest
from synapse_sso_proconnect.proconnect_mapping import ProConnectMappingProvider


def create_module(config
) -> ProConnectMappingProvider:
    module_api = AsyncMock()
    # Adding _store to the module_api object
    module_api._store = AsyncMock()
    module_api._store.get_user_id_by_threepid.side_effect = lambda typ, email: (
        "test-beta" if email == "test@beta.fr" 
        else "test-exemple" if email == "test@example.com"
        else "test-numerique" if email == "test@numerique.fr"  
        else "test-old" if email == "test@old.fr"  
        else None
    )
    parsed_config = ProConnectMappingProvider.parse_config(config)
    return ProConnectMappingProvider(parsed_config, module_api)
    
    
class ProConnectMappingTest(aiounittest.AsyncTestCase):
    #def setUp(self) -> None:
    
    async def test_with_map_should_replace(self):
        self.module = create_module({"user_id_lookup_fallback_rules":
            [
                {"match":"very-new.fr", "search": "beta.fr"},
                { "match":"new.fr","search":"beta.fr"}
            ]}) 
        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@new.fr")   
        # Assertions
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@new.fr")
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@beta.fr")    
        self.assertEqual(user_id, "test-beta")  # Should match the replaced email
        

    async def test_replace_by_priority(self):        
        self.module = create_module({"user_id_lookup_fallback_rules":
            [{"match":"test@new.fr", "search": "test@old.fr"},
             { "match":"new.fr","search":"beta.fr"}
            ]}) 


        #replace by domain leads to a dead-end but it lower in the list
        
        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@new.fr")   
        # Assertions
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@new.fr")
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@old.fr")    
        self.assertEqual(user_id, "test-old")  # Should match the replaced email

    async def test_with_map_should_not_replace(self):
        self.module = create_module({"user_id_lookup_fallback_rules":
            [{ "match":"new.fr","search":"beta.fr"}]}) 
        
        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@numerique.fr")

        # Assertions
        self.assertEqual(user_id, "test-numerique")

    async def test_with_empty_map(self):

        self.module = create_module({"user_id_lookup_fallback_rules":[]})

        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@numerique.fr")

        # Assertions
        self.assertEqual(user_id, "test-numerique")