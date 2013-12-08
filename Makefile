CC = gcc -fpic -Wall -Werror -I.

pyjq/compat.o: pyjq/compat.c
	$(CC) -c pyjq/compat.c -o pyjq/compat.o

pyjq/vpool.o: pyjq/vpool.c
	$(CC) -c pyjq/vpool.c -o pyjq/vpool.o

pyjq/compat.so: pyjq/compat.o pyjq/vpool.o
	gcc --shared pyjq/compat.o pyjq/vpool.o -o pyjq/compat.so -ljq

clean:
	rm -f pyjq/compat.o
	rm -f pyjq/compat.so

test: pyjq/compat.so
	py.test pyjq/ --verbose --capture=no --tb=native
