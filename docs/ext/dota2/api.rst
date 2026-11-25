.. currentmodule:: steam.ext.dota2

API Reference
===============

The following section outlines the API of steam.py's Dota 2 extension module.


Client
------

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :inherited-members:

Bot
----

``ext.dota2`` also provides a :class:`Bot` class, which is a subclass of :class:`Client` and :class:`steam.ext.commands.Bot`.

.. attributetable:: steam.ext.dota2.Bot

.. autoclass:: steam.ext.dota2.Bot
    :members:
    :inherited-members:

Enumerations
------------

.. autoclass:: Item
    :members: display_name, internal_name, from_internal_name

Models
------

.. autoclass:: steam.ext.dota2.PartialUser()
    :members:

.. autoclass:: steam.ext.dota2.User()
    :members:

.. autoclass:: steam.ext.dota2.ClientUser()
    :members:

.. autoclass:: steam.ext.dota2.ProfileCard()
    :members:

.. autoclass:: steam.ext.dota2.PartialMatch()
    :members:

.. autoclass:: steam.ext.dota2.MinimalMatch()
    :members:

.. autoclass:: steam.ext.dota2.MinimalMatchPlayer()
    :members:

.. autoclass:: steam.ext.dota2.DetailedMatch()
    :members:

.. autoclass:: steam.ext.dota2.MatchHistoryMatch()
    :members:

.. autoclass:: steam.ext.dota2.LiveMatch()
    :members:

.. autoclass:: steam.ext.dota2.LiveMatchPlayer()
    :members:

.. autoclass:: steam.ext.dota2.TournamentMatch()
    :members:

.. autoclass:: steam.ext.dota2.TournamentTeam()
    :members:

.. autoclass:: steam.ext.dota2.BattleCup()
    :members:

.. autoclass:: steam.ext.dota2.GlickoRating()
    :members:

.. autoclass:: steam.ext.dota2.BehaviorSummary()
    :members:

Exceptions
-----------

.. autoexception:: Dota2Exception
    :members:

.. autoexception:: GCRequestFailed
    :members:

.. autoexception:: MatchNotFound
    :members:

.. autoexception:: ProfileUnavailable
    :members:
