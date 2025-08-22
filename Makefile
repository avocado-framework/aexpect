PYTHON=$(shell which python 2>/dev/null || which python3 2>/dev/null)
PROJECT=aexpect
VERSION=$(shell $(PYTHON) -m setuptools_scm)
COMMIT=$(shell git log --pretty=format:'%H' -n 1)
SHORT_COMMIT=$(shell git log --pretty=format:'%h' -n 1)
COMMIT_DATE=$(shell git log --pretty='format:%cd' --date='format:%Y%m%d' -n 1)
MOCK_CONFIG=default

all:
	@echo "make check - Runs tree static check, unittests and functional tests. Some tests are only executed when AEXPECT_TIME_SENSITIVE=yes is set."
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make build-deb-src - Generate a source debian package"
	@echo "make build-deb-bin - Generate a binary debian package"
	@echo "make build-deb-all - Generate both source and binary debian packages"
	@echo "RPM related targets:"
	@echo "make srpm: Generate a source RPM package (.srpm)"
	@echo "make rpm: Generate binary RPMs"
	@echo
	@echo "Release related targets:"
	@echo "source-release:     Create source package for the latest tagged release"
	@echo "srpm-release:       Generate a source RPM package (.srpm) for the latest tagged release"
	@echo "rpm-release:        Generate binary RPMs for the latest tagged release"

source: clean
	if test ! -d SOURCES; then mkdir SOURCES; fi
	git archive --prefix="$(PROJECT)-$(COMMIT)/" -o "SOURCES/$(PROJECT)-$(SHORT_COMMIT).tar.gz" HEAD

source-release: clean
	if test ! -d SOURCES; then mkdir SOURCES; fi
	git archive --prefix="$(PROJECT)-$(VERSION)/" -o "SOURCES/$(PROJECT)-$(VERSION).tar.gz" $(VERSION)

install:
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	$(PYTHON) -m pip install dist/*.whl

develop:
	$(PYTHON) -m pip install --editable .[dev]

prepare-source:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	dch -D "utopic" -M -v "$(VERSION)" "Automated (make builddeb) build."
	$(PYTHON) -m build --sdist --outdir ../
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
	if test ! -d BUILD/SRPM; then mkdir -p BUILD/SRPM; fi
	mock -r $(MOCK_CONFIG) --resultdir BUILD/SRPM -D "rel_build 0" -D "commit $(COMMIT)" -D "commit_date $(COMMIT_DATE)" --buildsrpm --spec python-$(PROJECT).spec --sources SOURCES

rpm: srpm
	if test ! -d BUILD/RPM; then mkdir -p BUILD/RPM; fi
	mock -r $(MOCK_CONFIG) --resultdir BUILD/RPM -D "rel_build 0" -D "commit $(COMMIT)" -D "commit_date $(COMMIT_DATE)" --rebuild BUILD/SRPM/python-$(PROJECT)-$(VERSION)-*.src.rpm

srpm-release: source-release
	if test ! -d BUILD/SRPM; then mkdir -p BUILD/SRPM; fi
	mock -r $(MOCK_CONFIG) --resultdir BUILD/SRPM -D "rel_build 1" --buildsrpm --spec python-$(PROJECT).spec --sources SOURCES

rpm-release: srpm-release
	if test ! -d BUILD/RPM; then mkdir -p BUILD/RPM; fi
	mock -r $(MOCK_CONFIG) --resultdir BUILD/RPM -D "rel_build 1" --rebuild BUILD/SRPM/python-$(PROJECT)-$(VERSION)-*.src.rpm

check: clean
	inspekt checkall --disable-lint R0917,R0205,R0801,W4901,W0703,W0511 --disable-style E203,E501,E265,W601,E402 --exclude .venv*
	$(PYTHON) -m black --check -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m isort --check-only -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m pytest

clean:
	$(MAKE) -f $(CURDIR)/debian/rules clean || true
	rm -rf .venv* .mypy_cache *.egg-info MANIFEST BUILD BUILDROOT SPECS RPMS SRPMS SOURCES dist
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

pypi: clean
	$(PYTHON) -m build
	@echo
	@echo
	@echo "Use 'python3 -m twine upload dist/*'"
	@echo "to upload this release"


.PHONY: source install clean

