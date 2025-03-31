from . import logger


class RespParser:
    def parse(self, data: bytes) -> list[str | None]:
        """
        Turn a chunk of RESP bytes into a list of command parts (e.g., ["SET", "foo", "bar"]).
        RESP command look like: *3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n
        """
        if not data:
            return []
        lines = data.decode().splitlines()
        self._check_not_empty(lines)

        num_parts = self._parse_array_header(lines[0])
        command = []
        current_line = 1  # Start after *n

        for _ in range(num_parts):
            if current_line >= len(lines):
                raise ValueError("Ran out of lines before finishing the command")
            part_length = self._parse_bulk_string_length(lines[current_line])
            current_line += 1
            if current_line >= len(lines):
                raise ValueError("Missing the data after the length line")
            command.append(self._parse_bulk_string(lines[current_line], part_length))
            current_line += 1
        return command

    def serialize(self, data) -> bytes:
        """Serialize a response into RESP format (unchanged)."""
        logger.debug(f"Pre-serialized response: {data}")
        if isinstance(data, str) and data.startswith("+"):  # Simple string
            serialized = f"{data}\r\n".encode()
        elif isinstance(data, str) and data.startswith("-"):  # Error
            serialized = f"{data}\r\n".encode()
        elif data is None:  # Null bulk string
            serialized = b"$-1\r\n"
        elif isinstance(data, str):  # Bulk string
            serialized = f"${len(data)}\r\n{data}\r\n".encode()
        elif isinstance(data, int):  # Integer
            serialized = f":{data}\r\n".encode()
        else:
            raise ValueError(f"Unsupported data type for serialization: {type(data)}")
        logger.info(f"Response: {serialized}")
        return serialized

    def _check_not_empty(self, lines: list[str]) -> None:
        """Raise an error if the input lines are empty."""
        if not lines:
            raise ValueError("Expected a RESP array starting with *, but got nothing")

    def _parse_array_header(self, first_line: str) -> int:
        """Extract the number of parts from the *n line (e.g., *3 -> 3)."""
        if not first_line.startswith("*"):
            raise ValueError(
                f"Expected a RESP array starting with *, but got: {first_line}"
            )
        try:
            return int(first_line[1:])
        except ValueError:
            raise ValueError(
                f"Expected a number after * (like *3), but got: {first_line}"
            )

    def _parse_bulk_string_length(self, length_line: str) -> int:
        """Get the length from a $n line (e.g., $3 -> 3)."""
        if not length_line.startswith("$"):
            raise ValueError(f"Expected a length like $3, but got: {length_line}")
        try:
            return int(length_line[1:])
        except ValueError:
            raise ValueError(
                f"Expected a number after $ (like $3), but got: {length_line}"
            )

    def _parse_bulk_string(self, data_line: str, expected_length: int) -> str | None:
        """Extract the string data, checking it matches the expected length."""
        if expected_length == -1:
            return None  # Null bulk string
        if len(data_line) != expected_length:
            raise ValueError(
                f"Expected {expected_length} bytes, but got {len(data_line)} in: {data_line}"
            )
        return data_line
