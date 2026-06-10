#include <stdio.h>

static int sum3(int a[]) {
    int s = 0;
    for (int i = 0; i < 3; i++) {
        s = (s + a[i]);
    }
    return s;
}

int main(void) {
    int a[3] = {24, 1, 1};
    printf("%d\n", sum3(a));
    return 0;
}
