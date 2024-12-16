import string

import attr
from authlib.oidc.core import UserInfo  # type: ignore
from typing import Any, Dict, List

from synapse.handlers.oidc import OidcMappingProvider, Token, UserAttributeDict
from synapse.handlers.sso import MappingException
from synapse.module_api import ModuleApi

mxid_localpart_allowed_characters = frozenset(
    "_-./=" + string.ascii_lowercase + string.digits
)


@attr.s(slots=True, frozen=True, auto_attribs=True)
class ProConnectMappingConfig:
    user_id_lookup_fallback_rules: List[Dict[str, str]]= []

class ProConnectMappingProvider(OidcMappingProvider[ProConnectMappingConfig]):
    def __init__(self, config: ProConnectMappingConfig, module_api: ModuleApi):
        self.module_api = module_api
        self._config = config

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> ProConnectMappingConfig:
        return ProConnectMappingConfig(**config)

    def get_remote_user_id(self, userinfo: UserInfo) -> str:
        if not hasattr(userinfo, 'sub') or not userinfo.sub:
            raise MappingException("The 'sub' attribute is missing or empty in the provided UserInfo object.")
        return str(userinfo.sub)

    async def map_user_attributes(
        self, userinfo: UserInfo, token: Token, failures: int
    ) -> UserAttributeDict:
        if not userinfo.email:
            raise MappingException("No email provided by Pro Connect")

        localpart = None
        # first, check if user exists in the homeserver, search by its email
        mapped_user_id = await self.search_user_id_by_threepid(userinfo.email)

        # If user has been found, try to map it to the proconnect identity
        if mapped_user_id:
            user_info = await self.module_api.get_userinfo_by_id(mapped_user_id)
            if user_info and not user_info.is_deactivated:
                localpart = user_info.user_id.localpart

        # If user has not been mapped, create a new localpart
        if not localpart:
            if not await self.module_api._password_auth_provider.is_3pid_allowed(
                "email", userinfo.email, True
            ):
                raise MappingException(
                    "Votre administration n'est pas encore présente sur Tchap, inscrivez-la sur https://tchap.numerique.gouv.fr/"
                )

            # filter out invalid characters
            filtered = filter(
                lambda c: c in mxid_localpart_allowed_characters,
                userinfo.email.replace("@", "-").lower(),
            )
            desired_localpart = "".join(filtered)

            # Loop until we find a available localpart. 
            # It means a localpart that don't exist or that is not taken by a deactivated account
            available_localpart_found = False
            while not available_localpart_found:
                # localpart intents are built on the model : localpart1, localpart2..
                localpart = desired_localpart + (str(failures) if failures else "")
                user_info = await self.module_api.get_userinfo_by_id(
                    f"@{localpart}:{self.module_api.server_name}"
                )
                if user_info and user_info.is_deactivated:
                    failures += 1
                else:
                    available_localpart_found = True

        # create display name
        display_name = await self.module_api._password_auth_provider.get_displayname_for_registration(
            {"m.login.email.identity": {"address": userinfo.email}},
            {},
        )

        return UserAttributeDict(  # type: ignore
            localpart=localpart,
            emails=[userinfo.email],
            confirm_localpart=False,
            display_name=display_name,
        )
    
    # Search user ID by its email, retrying with replacements if necessary.
    async def search_user_id_by_threepid(self, email: str)-> str | None:
        # Try to find the user ID using the provided email
        userId = await self.module_api._store.get_user_id_by_threepid("email", email)

        # If userId is not found, attempt replacements
        # Iterate through all fallback rules 
        if not userId:
            for rule in self._config.user_id_lookup_fallback_rules:
                replaced_email = email

                # If rule matches, retry the lookup with a modified_email 
                if "match" in rule and rule["match"] in email:
                    replaced_email = email.replace(rule["match"], rule["search"])
                    userId = await self.module_api._store.get_user_id_by_threepid(
                        "email", replaced_email
                    )

                    # Stop if a userId is found
                    if userId:
                        break

        return userId