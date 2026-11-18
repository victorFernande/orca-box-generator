"""Verify D-Bus routing and ownership without loading libdbus or OrcaSlicer.

These tests exercise Python control flow and ctypes pointer handling. They do not
establish that the native Linux ABI or a live OrcaSlicer session has been tested.
"""

from __future__ import annotations

import ctypes
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


_HELPER = Path(__file__).resolve().parents[1] / "src" / "box_studio" / "linux_ipc.py"
_SPEC = importlib.util.spec_from_file_location("box_linux_ipc_under_test", _HELPER)
assert _SPEC is not None and _SPEC.loader is not None
ipc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ipc)


class FakeFunction:
    """Allow the production helper to declare ctypes function signatures."""

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *arguments):
        return self.callback(*arguments)


class FakeBus:
    service = "com.orcaslicer.OrcaSlicer.InstanceCheck.Object123"
    process_id = 4242

    def __init__(self, case="success"):
        self.case = case
        self.services = [self.service]
        if case == "duplicate":
            self.services.append(self.service + "4")
        elif case == "no_service":
            self.services = []
        self.messages = {}
        self.live_messages = set()
        self.next_handle = 10
        self.closed = 0
        self.connection_unrefs = 0
        self.freed_arrays = 0
        self.sent = []
        self.pid_targets = []
        self.flags = []
        self.array_storage = None
        callbacks = {
            "threads_init_default": lambda: self.case != "thread_failure",
            "bus_get_private": lambda *_: 0 if self.case == "no_bus" else 2,
            "connection_set_exit_on_disconnect": lambda *_: None,
            "message_new_method_call": self.new_message,
            "message_append_args": self.append_args,
            "message_get_args": self.get_args,
            "connection_send_with_reply_and_block": self.daemon_reply,
            "message_get_type": lambda _: 3 if self.case == "daemon_error" else 2,
            "message_set_no_reply": lambda message, value: self.flags.append(
                ("no_reply", message, value)
            ),
            "message_set_auto_start": lambda message, value: self.flags.append(
                ("auto_start", message, value)
            ),
            "connection_send": self.send,
            "connection_flush": lambda _: None,
            "connection_get_is_connected": lambda _: self.case != "disconnect",
            "message_unref": self.unref_message,
            "connection_close": self.close,
            "connection_unref": self.unref_connection,
            "free_string_array": self.free_string_array,
        }
        for name, callback in callbacks.items():
            setattr(self, "dbus_" + name, FakeFunction(callback))

    def new_message(self, destination, path, interface, method):
        handle = self.next_handle
        self.next_handle += 1
        self.messages[handle] = dict(
            destination=destination,
            path=path,
            interface=interface,
            method=method,
            argument=None,
        )
        self.live_messages.add(handle)
        return handle

    def append_args(self, message, kind, argument, terminator):
        assert kind == ord("s") and terminator.value == 0
        record = self.messages[message]
        record["argument"] = argument._obj.value.decode("utf-8")
        return not (
            self.case == "append_failure" and record["method"] == b"AnotherInstance"
        )

    def daemon_reply(self, connection, request, timeout, error):
        assert connection == 2 and timeout == 1500 and error is None
        record = self.messages[request]
        if self.case == "daemon_timeout" or (
            self.case == "owner_lost" and record["method"] == b"GetNameOwner"
        ):
            return 0
        response = self.new_message(b"", b"", b"", record["method"])
        self.messages[response]["argument"] = record["argument"]
        return response

    def get_args(self, message, error, kind, *arguments):
        record = self.messages[message]
        assert error is None and arguments[-1].value == 0
        if kind == ord("a"):
            assert record["method"] == b"ListNames"
            assert arguments[0].value == ord("s")
            self.array_storage = (ctypes.c_char_p * len(self.services))(
                *(name.encode("ascii") for name in self.services)
            )
            ctypes.cast(
                arguments[1], ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
            )[0] = ctypes.cast(self.array_storage, ctypes.POINTER(ctypes.c_char_p))
            arguments[2]._obj.value = len(self.services)
        elif kind == ord("s"):
            assert record["method"] == b"GetNameOwner"
            arguments[0]._obj.value = (
                b":1.42" if record["argument"] == self.service else b":1.43"
            )
        elif kind == ord("u"):
            assert record["method"] == b"GetConnectionUnixProcessID"
            self.pid_targets.append(record["argument"])
            arguments[0]._obj.value = self.process_id + (
                1 if self.case == "wrong_process" else 0
            )
        else:
            raise AssertionError("Unexpected D-Bus argument type")
        return 1

    def send(self, connection, message, serial):
        assert connection == 2
        self.sent.append((message, self.messages[message].copy()))
        serial._obj.value = 7
        return self.case != "send_failure"

    def unref_message(self, message):
        if message not in self.live_messages:
            raise AssertionError("Message unreferenced twice")
        self.live_messages.remove(message)

    def close(self, connection):
        assert connection == 2
        self.closed += 1

    def unref_connection(self, connection):
        assert connection == 2
        self.connection_unrefs += 1

    def free_string_array(self, _array):
        self.freed_arrays += 1


