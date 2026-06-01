int compute(void) {
  int x = 2;
  int y = 0;
  for (int i = 0; i < 5; i += 1) {
    if (x > 1) {
      y += x;
    }
  }
  return y;
}
