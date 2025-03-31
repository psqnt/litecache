import asyncio
from .parser import RespParser

HOST = "localhost"
PORT = 6379
OK = "+OK"


class LiteCache:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.cache = {}
        self.parser = RespParser()

    async def read_complete_command(self, reader: asyncio.StreamReader) -> bytes:
        """Read a complete RESP command from the reader."""
        # Read the first line to get the array size
        line = await reader.readline()
        if not line:
            return b""

        if not line.startswith(b"*"):
            raise ValueError(f"Expected array (*), got: {line.decode().rstrip()}")

        num_elements = int(line[1:].decode().rstrip())
        data = line

        # Read each bulk string (length line + data line)
        for _ in range(num_elements):
            length_line = await reader.readline()
            data += length_line
            length = int(length_line[1:].decode().rstrip())
            if length != -1:  # Skip null bulk strings
                value = await reader.readexactly(length + 2)  # +2 for \r\n
                data += value

        return data

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        addr = writer.get_extra_info("peername")
        print(f"New connection {addr}")

        try:
            while True:
                data = await self.read_complete_command(reader)
                if not data:  # client disconnected
                    break

                print(f"Raw: {data}")
                command = self.parser.parse(data)

                print(f"Received from {addr}: {command!r}")
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
                        del self.cache[key]
                        writer.write(self.parser.serialize(1))
                    except Exception:
                        writer.write(self.parser.serialize(2))
                else:
                    writer.write(self.parser.serialize("-ERR invalid command"))
        except Exception as e:
            print(f"Error with {addr}: {e}")
            writer.write(self.parser.serialize(f"-ERR {str(e)}"))
            await writer.drain()

        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Closed connection from {addr}")

    async def run(self) -> None:
        server = await asyncio.start_server(self.handle_client, HOST, PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server running on {addr}")

        async with server:
            await server.serve_forever()

    @staticmethod
    def start() -> None:
        server = LiteCache(HOST, PORT)
        asyncio.run(server.run())
