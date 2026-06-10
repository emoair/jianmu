#include <stdio.h>

int main(void) {
    int a[4] = {9, 1, 1, 1};
    int s = 0;
    for (int i = 0; i < 4; i++) {
        s = (s + a[i]);
    }
    printf("%d\n", s);
    return 0;
}
