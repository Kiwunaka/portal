#include <netdb.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 5 && argc != 6) {
        return 2;
    }
    const char *host = argv[1];
    const char *port = argv[2];
    long payload_size = strtol(argv[3], NULL, 10);
    long send_count = strtol(argv[4], NULL, 10);
    if (payload_size < 1 || payload_size > 256 || send_count < 1 || send_count > 20) {
        return 2;
    }
    int require_echo = argc == 6 && strcmp(argv[5], "roundtrip") == 0;
    if (argc == 6 && !require_echo) {
        return 2;
    }

    struct addrinfo hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_DGRAM;
    struct addrinfo *result = NULL;
    if (getaddrinfo(host, port, &hints, &result) != 0 || result == NULL) {
        return 3;
    }

    int fd = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
    if (fd < 0) {
        freeaddrinfo(result);
        return 4;
    }
    unsigned char payload[256];
    memset(payload, 0x50, (size_t)payload_size);
    if (require_echo) {
        struct timeval timeout;
        timeout.tv_sec = 5;
        timeout.tv_usec = 0;
        if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) != 0) {
            close(fd);
            freeaddrinfo(result);
            return 6;
        }
    }
    for (long index = 0; index < send_count; ++index) {
        ssize_t written = sendto(
            fd,
            payload,
            (size_t)payload_size,
            0,
            result->ai_addr,
            result->ai_addrlen
        );
        if (written != payload_size) {
            close(fd);
            freeaddrinfo(result);
            return 5;
        }
        usleep(100000);
    }
    if (require_echo) {
        unsigned char response[256];
        ssize_t received = recvfrom(fd, response, sizeof(response), 0, NULL, NULL);
        if (received != payload_size || memcmp(response, payload, (size_t)payload_size) != 0) {
            close(fd);
            freeaddrinfo(result);
            return 7;
        }
    }
    close(fd);
    freeaddrinfo(result);
    return 0;
}
