import string

import attr
from authlib.oidc.core import UserInfo
from typing import Any, Dict, List, Optional, Tuple

from synapse.handlers.oidc import OidcMappingProvider, Token, UserAttributeDict
from synapse.handlers.sso import MappingException
from synapse.module_api import ModuleApi

mxid_localpart_allowed_characters = frozenset(
    "_-./=" + string.ascii_lowercase + string.digits
)


@attr.s(slots=True, frozen=True, auto_attribs=True)
class ProConnectMappingConfig:
    user_id_lookup_fallback_rules:Dict[str, str]= {}

class ProConnectMappingProvider(OidcMappingProvider[ProConnectMappingConfig]):
    def __init__(self, config: ProConnectMappingConfig, module_api: ModuleApi):
        self.module_api = module_api
        self._config=config

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> ProConnectMappingConfig:
        return ProConnectMappingConfig(**config)

    def get_remote_user_id(self, userinfo: UserInfo) -> str:
        return userinfo.sub

    async def map_user_attributes(
        self, userinfo: UserInfo, token: Token, failures: int
    ) -> UserAttributeDict:
        if not userinfo.email:
            raise MappingException("No email provided by Pro Connect")

        localpart = None
        mapped_user_id = await self.search_user_id_by_threepid(userinfo.email)
        if mapped_user_id:
            user_info = await self.module_api.get_userinfo_by_id(mapped_user_id)
            if user_info and not user_info.is_deactivated:
                localpart = user_info.user_id.localpart

        if not localpart:
            if not await self.module_api._password_auth_provider.is_3pid_allowed(
                "email", userinfo.email, True
            ):
                raise MappingException("Votre administration n'est pas encore présente sur Tchap, inscrivez-la sur https://tchap.beta.gouv.fr/")

            # filter out invalid characters
            filtered = filter(
                lambda c: c in mxid_localpart_allowed_characters,
                userinfo.email.replace("@", "-").lower(),
            )
            desired_localpart = "".join(filtered)

            deactivated = True
            while deactivated:
                localpart = desired_localpart + (str(failures) if failures else "")
                user_info = await self.module_api.get_userinfo_by_id(
                    f"@{localpart}:{self.module_api.server_name}"
                )
                if user_info and user_info.is_deactivated:
                    failures += 1
                else:
                    deactivated = False

        display_name = await self.module_api._password_auth_provider.get_displayname_for_registration(
            {"m.login.email.identity": {"address": userinfo.email}},
            {},
        )

        return UserAttributeDict(
            localpart=localpart,
            emails=[userinfo.email],
            confirm_localpart=False,
            display_name=display_name,
        )
    
    # Search user ID by its email, retrying with replacements if necessary.
    async def search_user_id_by_threepid(self, email: str):
        # Try to find the user ID using the provided email
        userId = await self.module_api._store.get_user_id_by_threepid("email", email)

        # If userId is not found, attempt replacements
        if not userId:
            # Iterate through all mappings
            for old_value, new_value in  self._config.user_id_lookup_fallback_rules.items():
                # Check if the key (old_value) exists within the email
                if old_value in email:
                    # Replace the old value with the new value
                    replaced_email = email.replace(old_value, new_value)

                    # Retry finding the userId with the replaced email
                    userId = await self.module_api._store.get_user_id_by_threepid("email", replaced_email)

                    # If userId is found, break the loop early
                    if userId:
                        break

        return userId