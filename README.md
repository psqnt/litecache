# litecache
===========================================================

## Introduction
---------------

litecache is a basic in-memory key-value store written in Python supporting a subset of RESP (redis serialization language)

## Features
------------

* **Key-Value Cache**: Store and retrieve data using a simple key-value pair system
* **RESP**: support a subset of resp so should work with any redis client (SET,GET,DEL)
* **Simple**: small code base and fairly readable so should be easy to understand and make updates to

## Installation
---------------

To install litecache, run the following command:
```bash
pip install litecache
```

## Usage
-----

### Basic Example

```bash
uv run litecache
```
## Configuration
---------------

litecache can be configured using the following environment variables:

*TODO*

## Testing
-------

To run the tests, use the following command:
```bash
uv run pytest
```

