# Conditional for release vs. snapshot builds. Set to 1 for release build.
%if ! 0%{?rel_build:1}
    %global rel_build 1
%endif

# Settings used for build from snapshots.
%if 0%{?rel_build}
%global gittar		aexpect-%{version}.tar.gz
%else
%if ! 0%{?commit:1}
%global commit		3c1d7eeec3ea607d1ac51dbf538e9e98b4731afe
%endif
%if ! 0%{?commit_date:1}
%global commit_date	20211208
%endif
%global shortcommit	%(c=%{commit};echo ${c:0:7})
%global gitrel		.%{commit_date}git%{shortcommit}
%global gittar		aexpect-%{shortcommit}.tar.gz
%endif

# Selftests are provided but skipped because they use unsupported tooling.
%global with_tests 0

Name: python-aexpect
Version: 1.6.4
Release: 1%{?gitrel}%{?dist}
Summary: Aexpect is a python library to control interactive applications

License: GPLv2+
URL: https://github.com/avocado-framework/aexpect

%if 0%{?rel_build}
Source0: %{url}/archive/%{version}/%{gittar}
%else
Source0: %{url}/archive/%{commit}/%{gittar}
%endif

BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools

%description
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%package -n python3-aexpect
Summary: %{summary}

%description -n python3-aexpect
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%prep
%if 0%{?rel_build}
%autosetup -n aexpect-%{version} -p 1
%else
%autosetup -n aexpect-%{commit} -p 1
%endif

%build
%py3_build

%install
%py3_install
ln -s aexpect_helper %{buildroot}%{_bindir}/aexpect_helper-%{python3_pkgversion}
ln -s aexpect_helper %{buildroot}%{_bindir}/aexpect_helper-%{python3_version}

%if %{with_tests}
%check
selftests/checkall
%endif

%files -n python3-aexpect
%license LICENSE
%doc README.rst
%{python3_sitelib}/aexpect/
%{python3_sitelib}/aexpect-%{version}-py%{python3_version}.egg-info/
%{_bindir}/aexpect_helper*

%changelog
* Wed Dec  8 2021 Cleber Rosa <crosa@redhat.com> - 1.6.4-1
- New release

* Tue Nov 23 2021 Cleber Rosa <cleber@redhat.com> - 1.6.3-1
- New release

* Mon Jun 28 2021 Merlin Mathesius <mmathesi@redhat.com> - 1.6.2-2
- Spec file cleanup resulting from downstream package review.

* Wed Jun  2 2021 Cleber Rosa <cleber@redhat.com> - 1.6.2-1
- New release

* Mon Nov 2 2020 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.6.1-1
- Plamen Dimitrov
- Remove pylint issues due to improperly initialized exception attribute
- Fix reraising from previous exceptions
- Use python 3 style super() call
- Fix the order of remote keyword arguments
- Detect and deserialize exceptions from a module if provided
- Disable aexpect importing on the remote side if not available
- Use known (local) methods to obtain a session in a door usage example
- Convert the remote door unit tests to functional tests
- Samir Aguiar
- Add support for invoking remote functions and objects on Windows
- Add support for indented functions
- Return serialized remote function or utility arguments
- Xiaodai Wang:
- Migrate ssh options and handle_prompts changes from avocado-vt to aexpect

* Tue Sep 22 2020 Cleber Rosa <cleber@redhat.com> - 1.6.0-1
- New release

* Tue Sep 22 2020 Cleber Rosa <cleber@redhat.com> - 1.5.1-2
- Drop Python 2 support and packages

* Wed Nov 20 2019 Cleber Rosa <cleber@redhat.com> - 1.5.1-1
- Made python2 build conditional
- Enabled RHEL 8 build with Python 3 only

* Wed Jun 13 2018 Cleber Rosa <cleber@redhat.com> - 1.5.1-0
- Upgrade to upstream version 1.5.1

* Mon Jun 4 2018 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.5.0-1
- Upgrade to upstream version 1.5.0

* Wed Mar 14 2018 Cleber Rosa <cleber@redhat.com> - 1.4.0-2
- Changed URL to aexpect repo
- Changed build to use a git archived based source
- Added released version builds
- Remove compatibility with older package name
- Reordered tags
- Added conditional for check target
- Only require python-setuptools on RHEL
- Added rules for also building Python 3 packages

* Mon Apr 3 2017 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.4.0-1
- Upgrade to upstream version 1.4.0

* Wed Mar  8 2017 Cleber Rosa <cleber@redhat.com> - 1.3.1-1
- Rename package to python-aexpect

* Mon Feb 20 2017 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.3.1-0
- Update to upstream version 1.3.1
- Fix encoding related bug.

* Thu Jan 12 2017 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.3.0-2
- Fix dependency on python-setuptools.

* Thu Jan 12 2017 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.3.0-1
- Update to upstream version 1.3.0.

* Tue Jun 7 2016 Lucas Meneghel Rodrigues <lookkas@gmail.com> - 1.2.0-1
- Update to upstream version 1.2.0.

* Thu Sep 17 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.1.0-1
- Update to upstream version 1.1.0.

* Fri Jul 31 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.1-2
- Fix spec bug

* Fri Jul 31 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.1-1
- First COPR build

* Thu Apr 23 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.0-1
- First RPM
