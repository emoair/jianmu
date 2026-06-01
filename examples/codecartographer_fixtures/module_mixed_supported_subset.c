int compute(void) {
  int fuel = 4;
  int x = 1;
  int y = 0;
  while (fuel > 0) {
    if (x < 3) {
      y += x;
    } else {
      y += 1;
    }
    x += 1;
    fuel -= 1;
  }
  return y;
}
