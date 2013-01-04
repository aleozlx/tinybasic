#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main (void) {
char* A;
// A PROGRAM THAT SAYS YOU'RE AWESOME
label_10:
printf("%s\n", "What's your name?");
label_20:
A = malloc(sizeof(char) * 50); 
fgets(A, 50, stdin); 
if (A[strlen(A) - 1] == '\n') { 
A[strlen(A) - 1] = '\0'; 
}
label_30:
printf("%s %s\n", A, "is awesome!");
label_40:
free(A);
return 0;
}
