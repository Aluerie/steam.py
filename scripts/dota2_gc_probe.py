"""
A script to check ``steam.ext.dota2`` against the real Dota 2 Game Coordinator.

Logs in, waits for the Game Coordinator, then runs every request the extension makes and prints PASS/FAIL/INFO lines
with a summary at the end. Exits with code 1 if anything failed.

Run it from the repository root::

    python scripts/dota2_gc_probe.py

Configuration comes from environment variables or a ``.env`` file in the current directory:

* ``STEAM_USERNAME``, ``STEAM_PASSWORD``: the account to log in with, prompted for if missing.
  Use a throwaway: logging in starts Dota 2 on it.
* ``STEAM_SHARED_SECRET``: optional, otherwise Steam may ask for a Steam Guard code.
* ``MATCH_IDS``: optional comma-separated finished match ids, fetched from OpenDota's recent pro matches if missing.

Licensed under The MIT License (MIT) - Copyright (c) 2020-present James H-B. See LICENSE
"""

from __future__ import annotations

import asyncio
import datetime
import getpass
import os
import re
import sys
import time
import traceback
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

from steam.ext import dota2
from steam.ext.dota2.protobufs import client_messages as cm, watch

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from steam.protobufs.msg import GCProtobufMessage

BAD_MATCH_ID = 1
results: list[tuple[str, str, str]] = []


def report(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""), flush=True)


def check(name: str, ok: bool, detail: str = "") -> None:
    report(name, "PASS" if ok else "FAIL", detail)


async def timed(awaitable: Awaitable[Any]) -> tuple[Any, BaseException | None, float]:
    start = time.perf_counter()
    try:
        return await awaitable, None, time.perf_counter() - start
    except Exception as exc:
        return None, exc, time.perf_counter() - start


def load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE lines from a .env file, without overriding variables that are already set."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if value:
            os.environ.setdefault(key.strip(), value)


def finished_match_ids() -> list[int]:
    """Get a few finished match ids from ``MATCH_IDS`` or OpenDota's recent pro matches."""
    if ids := os.getenv("MATCH_IDS"):
        return [int(x) for x in ids.split(",") if x.strip()]
    request = urllib.request.Request("https://api.opendota.com/api/proMatches", headers={"User-Agent": "steam.py"})
    try:
        # the full response often stalls midway, but the newest matches come first
        with urllib.request.urlopen(request, timeout=30) as response:
            head = response.read(8192).decode(errors="ignore")
        ids = [int(id) for id in re.findall(r'"match_id":(\d+)', head)[:5]]
        if not ids:
            raise ValueError("no match ids in the response")
        return ids
    except Exception as exc:
        report("fetch match ids from OpenDota", "INFO", f"{exc!r}, set MATCH_IDS to run the match tests")
        return []


async def check_job_id_echo(client: dota2.Client, match_id: int | None) -> None:
    """Report whether the GC copies a request's job id into its response, which the extension relies on."""
    state = client._state
    ws = client.ws
    requests: list[tuple[GCProtobufMessage, type[GCProtobufMessage]]] = [
        (cm.ProfileRequest(account_id=client.user.id), cm.ProfileResponse),
        (cm.ClientToGCRankRequest(rank_type=cm.ERankType.RankedGlicko), cm.GCToClientRankResponse),
        (cm.GetPlayerMatchHistory(account_id=client.user.id, matches_requested=1), cm.GetPlayerMatchHistoryResponse),
        (cm.MatchmakingStatsRequest(), cm.MatchmakingStatsResponse),
    ]
    if match_id:
        requests.append((cm.MatchDetailsRequest(match_id=match_id), cm.MatchDetailsResponse))
        requests.append(
            (watch.ClientToGCMatchesMinimalRequest(match_ids=[match_id]), watch.ClientToGCMatchesMinimalResponse)
        )
    for request, response_type in requests:
        name = f"job id echo: {type(request).__name__}"
        # the lock keeps the extension's own requests from taking this response
        async with state._request_locks[response_type]:
            request.header.job_id_source = job_id = ws.next_gc_job_id
            future = ws.gc_wait_for(response_type)
            try:
                await ws.send_gc_message(request)
                async with asyncio.timeout(8):
                    response = await future
            except TimeoutError:
                report(name, "INFO", "no response")
                continue
            finally:
                future.cancel()
        echoed = response.header.job_id_target == job_id
        # matchmaking stats is the one request the GC answers without the job id
        expected = response_type is not cm.MatchmakingStatsResponse
        report(name, "PASS" if echoed == expected else "FAIL", "echoed" if echoed else "not echoed")


