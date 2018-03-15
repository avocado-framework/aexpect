PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/aexpect
PROJECT=aexpect
VERSION="1.4.0"
COMMIT=$(shell git log --pretty=format:'%H' -n 1)
SHORT_COMMIT=$(shell git log --pretty=format:'%h' -n 1)

all:
	@echo "make check - Runs tree static check, unittests and functional tests"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make build-deb-src - Generate a source debian package"
	@echo "make build-deb-bin - Generate a binary debian package"
	@echo "make build-deb-all - Generate both source and binary debian packages"
	@echo "RPM related targets:"
	@echo "make srpm: Generate a source RPM package (.srpm)"
	@echo "make rpm: Generate binary RPMs"

source: clean
	if test ! -d SOURCES; then mkdir SOURCES; fi
	git archive --prefix="aexpect-$(COMMIT)/" -o "SOURCES/aexpect-$(SHORT_COMMIT).tar.gz" HEAD

source-release: clean
	if test ! -d SOURCES; then mkdir SOURCES; fi
	git archive --prefix="aexpect-$(VERSION)/" -o "SOURCES/aexpect-$(VERSION).tar.gz" $(VERSION)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

prepare-source:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	dch -D "utopic" -M -v "$(VERSION)" "Automated (make builddeb) build."
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*

build-deb-src: prepare-source
	# build the source package
	dpkg-buildpackage -S -elookkas@gmail.com -rfakeroot

build-deb-bin: prepare-source
	# build binary package
	dpkg-buildpackage -b -rfakeroot

build-deb-all: prepare-source
	# build both source and binary packages
	dpkg-buildpackage -i -I -rfakeroot

srpm: source
	rpmbuild --define '_topdir %{getenv:PWD}' \
		 -bs python-aexpect.spec

rpm: source
	rpmbuild --define '_topdir %{getenv:PWD}' \
		 -ba python-aexpect.spec

check:
	inspekt checkall

clean:
	$(PYTHON) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean || true
	rm -rf build/ MANIFEST BUILD BUILDROOT SPECS RPMS SRPMS SOURCES
	find . -name '*.pyc' -delete

.PHONY: source install clean

