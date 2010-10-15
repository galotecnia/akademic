#!/bin/sh

F1=$1
F2=$2

filtra() {
    cat $1 | \
    tr -d '\n' | \
    sed '
        s/}, {/},\n{/g;
        s/\[{/[\n{/g;
        s/ *"pk": *\([^,]*\), *"model": "\([^"]*\)", *"fields"/ \2.\1/g;
    ' | \
    sort 
}


echo PROCESANDO $F1
filtra $F1 > $F1.$$.sort

echo PROCESANDO $F2
filtra $F2 > $F2.$$.sort

echo COMPARANDO
diff -U0 "$F1.$$.sort" "$F2.$$.sort"  |  sed 's/^@@.*//;' | less -S

echo BORRANDO
rm -f $F1.$$.sort $F2.$$.sort