async def check_matches(client: dota2.Client, match_ids: list[int]) -> None:
    _, exc, took = await timed(client.create_partial_match(BAD_MATCH_ID).details())
    check(
        "match details: bad id raises MatchNotFound", isinstance(exc, dota2.MatchNotFound), f"{exc!r} after {took:.2f}s"
    )

    if not match_ids:
        return
    match_id = match_ids[0]
    details, exc, took = await timed(client.create_partial_match(match_id).details())
    check(
        "match details: good id", details is not None and details.id == match_id, repr(exc) if exc else f"{took:.2f}s"
    )

    minimal, exc, _ = await timed(client.create_partial_match(match_id).minimal())
    check("match minimal", minimal is not None and minimal.id == match_id, repr(exc) if exc else "")
    if minimal:
        items = [item for player in minimal.players for item in player.items]
        unknown = [item for item in items if not isinstance(item, dota2.Item) or item.name.endswith("UnknownValue")]
        check("match minimal: items are known Item members", bool(items) and not unknown, f"unknown: {unknown}")

    _, exc, _ = await timed(client.create_partial_match(BAD_MATCH_ID).minimal())
    check("match minimal: bad id raises MatchNotFound", isinstance(exc, dota2.MatchNotFound), repr(exc))

    start = time.perf_counter()
    for id in match_ids:
        await client.create_partial_match(id).details()
    sequential = time.perf_counter() - start
    start = time.perf_counter()
    r = await asyncio.gather(
        *(client.create_partial_match(id).details() for id in match_ids),
        client.create_partial_match(BAD_MATCH_ID).details(),
        return_exceptions=True,
    )
    concurrent = time.perf_counter() - start
    ok = [getattr(x, "id", None) for x in r[:-1]] == match_ids and isinstance(r[-1], dota2.MatchNotFound)
    check(
        f"match details: {len(match_ids)} good + 1 bad at once each get their own response",
        ok,
        f"sequential {sequential:.2f}s vs concurrent {concurrent:.2f}s" if ok else repr(r),
    )


async def check_users(client: dota2.Client, player_ids: list[int]) -> None:
    me = client.user
    ids = [me.id, *player_ids[:3]]

    profiles = await asyncio.gather(*(client._state.fetch_dota2_profile(id) for id in ids), return_exceptions=True)
    kinds = [type(p).__name__ if isinstance(p, BaseException) else "ok" for p in profiles]
    check("profile: own one loads", kinds[0] == "ok", kinds[0])
    # a fresh account is refused other people's profiles (TooBusy); that has to raise, not return an empty profile
    # limited accounts are refused every profile but their own, which has to raise, not return an empty profile
    check(
        "profile: other players load or raise ProfileUnavailable",
        all(kind in {"ok", "ProfileUnavailable"} for kind in kinds[1:]),
        str(kinds[1:]),
    )

    cards = await asyncio.gather(
        *(client.create_partial_user(id).dota2_profile_card() for id in ids), return_exceptions=True
    )
    got = [card.user.id if isinstance(card, dota2.ProfileCard) else repr(card) for card in cards]
    check(f"profile cards: {len(ids)} at once each get their own", got == ids, "" if got == ids else str(got))

    for name, awaitable in [
        ("own match history", me.match_history(matches_requested=5)),
        ("glicko rating", me.glicko_rating()),
        ("behavior summary", me.behavior_summary()),
        ("matchmaking stats", client.matchmaking_stats()),
    ]:
        _, exc, took = await timed(awaitable)
        check(name, exc is None, repr(exc) if exc else f"{took:.2f}s")


