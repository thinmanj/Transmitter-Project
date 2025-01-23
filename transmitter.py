#!/usr/bin/env python
import argparse
import logging
import multiprocessing
import os
import socket

logger = logging.getLogger(__name__)


def _server_out_bound_name(conn):
    filename = conn.recv(1024).decode("utf-8")
    logger.debug(f"Client send: {filename}")
    conn.send("ok".encode("utf-8"))

    return filename


def _server_process_dir(filename):
    if "/" in filename:
        path_parent = os.path.dirname(filename)
        os.makedirs(path_parent, exist_ok=True)
        logger.info(f"Create path: {path_parent}")


def handler_server(conn, addr):
    filename = _server_out_bound_name(conn)
    _server_process_dir(filename)

    try:
        with conn, open(filename, "wb") as out_file:
            logger.info(f"Saving file: {filename}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                out_file.write(data)
                logger.debug(f"Writning: {data!r}")
    except FileNotFoundError:
        logger.exception(f"File {filename} or path not found")
    except OSError:
        logger.exception(f"OS error ocurred while accessing file {filename}")
    except Exception as err:
        logger.exception("Unexpected error happened")


def server(args):
    logger.debug(f"Called with {args!r}")
    process_list = []

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_s:
            server_s.bind((args.ip, args.port))
            logger.info(f"Listening on {args.ip}:{args.port}")
            server_s.listen()
            while True:
                conn, addr = server_s.accept()
                logger.info(f"Connection from {addr}")

                process = multiprocessing.Process(
                    target=handler_server, args=(conn, addr)
                )
                process.start()
                process_list.append(process)

            logger.debug("Exiting server loop")
    except socket.error as err_s:
        logger.exception("Error happened while processing sockets")

    for process in process_list:
        process.join()


def _client_out_bound_name(conn, filename):
    out_bound = f"{filename}"
    client_s.send(out_bound.encode("utf-8"))
    msg = client_s.recv(1024).decode("utf-8")
    logger.debug(f"Server answered: {msg}")


def handler_client(client_s, filename):
    try:
        with open(filename, "rb") as in_file:
            _client_out_bound_name(conn, filename)

            for chunck in iter(lambda: in_file.read(1024), b""):
                client_s.sendall(chunck)
                logger.info(f"Sending data of size {len(chunck)}")
    except FileNotFoundError:
        logger.exception(f"File {filename} not found")
    except OSError:
        logger.exception(f"OS Error happend while trying to access file {filename}")
    except Exception as err_c:
        logger.exception("Unexpected error happened")


def client(args):
    logger.debug(f"Called with {args!r}")
    process_list = []

    if not os.path.isdir(args.filename):
        filenames = [args.filename]
    else:
        filenames = []
        for root, _, files in os.walk(args.filename):
            for name in files:
                filenames.append(os.path.join(root, name))

    for filename in filenames:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_s:
                client_s.connect((args.ip, args.port))
                logger.info(f"Communicating with {args.ip}:{args.port}")

                process = multiprocessing.Process(
                    target=handler_client, args=(client_s, filename)
                )
                process.start()
                process_list.append(process)

        except socket.error as err_c:
            logger.exception("Error heppened while processing sockets")

    for process in process_list:
        process.join()


def log_setup():
    logging.basicConfig(
        filename="transmitter.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)15s.%(funcName)s:%(lineno)s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(name)12s.%(funcName)s:%(lineno)s %(levelname)-8s %(message)s"
    )
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)


def handle_arguments():
    parser = argparse.ArgumentParser(prog="trasmitter.py", usage="%(prog)s [options]")
    parser.add_argument("action", choices=["send", "recv"])
    parser.add_argument("filename", nargs="?", default=None)
    parser.add_argument("ip", nargs="?", default="127.0.0.1")
    parser.add_argument("port", nargs="?", default=8088, type=int)
    args = parser.parse_args()

    if args.action == "send" and args.filename is None:
        parser.error("send action requires a filename")

    return args


def main():

    log_setup()

    args = handle_arguments()

    if args.action == "send":
        client(args)
    elif args.action == "recv":
        server(args)
    else:
        logger.error(f"oops, invalid action: {args.action}")


if __name__ == "__main__":
    main()
