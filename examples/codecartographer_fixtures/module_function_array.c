int helper(int a) {
  return a + 1;
}

int compute(void) {
  int values[3];
  values[0] = helper(2);
  values[1] = 4;
  return values[0] + values[1];
}
