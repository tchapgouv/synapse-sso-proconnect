
import logging
from typing import Any, Dict, List, Union

from synapse.module_api import ModuleApi


logger = logging.getLogger(__name__)

class LoginCallback(object):
    """
    Implementation of a Login Callback
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

        # only process login from oidc-proconnect
        if auth_provider_id != "oidc-proconnect":
            return

        # Extra attributes are set by the mapper : ./proconnect_mapping.py
        # This mapper is only invoked when the oidc user is not mapped to a MxId
        # After the first login the oidc user unique field (sub) is mapped to a MxId
        # Thus the 3PID substitution happens only at the first login of the oidc user

        # Check if extra attributes were attached to user_id 
        sso_extra_attributes = self.module_api._auth_handler._extra_attributes.get(user_id, None)
        logger.info("extra attributes found for user %s : %s",user_id, sso_extra_attributes  or "None")

        if not sso_extra_attributes:
            return

        extra_attributes = sso_extra_attributes.extra_attributes
        oidc_email = extra_attributes.get('oidc_email', None)
        current_threepid_email = extra_attributes.get('current_threepid_email', None)
        if(current_threepid_email and oidc_email and current_threepid_email != oidc_email):
            # make the substitution
            await self.substitute_threepid(user_id, current_threepid_email, oidc_email)

    async def substitute_threepid(self,user_id, current_threepid_email, new_threepid_email) -> None:
        """
            Delete current threepid email and add a new threepid in synapse and sydent
        """
        logger.info("Substitute %s 3PID with a new email:%s, the old one:%s", user_id, new_threepid_email,current_threepid_email)
        try:
            await self.module_api._auth_handler.delete_local_threepid(user_id,'email', current_threepid_email)
            current_time = self.module_api._clock.time_msec()
            await self.module_api._auth_handler.add_threepid(user_id, 'email', new_threepid_email, current_time)
        except Exception as e:
            # If there was an error when substituting the 3PID
            logger.exception(
                "Failed to substitute %s 3PID with a new email:%s, the old one:%s:%s", user_id, new_threepid_email, current_threepid_email, e)
