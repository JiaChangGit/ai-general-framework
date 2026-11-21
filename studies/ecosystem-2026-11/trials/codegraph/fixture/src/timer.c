#include "dev.h"

void timer_setup(struct timer *t, timer_cb cb, void *arg)
{
	t->cb = cb;
	t->arg = arg;
}

void timer_fire(struct timer *t)
{
	t->cb(t->arg);
}
