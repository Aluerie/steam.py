"""Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from functools import partial
from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict, TypeVar, Unpack

from ..._gc import GCState as GCState_
from ...app import DOTA2
from ...enums import Result
from ...id import _ID64_TO_ID32
from ...models import return_true
from ...protobufs.msg import GCProtobufMessage
from ...state import parser
from .errors import GCRequestFailed, MatchNotFound, ProfileUnavailable
from .models import PartialUser, User
from .protobufs import client_messages, common, sdk, watch

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from weakref import WeakValueDictionary

    from ...protobufs import friends
    from ...types.id import ID32, ID64, Intable
    from .client import Client

    # TODO: test this whole Kwargs thing, does it error if we don't provide some of them?
    # what defaults does it assume?

    class MatchHistoryKwargs(TypedDict):
        account_id: int
        start_at_match_id: NotRequired[int]
        matches_requested: int
        hero_id: NotRequired[int]
        include_practice_matches: bool
        include_custom_games: bool
        include_event_games: bool
        request_id: NotRequired[int]

    class PostSocialMessageKwargs(TypedDict):
        message: NotRequired[str]
        match_id: NotRequired[int]
        match_timestamp: NotRequired[int]

    class TopSourceTVGamesKwargs(TypedDict):
        search_key: NotRequired[str]
        league_id: NotRequired[int]
        hero_id: NotRequired[int]
        start_game: NotRequired[int]
        game_list_index: NotRequired[int]
        lobby_ids: NotRequired[list[int]]


TIMEOUT_DEFAULT = 8.0  # not sure which value would suit the best;

ResponseT = TypeVar("ResponseT", bound=GCProtobufMessage)


class GCState(GCState_[Any]):  # TODO: implement basket-analogy for dota2
    client: Client  # type: ignore  # PEP 705
    _users: WeakValueDictionary[ID32, User]
    _APP = DOTA2  # type: ignore

    def __init__(self, client: Client, **kwargs: Any):
        super().__init__(client, **kwargs)
        # The GC dispatcher resolves every listener whose check passes, so requests whose responses can't be told
        # apart (no job id echo, nothing to check) are serialised per response type.
        self._request_locks: defaultdict[type[GCProtobufMessage], asyncio.Lock] = defaultdict(asyncio.Lock)

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

    # dota fetch proto calls
    # the difference between these calls and the ones in `client`/`models` is that
    # they directly give proto-response while the latter modelize them into more convenient formats.

    async def _send_and_wait(
        self,
        request: GCProtobufMessage,
        response_type: type[ResponseT],
        *,
        check: Callable[[ResponseT], bool] = return_true,
        match: Literal["job_id", "lock", "check"] = "job_id",
    ) -> ResponseT:
        """Send a GC request and wait for its response.

        ``match`` says how the response is tied to this request:

        * ``"job_id"``: the GC echoes the request's job id back in the response header, so requests run in parallel.
        * ``"lock"``: only one request per response type is in flight at a time.
        * ``"check"``: ``check`` alone identifies the response.
        """
        if match == "lock":
            async with self._request_locks[response_type]:
                return await self._send_and_wait(request, response_type, check=check, match="check")

        if match == "job_id":
            request.header.job_id_source = job_id = self.ws.next_gc_job_id
            user_check = check

            def check(msg: ResponseT) -> bool:
                return msg.header.job_id_target == job_id and user_check(msg)

        # register the listener before sending so a fast response can't be missed
        future = self.ws.gc_wait_for(response_type, check=check)
        try:
            await self.ws.send_gc_message(request)
            async with asyncio.timeout(TIMEOUT_DEFAULT):
                return await future
        finally:
            future.cancel()  # no-op if it already has a result; otherwise the dispatcher drops the listener

    async def fetch_top_source_tv_games(
        self, **kwargs: Unpack[TopSourceTVGamesKwargs]
    ) -> list[watch.GCToClientFindTopSourceTVGamesResponse]:
        """Fetch Top Source TV Games."""
        # a lookup by lobby_ids is answered with a single response holding every requested game
        # (start_game 0, specific_games True), so it never pages
        specific_games = bool(kwargs.get("lobby_ids"))
        if specific_games:
            kwargs.pop("start_game", None)
        start_game = kwargs.get("start_game") or 0

        # # if start_game and (start_game < 0 or start_game > 90): # TODO: ???
        # #     # in my experience it never answers in these cases
        # #     raise ValueError("start_game should be between 0 and 90 inclusively.")

        def check(start_game: int, msg: watch.GCToClientFindTopSourceTVGamesResponse) -> bool:
            return msg.start_game == start_game and msg.specific_games == specific_games

        # responses only carry `start_game`, so concurrent searches with different filters would mix up pages
        async with self._request_locks[watch.GCToClientFindTopSourceTVGamesResponse]:
            futures = [
                self.ws.gc_wait_for(
                    watch.GCToClientFindTopSourceTVGamesResponse,
                    check=partial(check, start_game),
                )
                for start_game in range(0, start_game + 1, 10)
            ]
            try:
                await self.ws.send_gc_message(watch.ClientToGCFindTopSourceTVGames(**kwargs))
                async with asyncio.timeout(TIMEOUT_DEFAULT):
                    # each response.game_list is 10 games (except possibly last one if filtered by)
                    return await asyncio.gather(*futures)
            finally:
                for future in futures:
                    future.cancel()

    async def fetch_dota2_profile(self, account_id: int) -> client_messages.ProfileResponse:
        """Fetch user's dota 2 profile."""
        response = await self._send_and_wait(
            client_messages.ProfileRequest(account_id=account_id), client_messages.ProfileResponse
        )
        if response.eresult != client_messages.ProfileResponseEResponse.Success:
            # betterproto gives a plain int here
            reason = client_messages.ProfileResponseEResponse(response.eresult)
            raise ProfileUnavailable(response, account_id=account_id, reason=reason)
        return response

    async def fetch_dota2_profile_card(self, account_id: int) -> common.ProfileCard:
        """Fetch user's dota 2 profile card."""
        return await self._send_and_wait(
            client_messages.ClientToGCGetProfileCard(account_id=account_id),
            common.ProfileCard,
            check=lambda msg: msg.account_id == account_id,
            match="check",
        )

    async def fetch_match_history(
        self,
        **kwargs: Unpack[MatchHistoryKwargs],
    ) -> client_messages.GetPlayerMatchHistoryResponse:
        """Fetch match history."""
        return await self._send_and_wait(
            client_messages.GetPlayerMatchHistory(**kwargs), client_messages.GetPlayerMatchHistoryResponse
        )

    async def fetch_matches_minimal(self, match_ids: list[int]) -> watch.ClientToGCMatchesMinimalResponse:
        """Fetch matches minimal."""
        return await self._send_and_wait(
            watch.ClientToGCMatchesMinimalRequest(match_ids=match_ids), watch.ClientToGCMatchesMinimalResponse
        )

    async def fetch_match_details(self, match_id: int) -> client_messages.MatchDetailsResponse:
        """Fetch match details."""
        # a failed response has an empty `match` (match_id 0), so only the job id ties it to this request;
        # `eresult` is a Steam result code
        response = await self._send_and_wait(
            client_messages.MatchDetailsRequest(match_id=match_id), client_messages.MatchDetailsResponse
        )
        if response.eresult != Result.OK:
            raise MatchNotFound(response, match_id=match_id)
        return response

    async def fetch_rank(self, rank_type: client_messages.ERankType) -> client_messages.GCToClientRankResponse:
        """Fetch rank."""
        response = await self._send_and_wait(
            client_messages.ClientToGCRankRequest(rank_type=rank_type), client_messages.GCToClientRankResponse
        )
        if response.result_enum != client_messages.GCToClientRankResponseEResultCode.k_Succeeded:
            raise GCRequestFailed(response)
        return response

    async def post_social_message(
        self, **kwargs: Unpack[PostSocialMessageKwargs]
    ) -> client_messages.GCToClientSocialFeedPostMessageResponse:
        """Post social message."""
        response = await self._send_and_wait(
            client_messages.ClientToGCSocialFeedPostMessageRequest(**kwargs),
            client_messages.GCToClientSocialFeedPostMessageResponse,
            match="lock",  # job id echo unverified: probing it would post to the feed
        )
        if not response.success:
            raise GCRequestFailed(response)
        return response

    async def fetch_matchmaking_stats(self) -> client_messages.MatchmakingStatsResponse:
        """Fetch matchmaking stats."""
        # the GC doesn't echo the job id here, but every response is the same global snapshot,
        # so any of them answers any request
        return await self._send_and_wait(
            client_messages.MatchmakingStatsRequest(), client_messages.MatchmakingStatsResponse, match="check"
        )
