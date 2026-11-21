#include "dev.h"

int dev_open(struct device *dev)
{
	return dev->ops->open(dev);
}

void dev_close(struct device *dev)
{
	dev->ops->close(dev);
}
