"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

import asyncio
import logging
from inspect import get_annotations
from typing import TYPE_CHECKING, Any, ClassVar, Final, cast, overload

from ..client import Client as Client_
from ..gateway import RAISED_EXCEPTIONS
from ..user import ClientUser as ClientUser_
from .state import GCState

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Self

    from ..app import App
    from ..enums import Language
    from ..trade import Inventory, Item
    from ..types.id import AppID
    from ..utils import cached_property

__all__ = ("Client",)

log = logging.getLogger(__name__)


class ClientUser(ClientUser_):
    _state: GCState[Any]

    async def inventory(
        self, app: App, *, context_id: int | None = None, language: Language | None = None
    ) -> Inventory[Item[Self], Self]:
        return (  # type: ignore
            self._state.backpacks[app.id]
            if app.id in self._state.backpacks and self._state._gc_ready.is_set()
            else await super().inventory(app, context_id=context_id, language=language)
        )


class Client(Client_):
    _state: GCState[Any]
    _GC_HEART_BEAT: ClassVar = 30.0

    _ClientUserCls: ClassVar[type[ClientUser]] = ClientUser  # ideally one day this will be a generic
    _GC_BASES: Final[tuple[type[GCState[Any]], ...]] = ()
    _GC_APPS: Final[Mapping[AppID, App]] = {}
    user: cached_property[Self, ClientUser]  # type: ignore

    def __init_subclass__(cls) -> None:
        bases = [base for base in cls.__mro__ if issubclass(base, Client) and base is not Client]
        previous_state = None
        cls._GC_BASES = cast(  # type: ignore
            tuple[type[GCState[Any]], ...],
            tuple(
                dict.fromkeys(
                    previous_state := get_annotations(base, eval_str=True).get("_state", previous_state)
                    for base in reversed(bases)
                )
            ),
        )
        cls._GC_APPS = {  # type: ignore
            base._APP.id: base._APP for base in cls._GC_BASES
        }  # fmt: skip

        seen_methods = set[str]()
        for base in cls._GC_BASES:
            if (
                overridden_methods := seen_methods & base.__dict__.keys()
            ):  # How do we deal with subclasses of the same state overriding the method? Is anyone even going to do that?
                raise TypeError(f"Method(s) {', '.join(overridden_methods)} conflict inside of the state subclasses")
            seen_methods |= base.__dict__.keys()

    def _get_state(self, **options: Any) -> GCState[Any]:
        return type("GCState", self._GC_BASES, {})(self, **options)

    async def _ping_gc(self) -> None:
        while not self.is_closed():
            # cleared while the connection to Steam is down, so pinging pauses until it's back
            await self._state.login_complete.wait()
            try:
                for base in self._GC_BASES:
                    if (msg := base._get_gc_message(self._state)) is not None:
                        await self._state.ws.send_gc_message(msg)
            except RAISED_EXCEPTIONS:
                log.debug("Couldn't ping the GC, the connection to Steam dropped")
            except Exception:
                log.exception("Failed to ping the GC")
            await asyncio.sleep(self._GC_HEART_BEAT)

    def is_gc_ready(self) -> bool:
        return self._state._gc_ready.is_set()

    @overload
    async def login(
        self,
        username: str,
        password: str,
        *,
        shared_secret: str = ...,
        identity_secret: str = ...,
    ) -> None: ...

    @overload
    async def login(
        self,
        *,
        refresh_token: str,
        shared_secret: str = ...,
        identity_secret: str = ...,
    ) -> None: ...

    async def login(self, *args: Any, **kwargs: Any) -> None:
        ping = asyncio.create_task(self._ping_gc(), name="steam.py: GC ping")
        try:
            await super().login(*args, **kwargs)
        finally:
            # the ping loop can be stuck waiting for a login that's never coming once the client is closed
            ping.cancel()
            await asyncio.wait([ping])

    async def _handle_ready(self) -> None:
        us = self._state._original_client_user_msg
        assert us is not None
        current_user = self._state.user
        user = self.http.user = self.__class__._ClientUserCls(self._state, us)
        user._friends = current_user._friends
        user._inventory_locks = current_user._inventory_locks
        self._state.user = user
        await super()._handle_ready()

    async def wait_until_gc_ready(self) -> None:
        """Wait for the :meth:`on_gc_ready` method to be dispatched.

        See Also
        --------
        :meth:`wait_for_ready`
        """
        await self._state._gc_ready.wait()

    # async def buy_item(self, def_index: int, price: int, def_indexes: list[int], prices: int) -> None:
    #     ...
