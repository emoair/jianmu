#include <stdio.h>

static int calc(int x) {
    return (x + 1);
}

int main(void) {
    printf("%d\n", calc(5));
    return 0;
}
