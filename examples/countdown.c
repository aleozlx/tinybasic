#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main (void) {
int A;
// A PROGRAM THAT COUNTS DOWN FROM 10 TO 0
label_10:
A = 10;
label_20:
if (A<0) {
goto label_60;
}
label_30:
printf("%d\n", A);
label_40:
A = A-1;
label_50:
goto label_20;
label_60:
printf("%s\n", "BLAST OFF!");
label_70:
return 0;
}