async def check_live_matches(client: dota2.Client, live: list[dota2.LiveMatch]) -> None:
    hero = next((p.hero for p in live[0].players if p.hero), None)
    if hero:
        res, exc, took = await timed(client.top_live_matches(hero=hero, limit=100))
        check(
            f"top live matches filtered by {hero.name}", exc is None, repr(exc) if exc else f"{len(res)} in {took:.2f}s"
        )

    league_id = next((m.tournament.league_id for m in live if m.tournament), None)
    if league_id:
        res, exc, _ = await timed(client.tournament_live_matches(league_id))
        check(
            f"tournament live matches for league {league_id}", exc is None, repr(exc) if exc else f"{len(res)} matches"
        )

    single, exc, _ = await timed(client.live_matches(lobby_id=live[0].lobby_id))
    check(
        "live match by lobby_id", single is not None and single.lobby_id == live[0].lobby_id, repr(exc) if exc else ""
    )

    # more than the 20 lobby ids the GC answers per request, so the lookup has to be split
    lobby_ids = [m.lobby_id for m in live[:35]]
    res, exc, took = await timed(client.live_matches(lobby_ids=lobby_ids))
    got = {m.lobby_id for m in res} if res else set()
    check(
        f"live matches by {len(lobby_ids)} lobby_ids return exactly those",
        exc is None and got == set(lobby_ids),
        repr(exc) if exc else f"{len(res)} matches in {took:.2f}s",
    )

    r = await asyncio.gather(
        client.top_live_matches(limit=20), client.live_matches(lobby_ids=lobby_ids[:3]), return_exceptions=True
    )
    ok = not any(isinstance(x, BaseException) for x in r) and {m.lobby_id for m in r[1]} == set(lobby_ids[:3])
    check("top live matches + lobby lookup at once don't mix", ok, "" if ok else repr(r))

    _, exc, _ = await timed(client.live_matches(lobby_id=1))
    check("live match by unknown lobby_id raises MatchNotFound", isinstance(exc, dota2.MatchNotFound), repr(exc))

    _, exc, _ = await timed(client.live_matches())
    check("live_matches() without arguments raises TypeError", isinstance(exc, TypeError), repr(exc))
    res, exc, _ = await timed(client.live_matches(lobby_ids=[]))
    check("live_matches(lobby_ids=[]) returns []", res == [], repr(exc) if exc else f"got {res!r}")

    bad = [m.end_time for m in live if m.end_time is not None and not isinstance(m.end_time, datetime.datetime)]
    check("live match end_time is a datetime or None", not bad, repr(bad[:3]))


async def run_checks(client: dota2.Client) -> None:
    print(f"\nLogged in, Game Coordinator ready. Account id32={client.user.id}\n", flush=True)
    match_ids = finished_match_ids()

    live, exc, _ = await timed(client.top_live_matches(limit=100))
    check("top live matches", exc is None and bool(live), repr(exc) if exc else f"{len(live)} matches")
    live = live or []
    player_ids = [p.id for m in live for p in m.players if p.id]

    await check_job_id_echo(client, match_ids[0] if match_ids else None)
    await check_matches(client, match_ids)
    await check_users(client, player_ids)
    if live:
        await check_live_matches(client, live)


async def main() -> int:
    load_dotenv()
    username = os.getenv("STEAM_USERNAME") or input("Steam username: ")
    password = os.getenv("STEAM_PASSWORD") or getpass.getpass("Steam password: ")
    kwargs = {}
    if shared_secret := os.getenv("STEAM_SHARED_SECRET"):
        kwargs["shared_secret"] = shared_secret

    client = dota2.Client()
    async with client:
        login = asyncio.create_task(client.login(username, password, **kwargs))
        ready = asyncio.create_task(client.wait_until_gc_ready())
        done, _ = await asyncio.wait({login, ready}, timeout=180, return_when=asyncio.FIRST_COMPLETED)
        if login in done:
            login.result()  # login ended early: raise its error
            raise RuntimeError("login returned before the Game Coordinator was ready")
        if ready not in done:
            raise RuntimeError("the Game Coordinator wasn't ready after 180s")
        try:
            await run_checks(client)
        except Exception:
            traceback.print_exc()
            report("probe crashed", "FAIL")
        finally:
            await client.close()
            login.cancel()

    print("\n==== summary ====")
    for name, status, detail in results:
        print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    failed = sum(status == "FAIL" for _, status, _ in results)
    print(f"\n{failed} failed" if failed else "\nall passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
