# How should a resumable geospatial downloader handle ignored Range responses safely?

I am building a local Python utility for monitoring public geospatial datasets. It uses conditional HTTP requests and bounded periodic checks rather than repeatedly downloading complete files.

The current workflow is:

1. Check endpoint availability with `HEAD` (with a bounded GET fallback).
2. Send `If-None-Match` and `If-Modified-Since` when a completed version exists.
3. Skip the download on `304 Not Modified`.
4. If a `.part` file exists, request `Range: bytes=<current_size>-` and append only on `206 Partial Content`.
5. Hash the existing partial bytes and the new bytes, and only mark the transfer complete after the response finishes.

The case I am unsure about is a server that ignores `Range` and returns `200 OK` with the entire file. My current implementation discards the new response's offset mode and restarts from byte zero, because appending a full response to the partial file would corrupt it.

```text
partial file exists + 206 -> append from local offset
partial file exists + 200 -> restart from byte zero
partial file exists + 416 -> inspect and restart if necessary
```

Questions:

1. Is restarting from byte zero the safest general behavior when a server ignores Range?
2. Are there HTTP headers or response combinations that would make a `206` response unsafe to append without additional validation?
3. Is it reasonable to rely on `HEAD` plus conditional GET for incremental checks, or are there important limitations for geospatial services?
4. For OGC WFS endpoints, should acquisition be implemented only through bounded, filter-specific queries rather than treating the service URL as a generic downloadable file? I want to avoid unbounded crawling and respect provider constraints.

I am looking for correctness and provider-friendly behavior, not a faster way to download data.
