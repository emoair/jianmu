#include <stdio.h>

int fact(int n) {
  if (n <= 1) {
    return 1;
  }
  return n * fact(n - 1);
}

int compute(void) {
  int *p = 0;
  printf("%d", fact(3));
  return p == 0;
}
