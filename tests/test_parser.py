from litecache.parser import RespParser  # Import from src/litecache


def test_parse_valid_set_command():
    """Test parsing a valid SET command."""
    parser = RespParser()
    data = b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    result = parser.parse(data)
    assert result == ["SET", "foo", "bar"]


def test_parse_empty_input():
    """Test handling empty input."""
    parser = RespParser()
    result = parser.parse(b"")
    assert result == []


def test_parse_invalid_array_header():
    """Test rejecting input that doesn’t start with *."""
    parser = RespParser()
    data = b"$3\r\nfoo\r\n"
    try:
        parser.parse(data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Expected a RESP array starting with *, but got: $3"


def test_serialize_simple_string():
    """Test serializing a simple string starting with +."""
    parser = RespParser()
    result = parser.serialize("+OK")
    assert result == b"+OK\r\n"


def test_serialize_error():
    """Test serializing an error starting with -."""
    parser = RespParser()
    result = parser.serialize("-ERR something went wrong")
    assert result == b"-ERR something went wrong\r\n"


def test_serialize_null_bulk_string():
    """Test serializing None as a null bulk string."""
    parser = RespParser()
    result = parser.serialize(None)
    assert result == b"$-1\r\n"


def test_serialize_bulk_string():
    """Test serializing a regular string as a bulk string."""
    parser = RespParser()
    result = parser.serialize("hello")
    assert result == b"$5\r\nhello\r\n"


def test_serialize_integer():
    """Test serializing an integer."""
    parser = RespParser()
    result = parser.serialize(42)
    assert result == b":42\r\n"


def test_serialize_invalid_type():
    """Test that an unsupported type raises an error."""
    parser = RespParser()
    try:
        parser.serialize([1, 2, 3])  # List isn’t supported
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Unsupported data type for serialization: <class 'list'>"
