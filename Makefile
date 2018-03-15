PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/aexpect
PROJECT=aexpect
VERSION="1.4.0"

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make build-deb-src - Generate a source debian package"
	@echo "make build-deb-bin - Generate a binary debian package"
	@echo "make build-deb-all - Generate both source and binary debian packages"
	@echo "make build-rpm-src - Generate a source RPM package (.srpm)"
	@echo "make build-rpm-all - Generate both source and binary RPMs"
	@echo "make check - Runs tree static check, unittests and functional tests"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=SOURCES

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

build-rpm-src: source
	rpmbuild --define '_topdir %{getenv:PWD}' \
		 -bs python-aexpect.spec

build-rpm-all: source
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

