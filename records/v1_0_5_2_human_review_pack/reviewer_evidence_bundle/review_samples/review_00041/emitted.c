#include <stdio.h>

static int calc(int x) {
    return (x + 1);
}

int main(void) {
    printf("%d\n", calc(33));
    return 0;
}