class LinuxTransportTests(unittest.TestCase):
    def test_transport_routing_failures_and_cleanup(self):
        cases = (
            "success",
            "wrong_process",
            "duplicate",
            "no_service",
            "owner_lost",
            "send_failure",
            "disconnect",
            "append_failure",
            "daemon_timeout",
            "daemon_error",
            "no_bus",
            "thread_failure",
        )
        payload = '"orca-slicer.exe";"/tmp/calibration.3mf"'
        for case in cases:
            with self.subTest(case=case):
                fake = FakeBus(case)
                with (
                    patch.object(ipc.sys, "platform", "linux"),
                    patch.object(ipc.ctypes, "CDLL", return_value=fake) as loader,
                ):
                    ok, detail = ipc.send_linux_plater_request(
                        payload, process_id=fake.process_id
                    )
                self.assertEqual(ok, case == "success")
                self.assertTrue(detail)
                loader.assert_called_once_with("libdbus-1.so.3")
                self.assertFalse(fake.live_messages)
                expected_closes = 0 if case in ("no_bus", "thread_failure") else 1
                self.assertEqual(fake.closed, expected_closes)
                self.assertEqual(fake.connection_unrefs, expected_closes)
                expected_arrays = 0 if case in (
                    "no_bus", "thread_failure", "daemon_timeout", "daemon_error"
                ) else 1
                self.assertEqual(fake.freed_arrays, expected_arrays)
                if fake.pid_targets:
                    self.assertTrue(all(name.startswith(":") for name in fake.pid_targets))
                for handle, request in fake.sent:
                    self.assertEqual(request["destination"], b":1.42")
                    self.assertIn(("no_reply", handle, 1), fake.flags)
                    self.assertIn(("auto_start", handle, 0), fake.flags)
                if case == "success":
                    self.assertEqual(fake.pid_targets, [":1.42"])
                    handle, request = fake.sent[0]
                    self.assertEqual(request["destination"], b":1.42")
                    self.assertEqual(request["interface"], fake.service.encode("ascii"))
                    self.assertEqual(
                        request["path"],
                        b"/com/orcaslicer/OrcaSlicer/InstanceCheck/Object123",
                    )
                    self.assertEqual(request["method"], b"AnotherInstance")
                    self.assertEqual(request["argument"], payload)
                    self.assertIn(("no_reply", handle, 1), fake.flags)
                    self.assertIn(("auto_start", handle, 0), fake.flags)
                    self.assertEqual(fake.freed_arrays, 1)
                elif case in ("wrong_process", "duplicate", "no_service", "owner_lost"):
                    self.assertFalse(fake.sent)

    def test_unavailable_platform_does_not_load_native_library(self):
        with (
            patch.object(ipc.sys, "platform", "win32"),
            patch.object(ipc.ctypes, "CDLL") as loader,
        ):
            ok, detail = ipc.send_linux_plater_request("request")
        self.assertFalse(ok)
        self.assertTrue(detail)
        loader.assert_not_called()

    def test_invalid_payload_does_not_load_native_library(self):
        for payload in (None, "", "bad\x00request"):
            with self.subTest(payload=payload):
                with (
                    patch.object(ipc.sys, "platform", "linux"),
                    patch.object(ipc.ctypes, "CDLL") as loader,
                ):
                    ok, detail = ipc.send_linux_plater_request(payload)
                self.assertFalse(ok)
                self.assertTrue(detail)
                loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
