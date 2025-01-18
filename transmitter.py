import argparse
import logging
import socket

logger = logging.getLogger(__name__)


def server(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_s:
        server_s.bind((args.ip, args.port))
        server_s.listen()
        conn, addr = server_s.accept()
        logger.info(f"Connection from {addr}")
        with conn:
            logger.info(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                logger.info(f"Data: {data!r}")


def client(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_s:
        client_s.connect((args.ip, args.port))
        logger.info(f"COmmunicating with {args.ip}:{args.port}")
        with open(args.filename, "rb") as in_file:
            for chunck in iter(lambda: in_file.read(1024), b''):
                client_s.sendall(chunck)                   
                logger.info(f"Sending data of size {len(chunck)}")


def main():

    logging.basicConfig(filename="transmitter.log", level=logging.INFO)

    parser = argparse.ArgumentParser(prog='trasmitter.py', usage='%(prog)s [options]')
    parser.add_argument('action', choices=['send', 'recv'])
    parser.add_argument('filename', nargs='?', default=None)
    parser.add_argument('ip', nargs='?', default='127.0.0.1')
    parser.add_argument('port', nargs='?', default=8088, type=int)
    args = parser.parse_args()

    if args.action == 'send' and args.filename is None:
        parser.error('send action requires a filename')

    if args.action == 'send':
        client(args)
    elif args.action == 'recv':
        server(args)
    else:
        logger.error(f"oops, invalid action: {args.action}")

if __name__ == '__main__':
    main()
