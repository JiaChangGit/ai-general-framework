#ifndef DEV_H
#define DEV_H

struct device;

struct dev_ops {
	int (*open)(struct device *dev);
	void (*close)(struct device *dev);
};

struct device {
	const char *name;
	const struct dev_ops *ops;
};

int dev_open(struct device *dev);
void dev_close(struct device *dev);

extern const struct dev_ops uart_ops;
extern const struct dev_ops spi_ops;

typedef void (*timer_cb)(void *arg);
struct timer {
	timer_cb cb;
	void *arg;
};
void timer_setup(struct timer *t, timer_cb cb, void *arg);
void timer_fire(struct timer *t);

int fast_submit(struct device *dev);
int slow_submit(struct device *dev);

#endif
