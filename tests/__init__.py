from unittest.mock import AsyncMock
from synapse_sso_proconnect.proconnect_mapping import ProConnectMappingProvider
from synapse.types import  UserID, UserInfo




def create_module(config
) -> ProConnectMappingProvider:
    module_api = AsyncMock()
    # Adding _store to the module_api object
    module_api._store = AsyncMock()
    module_api._store.get_user_id_by_threepid.side_effect = lambda typ, email: (
        "@test:beta" if email == "test@beta.fr" 
        else "@test:exemple" if email == "test@example.com"
        else "@test:numerique" if email == "test@numerique.fr"  
        else "@test:old" if email == "test@old.fr"  
        else None
    )
    module_api.get_userinfo_by_id.side_effect = lambda mapped_user_id: (
        UserInfo(
                user_id=UserID.from_string(mapped_user_id),
                is_admin=False,
                is_guest=False,
                consent_server_notice_sent=None,
                consent_ts=None,
                consent_version=None,
                appservice_id=None,
                creation_ts=0,
                user_type=None,
                is_deactivated=False,
                locked=False,
                is_shadow_banned=False,
                approved=True,
                suspended=False,
            )
    )

    parsed_config = ProConnectMappingProvider.parse_config(config)
    return ProConnectMappingProvider(parsed_config, module_api)
    
    