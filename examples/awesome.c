#include <stdio.h>
#include <stdlib.h>
int main (void) {
char* A;
// A PROGRAM THAT SAYS YOU'RE ARE AWESOME
label_10:
printf("%s\n", "What's your name?");
label_20:
A = malloc(sizeof(char)*(100));
fgets(A, 100, stdin);
label_30:
printf("%s\n", A);
printf("%s\n", "is awesome!");
label_40:
free(A);
return 0;
}
