# UPnpLOAD - Dead simple file upload through UPnP routers

Your local files, world accessible from a simple URL.

- Give a file, get a URL.
- Limit number of downloads per-file.
- No storage backend needed.

All you need is your router/wifi UPnP capable (most are), and
of course, it must be enabled.

## Usage

    $ upnpload hello.txt world.txt                                                                                                 [9:51:37]
    http://189.63.158.15:18182/hello.txt
    http://189.63.158.15:18182/world.txt

Each file can be downloaded only once. Use _-n_ to increase this value.

The same as before, but with some nice messages.

    ---> searching for UPnP router/wifi... http://192.168.1.1:1780/control?WANIPConnection (IP_Routed)
    ---> serving files:
    http://189.63.158.15:63457/hello.txt
    http://189.63.158.15:63457/world.txt
    ---> GET /hello.txt from 67.207.152.111:52402
    67.217.155.121 - - [08/Oct/2012 10:02:58] "GET /hello.txt HTTP/1.1" 200 -
    ---> file hello.txt served, 0 left
    ---> GET /world.txt from 67.207.152.111:52403
    67.217.155.121 - - [08/Oct/2012 10:03:22] "GET /world.txt HTTP/1.1" 200 -
    ---> file world.txt served, 0 left
    ---> all files upload

### Installation

    $ sudo wget https://raw.github.com/caruccio/upnpload/master/upnpload -O /usr/local/bin/upnpload

### RTFM
    $ upnpload -h                                                                                                                  [9:54:24]
    usage: upnpload [-h] [-e PORT] [-i PORT] [-p PORT] [-n COUNT]
                       [-c CONTENT-TYPE] [-l] [-v]
                       [FILE [FILE ...]]
    
    Dead simple file upload through UPnP routers
    
    positional arguments:
      FILE                  File(s) to serve
    
    optional arguments:
      -h, --help            show this help message and exit
      -e PORT, --ext-port PORT
                            External port to listen for incoming connection
      -i PORT, --int-port PORT
                            Internal port to listen for incoming connection
      -p PORT, --port PORT  Both ports to listen for incoming connection
      -n COUNT              How many times to serve each file
      -c CONTENT-TYPE       Force content-type
      -l                    List active mappings and exit
      -v                    Print stuff

## Notes ##

Of course, this method has some security issues.

Based on idea from [geturl](https://github.com/uams/geturl).
