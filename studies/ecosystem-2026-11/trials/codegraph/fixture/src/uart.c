#include "dev.h"

static void uart_reset(struct device *dev)
{
	(void)dev;
}

static int uart_open(struct device *dev)
{
	uart_reset(dev);
	return 0;
}

static void uart_close(struct device *dev)
{
	uart_reset(dev);
}

const struct dev_ops uart_ops = {
	.open = uart_open,
	.close = uart_close,
};
