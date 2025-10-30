PYTHON=$(shell which python 2>/dev/null || which python3 2>/dev/null)
PROJECT=aexpect
VERSION=$(shell $(PYTHON) -m setuptools_scm)
COMMIT=$(shell git log --pretty=format:'%H' -n 1)
SHORT_COMMIT=$(shell git log --pretty=format:'%h' -n 1)
COMMIT_DATE=$(shell git log --pretty='format:%cd' --date='format:%Y%m%d' -n 1)
MOCK_CONFIG=default

all:
	@echo "make check - Run lint and tests"
	@echo "make clean - Remove build artifacts"
	@echo "make source - Create source package (commit snapshot)"
	@echo "make source-release - Create source package (versioned tag)"
	@echo "make install - Install from built wheel"
	@echo "make develop - Editable install"
	@echo "make pypi - Build wheel+sdist (ready for upload)"
	@echo
	@echo "Debian targets: build-deb-src, build-deb-bin, build-deb-all"
	@echo "RPM targets: srpm, rpm, srpm-release, rpm-release"

# --- Packaging ---
source: clean
	mkdir -p SOURCES
	git archive --prefix="$(PROJECT)-$(COMMIT)/" -o "SOURCES/$(PROJECT)-$(SHORT_COMMIT).tar.gz" HEAD

source-release: clean
	mkdir -p SOURCES
	git archive --prefix="$(PROJECT)-$(VERSION)/" -o "SOURCES/$(PROJECT)-$(VERSION).tar.gz" $(VERSION)

install:
	rm -r dist 2>/dev/null || true
	$(PYTHON) -m pip install --upgrade pip build wheel
	$(PYTHON) -m build
	$(PYTHON) -m pip install --no-deps --force-reinstall dist/*.whl

develop:
	$(PYTHON) -m pip install --editable .[dev]

pypi: clean
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*
	@echo
	@echo
	@echo "Use 'python3 -m twine upload dist/*'"
	@echo "to upload this release"

# --- Checks ---
check: clean
	inspekt checkall --disable-lint R0917,R0205,R0801,W4901,W0703,W0511 --disable-style E203,E501,E265,W601,E402 --exclude .venv*
	$(PYTHON) -m black --check -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m isort --check-only -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m pytest

test: check

# --- Distro packaging (unchanged except cosmetic) ---
prepare-source:
	dch -D "utopic" -M -v "$(VERSION)" "Automated (make builddeb) build."
	$(PYTHON) -m build --sdist --outdir ../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*

build-deb-src: prepare-source
	dpkg-buildpackage -S -elookkas@gmail.com -rfakeroot

build-deb-bin: prepare-source
	dpkg-buildpackage -b -rfakeroot

build-deb-all: prepare-source
	dpkg-buildpackage -i -I -rfakeroot

srpm: source
	mkdir -p BUILD/SRPM
	mock -r $(MOCK_CONFIG) --resultdir BUILD/SRPM -D "rel_build 0" -D "commit $(COMMIT)" -D "commit_date $(COMMIT_DATE)" --buildsrpm --spec python-$(PROJECT).spec --sources SOURCES

rpm: srpm
	mkdir -p BUILD/RPM
	mock -r $(MOCK_CONFIG) --resultdir BUILD/RPM -D "rel_build 0" -D "commit $(COMMIT)" -D "commit_date $(COMMIT_DATE)" --rebuild BUILD/SRPM/python-$(PROJECT)-$(VERSION)-*.src.rpm

srpm-release: source-release
	mkdir -p BUILD/SRPM
	mock -r $(MOCK_CONFIG) --resultdir BUILD/SRPM -D "rel_build 1" --buildsrpm --spec python-$(PROJECT).spec --sources SOURCES

rpm-release: srpm-release
	mkdir -p BUILD/RPM
	mock -r $(MOCK_CONFIG) --resultdir BUILD/RPM -D "rel_build 1" --rebuild BUILD/SRPM/python-$(PROJECT)-$(VERSION)-*.src.rpm

clean:
	$(MAKE) -f $(CURDIR)/debian/rules clean || true
	rm -rf .mypy_cache *.egg-info MANIFEST BUILD BUILDROOT SPECS RPMS SRPMS SOURCES dist
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

.PHONY: all source source-release install develop pypi check test clean \
	build-deb-src build-deb-bin build-deb-all srpm rpm srpm-release rpm-release prepare-source

