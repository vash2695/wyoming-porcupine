#!/usr/bin/env python3
import argparse
import asyncio
import logging
import platform
import struct
import time
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional

import pvporcupine
from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Attribution, Describe, Info, WakeModel, WakeProgram
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.wake import Detect, Detection, NotDetected

from . import __version__

_LOGGER = logging.getLogger(__name__)
_DIR = Path(__file__).parent

DEFAULT_KEYWORD = "porcupine"


@dataclass
class Keyword:
    """Single porcupine keyword"""

    language: str
    name: str


@dataclass
class Detector:
    porcupine: pvporcupine.Porcupine
    sensitivity: float


class State:
    """State of system"""

    def __init__(self, access_key: str, keywords: Dict[str, Keyword]):
        self.access_key = access_key
        self.keywords = keywords

        # keyword name -> [detector]
        self.detector_cache: Dict[str, List[Detector]] = {}
        self.detector_lock = asyncio.Lock()

    async def get_porcupine(self, keyword_name: str, sensitivity: float) -> Detector:
        keyword = self.keywords.get(keyword_name)
        if keyword is None:
            raise ValueError(f"No keyword {keyword_name}")

        # Check cache first for matching detector
        async with self.detector_lock:
            detectors = self.detector_cache.get(keyword_name, [])
            detector = next(
                (d for d in detectors if d.sensitivity == sensitivity), None
            )
            if detector is not None:
                # Remove from cache for use
                detectors.remove(detector)

                _LOGGER.debug(
                    "Using detector for %s from cache (%s)",
                    keyword_name,
                    len(detectors),
                )
                return detector

        _LOGGER.debug("Loading %s for %s", keyword.name, keyword.language)
        
        # Create the Porcupine detector with v3 API
        porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=[keyword_name],
            sensitivities=[sensitivity],
        )

        return Detector(porcupine, sensitivity)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="stdio://", help="unix:// or tcp://")
    parser.add_argument(
        "--access-key", 
        required=True, 
        help="Access key from Picovoice console"
    )
    parser.add_argument("--sensitivity", type=float, default=0.5)
    parser.add_argument(
        "--language", 
        default="en", 
        help="Language for wake words (en, fr, es, de)"
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    parser.add_argument(
        "--log-format", default=logging.BASIC_FORMAT, help="Format for log messages"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print version and exit",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO, format=args.log_format
    )
    _LOGGER.debug(args)

    # For v3, we need to get a list of available keywords for the specified language
    try:
        available_keywords = pvporcupine.KEYWORDS
        # Filter keywords for the requested language
        language_keywords = [kw for kw in available_keywords if kw.startswith(args.language)]
        
        # Create the keywords dictionary
        keywords: Dict[str, Keyword] = {}
        for kw in language_keywords:
            kw_name = kw.split("_")[0] if "_" in kw else kw
            keywords[kw_name] = Keyword(language=args.language, name=kw_name)
            
        if not keywords:
            _LOGGER.warning(f"No keywords found for language {args.language}")
            _LOGGER.info(f"Available keywords: {', '.join(available_keywords)}")
    except Exception as e:
        _LOGGER.error(f"Error loading available keywords: {e}")
        keywords = {}
        # Add default keyword as fallback
        keywords[DEFAULT_KEYWORD] = Keyword(language="en", name=DEFAULT_KEYWORD)

    wyoming_info = Info(
        wake=[
            WakeProgram(
                name="porcupine3",
                description="On-device wake word detection powered by deep learning",
                attribution=Attribution(
                    name="Picovoice", url="https://github.com/Picovoice/porcupine"
                ),
                installed=True,
                version=__version__,
                models=[
                    WakeModel(
                        name=kw.name,
                        description=f"{kw.name} ({kw.language})",
                        phrase=kw.name,
                        attribution=Attribution(
                            name="Picovoice",
                            url="https://github.com/Picovoice/porcupine",
                        ),
                        installed=True,
                        languages=[kw.language],
                        version="3.0.0",
                    )
                    for kw in keywords.values()
                ],
            )
        ],
    )

    state = State(access_key=args.access_key, keywords=keywords)

    _LOGGER.info("Ready")

    # Start server
    server = AsyncServer.from_uri(args.uri)

    try:
        await server.run(partial(Porcupine3EventHandler, wyoming_info, args, state))
    except KeyboardInterrupt:
        pass


# -----------------------------------------------------------------------------


class Porcupine3EventHandler(AsyncEventHandler):
    """Event handler for clients."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args: argparse.Namespace,
        state: State,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.wyoming_info_event = wyoming_info.event()
        self.client_id = str(time.monotonic_ns())
        self.state = state
        self.converter = AudioChunkConverter(rate=16000, width=2, channels=1)
        self.audio_buffer = bytes()
        self.detected = False

        self.detector: Optional[Detector] = None
        self.keyword_name: str = ""
        self.chunk_format: str = ""
        self.bytes_per_chunk: int = 0

        _LOGGER.debug("Client connected: %s", self.client_id)

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_event)
            _LOGGER.debug("Sent info to client: %s", self.client_id)
            return True

        if Detect.is_type(event.type):
            detect = Detect.from_event(event)
            if detect.names:
                # TODO: use all names
                await self._load_keyword(detect.names[0])
        elif AudioStart.is_type(event.type):
            self.detected = False
        elif AudioChunk.is_type(event.type):
            if self.detector is None:
                # Default keyword
                await self._load_keyword(DEFAULT_KEYWORD)

            assert self.detector is not None

            chunk = AudioChunk.from_event(event)
            chunk = self.converter.convert(chunk)
            self.audio_buffer += chunk.audio

            while len(self.audio_buffer) >= self.bytes_per_chunk:
                unpacked_chunk = struct.unpack_from(
                    self.chunk_format, self.audio_buffer[: self.bytes_per_chunk]
                )
                keyword_index = self.detector.porcupine.process(unpacked_chunk)
                if keyword_index >= 0:
                    _LOGGER.debug(
                        "Detected %s from client %s", self.keyword_name, self.client_id
                    )
                    await self.write_event(
                        Detection(
                            name=self.keyword_name, timestamp=chunk.timestamp
                        ).event()
                    )
                    self.detected = True
                    if AudioStop.is_type(event.type):
                        return True

                self.audio_buffer = self.audio_buffer[self.bytes_per_chunk :]

        elif AudioStop.is_type(event.type):
            if not self.detected:
                # Report no detection
                await self.write_event(NotDetected().event())

        return True

    async def _load_keyword(self, keyword_name: str) -> None:
        """Load a specific wake word model."""
        if self.detector is not None:
            # Cache existing detector
            async with self.state.detector_lock:
                detectors = self.state.detector_cache.setdefault(self.keyword_name, [])
                detectors.append(self.detector)

            self.detector = None
            self.keyword_name = ""
            self.chunk_format = ""
            self.bytes_per_chunk = 0

        self.detector = await self.state.get_porcupine(
            keyword_name, self.cli_args.sensitivity
        )
        self.keyword_name = keyword_name
        self.chunk_format = f"{self.detector.porcupine.frame_length}h"
        self.bytes_per_chunk = self.detector.porcupine.frame_length * 2  # 16-bit


def run():
    """Run from command-line."""
    asyncio.run(main()) 