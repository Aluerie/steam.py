"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..._const import timeout
from ..._gc import GCState as GCState_
from ...app import DOTA2
from ...id import _ID64_TO_ID32
from ...state import parser
from .models import PartialUser, User
from .protobufs import client_messages, common, sdk

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from weakref import WeakValueDictionary

    from ...protobufs import friends
    from ...types.id import ID32, ID64, Intable
    from .client import Client


class GCState(GCState_[Any]):  # todo: implement basket-analogy for dota2
    client: Client  # type: ignore  # PEP 705
    _users: WeakValueDictionary[ID32, User]
    _APP = DOTA2  # type: ignore

    def _store_user(self, proto: friends.CMsgClientPersonaStateFriend) -> User:
        try:
            user = self._users[_ID64_TO_ID32(proto.friendid)]
        except KeyError:
            user = User(state=self, proto=proto)
            self._users[user.id] = user
        else:
            user._update(proto)
        return user

    def get_partial_user(self, id: Intable) -> PartialUser:
        return PartialUser(self, id)

    if TYPE_CHECKING:

        def get_user(self, id: ID32) -> User | None: ...

        async def fetch_user(self, user_id64: ID64) -> User: ...

        async def fetch_users(self, user_id64s: Iterable[ID64]) -> Sequence[User]: ...

        async def _maybe_user(self, id: Intable) -> User: ...

        async def _maybe_users(self, id64s: Iterable[ID64]) -> Sequence[User]: ...

    def _get_gc_message(self) -> sdk.ClientHello:
        return sdk.ClientHello()

    async def fetch_user_dota2_profile_card(self, user_id: int) -> common.ProfileCard:
        await self.ws.send_gc_message(client_messages.ClientToGCGetProfileCard(account_id=user_id))
        return await self.ws.gc_wait_for(
            common.ProfileCard,
            check=lambda msg: msg.account_id == user_id,
        )

    async def fetch_match_details(self, match_id: int) -> client_messages.MatchDetailsResponse:
        await self.ws.send_gc_message(client_messages.MatchDetailsRequest(match_id=match_id))
        async with timeout(15.0):
            return await self.ws.gc_wait_for(
                client_messages.MatchDetailsResponse,
                check=lambda msg: msg.match.match_id == match_id,
            )

    @parser
    def parse_client_goodbye(self, msg: sdk.ConnectionStatus | None = None) -> None:
        if msg is None or msg.status == sdk.GCConnectionStatus.NoSession:
            self.dispatch("gc_disconnect")
            self._gc_connected.clear()
            self._gc_ready.clear()
        if msg is not None:
            self.dispatch("gc_status_change", msg.status)

    @parser
    async def parse_gc_client_connect(self, msg: sdk.ClientWelcome) -> None:
        if not self._gc_ready.is_set():
            self._gc_ready.set()
            self.dispatch("gc_ready")