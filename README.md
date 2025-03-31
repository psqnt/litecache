# litecache

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
pip install litecache2
```

or

```
pip install git+https://github.com/psqnt/litecache.git
```

## Usage
-----

### Basic Example
```
$ litecache --host localhost --port 6399
```


(development)
```bash
$ uv run litecache
```

using docker:
```
$ docker build -t litecache:latest .
$ docker run litecache:latest
```

## Configuration
---------------

litecache can be configured using the following cli parameters:

```
--host
--port
```

## Testing
-------

To run the tests, use the following command:
```bash
uv run pytest
```

## Redis-cli and Redis Benchmark

redis-cli
```
➜  ~ redis-cli SET foo bar
OK
➜  ~ redis-cli GET foo
"bar"
```

redis-benchmark
```
➜  ~ redis-benchmark -t set,get,del -n 100000 -c 50 -q

SET: 32509.75 requests per second, p50=1.343 msec
GET: 36258.16 requests per second, p50=1.191 msec
```

