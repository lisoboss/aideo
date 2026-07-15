ENV ?= local
ENV_FILE := .$(ENV).env

DIRS := $(patsubst %/,%,$(wildcard */))
VERBOSE_MODE := $(addsuffix @verbose,$(DIRS))

.PHONY: all $(DIRS) $(VERBOSE_MODE)

all: $(DIRS)

$(DIRS):
	hurl --variables-file $(ENV_FILE) ./$@/*.hurl --test

$(VERBOSE_MODE): %@verbose:
	hurl --variables-file $(ENV_FILE) ./$*/*.hurl -v
