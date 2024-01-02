import os, queue, threading, argparse#, hashlib
import requests as req

BUF_SIZE = 65536
retries = 0
class UpdateEntry:
    def __init__(self, filename: str, version: str, size: int, sha1: str, url: str):
        self.filename = filename
        self.version = version
        self.size = size
        self.sha1 = sha1
        self.url = url

def parse(rawXML: str) -> list[UpdateEntry]:
    def splitter(splitby: str) -> list[str]:
        return [s.split("\"")[0] for s in rawXML.split(f"{splitby}=\"")[1:]]
    entrylist = [UpdateEntry(filename, version, int(size), sha1, url)\
                for filename, version, size, sha1, url in zip(\
                [x.split("/")[-1] for x in splitter("url")],\
                splitter("version"),\
                splitter("size"),\
                splitter("sha1sum"),\
                splitter("url")
                )]
    verboseprint(f"Collected {len(entrylist)} entries")
    return entrylist

def run(id):
    CDNBASE = "https://a0.ww.np.dl.playstation.net/tpl/np"
    os.makedirs(f"{rootfolder}/{id}", exist_ok=True)
    response = req.get(f"{CDNBASE}/{id}/{id}-ver.xml", verify = False)
    if response.status_code == 404:
        print("That id does not exist")
        return

    verboseprint(f"Hit for {response.url}")
    updatelist = parse(response.text)
    threaddownload(id, updatelist)
    print("All files downloaded and verified")

def threaddownload(id: str, updatelist: list[UpdateEntry]) -> None:
    noverboseprint("Downloading")
    entries = queue.Queue()
    [entries.put(x) for x in updatelist]

    def thread():
        while True:
            entry: UpdateEntry = entries.get()
            if not entry:
                entries.task_done()
                return
            filename = f"{rootfolder}/{id}/{entry.filename}"
            if os.path.isfile(filename):
                verboseprint(f"{entry.filename} already exists, overwriting...")
                os.remove(filename)
            verboseprint(f"Retrieving v{entry.version} from {entry.url}")
            with req.get(entry.url, stream = True) as r:
                r.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size = chunk_size):
                        f.write(chunk)
            entries.task_done()
            noverboseprint(".", end = "")
    
    for i in range(threads):
        threading.Thread(target=thread, daemon=True).start()
        entries.put(None)

    entries.join()
    verify(id, updatelist)

def verify(id: str, entries: list[UpdateEntry]) -> None:
    print("Verifying files")
    q = queue.Queue()
    [q.put(entry) for entry in entries]
    retrylist = []
    while not q.empty():
        entry: UpdateEntry = q.get()
        verboseprint(f"Verifying {entry.filename}")
        filename = f"{rootfolder}/{id}/{entry.filename}"
        # sha1 = hashlib.sha1()
        # with open(filename, "rb") as f:
        #     while True:
        #         data = f.read(BUF_SIZE)
        #         if not data:
        #             break
        #         sha1.update(data)
        # if entry.sha1 != sha1.hexdigest() or entry.size != os.path.getsize(filename):
        if entry.size != os.path.getsize(filename):
            verboseprint(f"{entry.filename} failed, downloaded: {os.path.getsize(filename)}, recorded: {entry.size}, adding to retrylist")
            retrylist.append(entry)
        noverboseprint(".", end = "")
    if retrylist:
        retry()
        threaddownload(id, retrylist)

def retry() -> None:
    global retries
    print("Retrying...")
    retries += 1
    if retries > retrylimit:
        print("Maximum retries exceeded, please try again")
        exit(1)
    verboseprint(f"Retry count is at {retries}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help = True, description = "Downloads all available patches of the PS3 game ID")
    parser.add_argument("gameID")
    # parser.add_argument("-b", "--buf-size", help = "Buffer size for SHA1", default = 65536, type = int)
    parser.add_argument("-o", "--output", help = "Output folder", default = "ps3updates")
    parser.add_argument("-c", "--chunk-size", help = "Download chunk size", default = 8192, type = int)
    parser.add_argument("-t", "--threads", help = "Downloader threads", default = 20, type = int)
    parser.add_argument("-r", "--retry", help = "Retry attemps", default = 3, type = int)
    parser.add_argument("-v", "--verbose", action = "store_true", help = "Enable verbose logging")
    args = parser.parse_args()
    threads = args.threads
    retrylimit = args.retry
    rootfolder = args.output
    chunk_size = args.chunk_size
    verboseprint = print if args.verbose else lambda *a, **k: None
    noverboseprint = print if not args.verbose else lambda *a, **k: None
    run(args.gameID)