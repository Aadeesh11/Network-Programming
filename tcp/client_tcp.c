#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <strings.h>
#include <unistd.h>
void error(char *msg)
{
    perror(msg);
    exit(0);
}

int main(int argc, char *argv[])
{
    int sockfd, port, n;
    struct sockaddr_in serv_addr;
    struct hostent *server;

    char buffer[256];
    port = atoi(argv[2]);
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    server = gethostbyname(argv[1]);

    if (server == NULL)
    {
        error("No");
    }

    bzero((char *)&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;

    bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);

    serv_addr.sin_port = htons(port);

    if (connect(sockfd, &serv_addr, sizeof(serv_addr)) < 0)
    {
        error("NPPP");
    }

    printf("msg daalo: ");
    bzero(buffer, 256);

    fgets(buffer, 255, stdin);
    n = write(sockfd, buffer, strlen(buffer));

    if (n < 0)
    {
        error("buff");
    }

    bzero(buffer, 256);
    n = read(sockfd, buffer, 255);
    if (n < 0)
    {
        error("readd");
    }

    printf("msg: %s", buffer);

    return 0;
}