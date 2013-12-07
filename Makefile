pyjq/compat.o: pyjq/compat.c
	gcc -c pyjq/compat.c -o pyjq/compat.o -fpic -Wall -Werror

pyjq/compat.so: pyjq/compat.o
	gcc --shared pyjq/compat.o -o pyjq/compat.so -ljq

clean:
	rm -f pyjq/compat.o
	rm -f pyjq/compat.so

test: pyjq/compat.so
	py.test pyjq/binding_test.py --verbose --capture=no
