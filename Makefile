PYTHON ?= python3
VERSION := 1.0.0
SOURCE_DATE_EPOCH ?= 0
DIST_DIR := $(CURDIR)/dist
SOURCE_ARCHIVE := $(DIST_DIR)/tbl221-monitor-$(VERSION).tar.gz
CONTAINER_ENGINE ?= podman
TEST_IMAGE ?= tbl221-monitor-test:$(VERSION)

.PHONY: all build test wheels source package package-deb package-rpm container-build container-test clean help

all: build

help:
	@printf '%s\n' \
	  'make build        Compile-check both applications' \
	  'make test         Run unit tests and compile checks' \
	  'make wheels       Build Python wheel/sdist artifacts (requires build)' \
	  'make source       Create the RPM source archive' \
	  'make package-deb  Build Debian binary packages' \
	  'make package-rpm  Build RPM binary packages' \
	  'make package      Build both DEB and RPM packages' \
	  'make container-build  Build the OCI test image' \
	  'make container-test   Build and run the OCI test image' \
	  'make clean        Remove generated artifacts'

build:
	$(PYTHON) -m compileall -q tbl221-record tbl221-graphui packaging/debian/build.py packaging/container/gui_smoke.py

test: build
	$(PYTHON) -m unittest discover -s tbl221-record/tests -v

wheels:
	$(PYTHON) -m build --outdir $(DIST_DIR)/python tbl221-record
	$(PYTHON) -m build --outdir $(DIST_DIR)/python tbl221-graphui

source:
	mkdir -p $(DIST_DIR)
	tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='@$(SOURCE_DATE_EPOCH)' \
	  --exclude=.git --exclude=dist --exclude='*/__pycache__' --exclude='*.pyc' \
	  --transform='s,^,tbl221-monitor-$(VERSION)/,' -czf $(SOURCE_ARCHIVE) .

package: package-deb package-rpm

package-deb: build
	$(PYTHON) packaging/debian/build.py

package-rpm: build source
	mkdir -p $(DIST_DIR)/rpm $(DIST_DIR)/srpm $(DIST_DIR)/rpmbuild/BUILD $(DIST_DIR)/rpmbuild/BUILDROOT $(DIST_DIR)/rpmbuild/tmp
	rpmbuild -bb packaging/rpm/tbl221.spec \
	  --define '_topdir $(DIST_DIR)/rpmbuild' \
	  --define '_tmppath $(DIST_DIR)/rpmbuild/tmp' \
	  --define '_sourcedir $(DIST_DIR)' \
	  --define '_rpmdir $(DIST_DIR)/rpm' \
	  --define '_srcrpmdir $(DIST_DIR)/srpm'

container-build:
	$(CONTAINER_ENGINE) build --file Containerfile --tag $(TEST_IMAGE) .

container-test: container-build
	$(CONTAINER_ENGINE) run --rm $(TEST_IMAGE)

clean:
	rm -rf dist
	find tbl221-record tbl221-graphui packaging -type d -name __pycache__ -prune -exec rm -rf '{}' +
	find tbl221-record tbl221-graphui packaging -type f -name '*.py[co]' -delete
	rm -rf tbl221-record/build tbl221-graphui/build
	rm -rf tbl221-record/*.egg-info tbl221-graphui/*.egg-info
