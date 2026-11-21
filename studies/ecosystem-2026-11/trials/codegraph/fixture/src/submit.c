#include "dev.h"

int fast_submit(struct device *dev)
{
	(void)dev;
	return 2;
}

int slow_submit(struct device *dev)
{
	(void)dev;
	return 3;
}
