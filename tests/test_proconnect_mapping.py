import aiounittest
from tests import create_module

from authlib.oidc.core import UserInfo  # type: ignore


class ProConnectMappingTest(aiounittest.AsyncTestCase):
    #def setUp(self) -> None:
    
    async def test_module(self):
        self.module = create_module({"user_id_lookup_fallback_rules":
            [
                {"match":"@very-new.fr", "search": "@beta.fr"},
                { "match":"@new.fr","search":"@beta.fr"}
            ]}) 
        # Call the tested function with an email that requires replacement
        # user_id = await self.module.search_user_id_by_threepid("test@new.fr")   
        user_info = await self.module.map_user_attributes(
            userinfo=UserInfo(email="test@new.fr"), token="", failures=0)

        # Assertions
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@new.fr")
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@beta.fr")    
        self.assertEqual(user_info['localpart'], 'test')  # Should match the replaced email


    async def test_search_user_id_with_map_should_replace(self):
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
        self.assertEqual(user_id, "@test:beta")  # Should match the replaced email
        

    async def test_search_user_id_replace_by_priority(self):        
        self.module = create_module({"user_id_lookup_fallback_rules":
            [{"match":"test@new.fr", "search": "test@old.fr"},
             { "match":"new.fr","search":"beta.fr"}
            ]}) #replace by domain leads to a dead-end but it lower in the list
        
        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@new.fr")   
        # Assertions
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@new.fr")
        self.module.module_api._store.get_user_id_by_threepid.assert_any_call("email", "test@old.fr")    
        self.assertEqual(user_id, "@test:old")  # Should match the replaced email

    async def test_search_user_id_with_empty_map(self):

        self.module = create_module({"user_id_lookup_fallback_rules":[]})

        # Call the tested function with an email that requires replacement
        user_id = await self.module.search_user_id_by_threepid("test@numerique.fr")

        # Assertions
        self.assertEqual(user_id, "@test:numerique")