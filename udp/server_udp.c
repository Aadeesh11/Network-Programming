#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <ctype.h>
void error(char *msg)
{
    perror(msg);
    exit(0);
}

void str_upper(char *str)
{
    do
    {
        *str = toupper((unsigned char)*str);
    } while (*str++);
}

int main(int argc, char *argv[])
{
    int sock, length, fromlen, n;
    struct sockaddr_in server;
    struct sockaddr_in from;
    char buf[1024];

    if (argc < 2)
    {
        fprintf(stderr, "no port pr");
        exit(0);
    }

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0)
    {
        error("opening socket");
    }

    length = sizeof(server);
    bzero(&server, length);
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons(atoi(argv[1]));
    if (bind(sock, (struct sockaddr *)&server, length) < 0)
    {
        error("bind");
    }
    fromlen = sizeof(struct sockaddr_in);

    while (1)
    {
        n = recvfrom(sock, buf, 1024, 0, (struct sockaddr *)&from, &fromlen);
        if (n < 0)
        {
            error("recv");
        }
        fwrite(buf, n, 1, stdout);
        str_upper(buf);
        n = sendto(sock, buf, n, 0, (struct sockaddr *)&from, fromlen);
        if (n < 0)
        {
            error("send to");
        }
    }
}