#include "dev.h"

#define DEFINE_HANDLER(name)                         \
	int handle_##name(struct device *dev)        \
	{                                            \
		return dev_open(dev);                \
	}

DEFINE_HANDLER(uart)
DEFINE_HANDLER(spi)

static void heartbeat(void *arg)
{
	dev_close(arg);
}

#ifdef CONFIG_FAST_PATH
static int submit(struct device *dev)
{
	return fast_submit(dev);
}
#else
static int submit(struct device *dev)
{
	return slow_submit(dev);
}
#endif

int main(void)
{
	struct device uart = { "uart0", &uart_ops };
	struct device spi = { "spi0", &spi_ops };
	struct timer t;

	handle_uart(&uart);
	handle_spi(&spi);
	timer_setup(&t, heartbeat, &uart);
	timer_fire(&t);
	return submit(&uart);
}
