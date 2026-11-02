# How should a resumable geospatial downloader handle an ignored Range request?

I am building a local Python utility for monitoring public geospatial datasets. It uses conditional HTTP requests and bounded periodic checks instead of repeatedly downloading complete files.

When a `.part` file exists, the utility requests `Range: bytes=<current_size>-` and appends only on `206 Partial Content`. It also hashes both the existing partial bytes and the newly downloaded bytes before marking the transfer complete.

The case I am unsure about is a server that ignores `Range` and returns `200 OK` with the entire file. My current implementation restarts from byte zero, because appending that full response to the partial file would corrupt it:

```text
partial file exists + 206 -> append from local offset
partial file exists + 200 -> restart from byte zero
partial file exists + 416 -> inspect and restart if necessary
```

Is restarting from byte zero the safest general behavior when a server ignores Range? Before appending a `206` response, are there response headers or validation steps I should check to ensure that the returned chunk actually belongs at the requested offset?

For OGC WFS endpoints, I plan to use bounded, filter-specific queries rather than treating the service URL as a generic downloadable file, to avoid unbounded crawling and respect provider constraints.

I am looking for correctness and provider-friendly behavior, not a faster way to download data.
