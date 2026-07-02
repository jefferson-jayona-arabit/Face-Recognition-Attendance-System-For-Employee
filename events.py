# coding: utf-8
"""
Simple in-process event bus.

Usage
-----
Subscribe:
    AppEvents.on("attendance_changed", my_callback)

Fire:
    AppEvents.emit("attendance_changed")

Available events
----------------
    attendance_changed  — new time-in or time-out recorded
    employee_changed    — employee added / updated / deleted
    schedule_changed    — work schedule saved / deleted / activated
    user_changed        — admin account added / updated / deleted
"""
from collections import defaultdict
from typing import Callable


class AppEvents:
    _listeners: dict = defaultdict(list)

    @classmethod
    def on(cls, event: str, callback: Callable):
        if callback not in cls._listeners[event]:
            cls._listeners[event].append(callback)

    @classmethod
    def off(cls, event: str, callback: Callable):
        try:
            cls._listeners[event].remove(callback)
        except ValueError:
            pass

    @classmethod
    def emit(cls, event: str):
        for cb in list(cls._listeners.get(event, [])):
            try:
                cb()
            except Exception as exc:
                print(f"[AppEvents] error in {event} handler: {exc}")
