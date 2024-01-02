# fluffy-umbrella
Simple multi-threaded python script to download all game updates from PS CDN

```
usage: ps3updater.py [-h] [-o OUTPUT] [-c CHUNK_SIZE] [-t THREADS] [-r RETRY] [-v] gameID

Downloads all available patches of the PS3 game ID

positional arguments:
  gameID

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output folder
  -c CHUNK_SIZE, --chunk-size CHUNK_SIZE
                        Download chunk size
  -t THREADS, --threads THREADS
                        Downloader threads
  -r RETRY, --retry RETRY
                        Retry attemps
  -v, --verbose         Enable verbose logging
```