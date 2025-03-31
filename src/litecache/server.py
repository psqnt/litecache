import asyncio
import os
import yaml
import logging
import click
import uvloop
from typing import Optional
from .parser import RespParser
from . import logger

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

OK = "+OK"

# Environment Variables
LITECACHE_CONFIG = "LITECACHE_CONFIG"
LITECACHE_HOST = "LITECACHE_HOST"
LITECACHE_PORT = "LITECACHE_PORT"
LITECACHE_VERBOSE = "LITECACHE_VERBOSE"


class LiteCache:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.cache = {}
        self.parser = RespParser()

    async def read_complete_command(self, reader: asyncio.StreamReader) -> bytes:
        line = await reader.readline()
        if not line:
            return b""
        if not line.startswith(b"*"):
            raise ValueError(f"Expected array (*), got: {line.decode().rstrip()}")
        num_elements = int(line[1:].decode().rstrip())
        data = line
        for _ in range(num_elements):
            length_line = await reader.readline()
            data += length_line
            length = int(length_line[1:].decode().rstrip())
            if length != -1:
                value = await reader.readexactly(length + 2)
                data += value
        return data

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        addr = writer.get_extra_info("peername")
        logger.info(f"New connection {addr}")
        try:
            while True:
                data = await self.read_complete_command(reader)
                if not data:
                    break
                logger.debug(f"Raw: {data}")
                command = self.parser.parse(data)
                logger.info(f"Received from {addr}: {command!r}")
                cmd = command[0].upper() if command else ""
                if cmd == "SET" and len(command) == 3:
                    key, value = command[1], command[2]
                    self.cache[key] = value
                    writer.write(self.parser.serialize(OK))
                elif cmd == "GET" and len(command) == 2:
                    key = command[1]
                    value = self.cache.get(key)
                    writer.write(self.parser.serialize(value))
                elif cmd == "DEL" and len(command) == 2:
                    try:
                        del self.cache[command[1]]
                        writer.write(self.parser.serialize(1))
                    except Exception:
                        writer.write(self.parser.serialize(0))
                else:
                    writer.write(self.parser.serialize("-ERR invalid command"))
                await writer.drain()
        except Exception as e:
            logger.error(f"Error with {addr}: {e}")
            writer.write(self.parser.serialize(f"-ERR {str(e)}"))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Closed connection from {addr}")

    async def run(self) -> None:
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        logger.info(f"Server running on {addr}")
        async with server:
            await server.serve_forever()


def load_config(config_file: str) -> dict:
    """Load configuration from a YAML file, return defaults if not found."""
    defaults = {"host": "0.0.0.0", "port": 6379, "verbose": 0}
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
        return {**defaults, **config}
    except (FileNotFoundError, TypeError):  # TypeError if config_file is None
        return defaults


def get_config(
    cli_config: Optional[str],
    cli_host: Optional[str],
    cli_port: Optional[int],
    cli_verbose: Optional[int],
) -> tuple[str, int, int]:
    """Resolve config from CLI, env vars, config file, in that order."""
    # Determine config file path: CLI > Env Var > Default
    config_file = cli_config or os.environ.get(LITECACHE_CONFIG) or "config.yaml"
    config = load_config(config_file)

    # Override with environment variables
    env_host = os.environ.get(LITECACHE_HOST)
    env_port = os.environ.get(LITECACHE_PORT)
    env_verbose = os.environ.get(LITECACHE_VERBOSE)

    if env_host:
        config["host"] = env_host
    if env_port:
        config["port"] = int(env_port)
    if env_verbose:
        config["verbose"] = int(env_verbose)

    # Override with CLI args (highest priority)
    host = cli_host if cli_host is not None else config["host"]
    port = cli_port if cli_port is not None else config["port"]
    verbose = cli_verbose if cli_verbose is not None else config["verbose"]

    return host, port, verbose


@click.command()
@click.option("--config", default=None, help="Path to config YAML file")
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", type=int, default=None, help="Port to listen on")
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Verbosity level (e.g., -v for INFO, -vv for DEBUG)",
)
def start(
    config: Optional[str],
    host: Optional[str],
    port: Optional[int],
    verbose: Optional[int],
) -> None:
    """Start the LiteCache async TCP server."""
    # Resolve configuration
    host, port, verbose_level = get_config(config, host, port, verbose)

    # Set logging level
    if verbose_level == 0:
        logger.setLevel(logging.WARNING)  # Silent by default
    elif verbose_level == 1:
        logger.setLevel(logging.INFO)
    elif verbose_level >= 2:
        logger.setLevel(logging.DEBUG)

    click.secho(f"Starting LiteCache on {host}:{port}", fg="green")
    server = LiteCache(host, port)
    asyncio.run(server.run())


if __name__ == "__main__":
    start()
