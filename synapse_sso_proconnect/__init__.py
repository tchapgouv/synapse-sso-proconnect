
import logging
from typing import Any, Dict, List, Union

from synapse.module_api import ModuleApi


logger = logging.getLogger(__name__)

class LoginListener(object):
    """Implementation of the 
    """

    def __init__(
            self,
            config: Any,
            api: ModuleApi,
        ):

        self.config = config
        self.module_api = api

        self.module_api.register_account_validity_callbacks(
            on_user_login=self.on_user_login,
        )

    async def on_user_login(
            self, 
            user_id: str, 
            auth_provider_type: str, 
            auth_provider_id: str
    ) -> None:
        logger.info("onLogin callback %s, %s, %s", user_id, auth_provider_type, auth_provider_id)

        extra_attributes = self.module_api._auth_handler._extra_attributes.get(user_id)
        logger.info("extra attributes found for user %s : %s",user_id, extra_attributes or "nothing")

        if auth_provider_id == "proconnect" and extra_attributes:
            #check if extra attributes were attached to user_id 
            extra_attributes = self.module_api._auth_handler._extra_attributes[user_id]
            oidc_email = extra_attributes.get('oidc_email', None)
            known_email = extra_attributes.get('known_email', None)
            if(known_email and oidc_email and known_email != oidc_email):
                #make the remplacement
                self.substitute_known_email(user_id, known_email, oidc_email)

    async def substitute_known_email(self,user_id, known_email, new_email) -> None:
        logger.info("Substitute %s 3PID with a new email:%s, the old one:%s", user_id, new_email,known_email)
        try:
            await self.module_api._auth_handler.delete_local_threepid(user_id,'email', known_email)
            await self.module_api._auth_handler.add_threepid(user_id, 'email', new_email)
        except Exception as e:
            # If there was an error when substituting the 3PID
            logger.exception(
                "Failed to substitute %s 3PID with a new email:%s, the old one:%s:%s", user_id, new_email,known_email,e)
