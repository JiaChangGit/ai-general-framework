CFLAGS ?= -Wall -Wextra -Iinclude
SRC = src/main.c src/dev.c src/uart.c src/spi.c src/timer.c src/submit.c
demo: $(SRC) include/dev.h
	$(CC) $(CFLAGS) -o $@ $(SRC)
