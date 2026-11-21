#include "dev.h"

static int spi_open(struct device *dev)
{
	(void)dev;
	return 1;
}

static void spi_close(struct device *dev)
{
	(void)dev;
}

const struct dev_ops spi_ops = {
	.open = spi_open,
	.close = spi_close,
};
