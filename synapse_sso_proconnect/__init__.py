
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
            old_email = extra_attributes.get('old_email', None)
            new_email = extra_attributes.get('new_email', None)
            if(old_email and new_email):
                #make the remplacement
                logger.info("User is connected via %s with a new email:%s, the old one:%s will be substituted", auth_provider_id, new_email,old_email)
