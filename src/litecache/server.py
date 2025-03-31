import asyncio
import logging
import click
import uvloop
from .parser import RespParser
from . import logger

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

OK = "+OK"


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


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", type=int, default=6379, help="Port to listen on")
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (e.g., -v for INFO, -vv for DEBUG)",
)
def start(host: str, port: int, verbose: int) -> None:
    """Start the LiteCache async TCP server."""
    # Set logging level based on verbosity count
    if verbose == 0:
        logger.setLevel(logging.WARNING)  # Silent except for warnings/errors
    elif verbose == 1:
        logger.setLevel(logging.INFO)  # Info logs
    elif verbose >= 2:
        logger.setLevel(logging.DEBUG)  # Debug logs
    click.secho(f"Starting LiteCache on {host}:{port}", fg="green")
    server = LiteCache(host, port)
    asyncio.run(server.run())


if __name__ == "__main__":
    start()
