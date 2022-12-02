#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

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
    int sockfd, newSockfd, port, clilen;
    char buffer[256];
    struct sockaddr_in serv_addr, cli_addr;
    int n;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
        error("bye");

    bzero((char *)&serv_addr, sizeof(serv_addr));

    port = atoi(argv[1]);

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(port);

    if (bind(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
        error("bye1");
    }

    listen(sockfd, 2);
    clilen = sizeof(cli_addr);

    while (1)
    {
        newSockfd = accept(sockfd, (struct sockaddr *)&cli_addr, &clilen);
        if (newSockfd < 0)
        {
            error("bye3");
        }
        bzero(buffer, 256);
        n = read(newSockfd, buffer, 255);

        if (n < 0)
        {
            error("bye4");
        }
        printf("msg : %s\n", buffer);
        str_upper(buffer);
        n = write(newSockfd, buffer, 255);

        if (n < 0)
        {
            error("bye5");
        }
    }
    return 0;
}