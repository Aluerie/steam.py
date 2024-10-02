# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: base_gcmessages.proto
# plugin: python-betterproto

from __future__ import annotations

from dataclasses import dataclass

import betterproto

# PROFILE


@dataclass(eq=False, repr=False)
class SOEconItem(betterproto.Message):
    id: int = betterproto.uint64_field(1)
    account_id: int = betterproto.uint32_field(2)
    inventory: int = betterproto.uint32_field(3)
    def_index: int = betterproto.uint32_field(4)
    quantity: int = betterproto.uint32_field(5)
    level: int = betterproto.uint32_field(6)
    quality: int = betterproto.uint32_field(7)
    flags: int = betterproto.uint32_field(8)
    origin: int = betterproto.uint32_field(9)
    attribute: list[SOEconItemAttribute] = betterproto.message_field(12)
    interior_item: SOEconItem = betterproto.message_field(13)
    style: int = betterproto.uint32_field(15)
    original_id: int = betterproto.uint64_field(16)
    equipped_state: list[SOEconItemEquipped] = betterproto.message_field(18)


@dataclass(eq=False, repr=False)
class SOEconItemAttribute(betterproto.Message):
    def_index: int = betterproto.uint32_field(1)
    value: int = betterproto.uint32_field(2)
    value_bytes: bytes = betterproto.bytes_field(3)


@dataclass(eq=False, repr=False)
class SOEconItemEquipped(betterproto.Message):
    new_class: int = betterproto.uint32_field(1)
    new_slot: int = betterproto.uint32_field(2)