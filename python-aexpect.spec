%global srcname aexpect

# Conditional for release vs. snapshot builds. Set to 1 for release build.
%if ! 0%{?rel_build:1}
    %global rel_build 1
%endif

# Settings used for build from snapshots.
%if 0%{?rel_build}
%global gittar		%{srcname}-%{version}.tar.gz
%else
%if ! 0%{?commit:1}
%global commit		7597f77853fc668d640b3652a25aa57a515742fa
%endif
%if ! 0%{?commit_date:1}
%global commit_date	20180202
%endif
%global shortcommit	%(c=%{commit};echo ${c:0:7})
%global gitrel		.%{commit_date}git%{shortcommit}
%global gittar		%{srcname}-%{shortcommit}.tar.gz
%endif

# Selftests are provided but skipped because they use unsupported tooling.
%global with_tests 0

%if 0%{?rhel}
%global with_python3 0
%else
%global with_python3 1
%endif

Name: python-%{srcname}
Version: 1.4.0
Release: 2%{?gitrel}%{?dist}
Summary: Aexpect is a python library to control interactive applications
Group: Development/Tools

License: GPLv2
URL: https://github.com/avocado-framework/aexpect

%if 0%{?rel_build}
Source0: https://github.com/avocado-framework/%{srcname}/archive/%{version}.tar.gz#/%{gittar}
%else
Source0: https://github.com/avocado-framework/%{srcname}/archive/%{commit}.tar.gz#/%{gittar}
%endif

BuildArch: noarch
Requires: python
BuildRequires: python2-devel

%if %{with_python3}
Requires: python3
BuildRequires: python3-devel
%endif

%if 0%{?rhel}
BuildRequires: python-setuptools
%endif

%description
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%package -n python2-%{srcname}
Summary: %{summary}
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%if %{with_python3}
%package -n python%{python3_pkgversion}-%{srcname}
Summary: %{summary}
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}

%description -n python%{python3_pkgversion}-%{srcname}
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.
PYTHON 3 SUPPORT IS CURRENTLY EXPERIMENTAL
%endif

%prep
%if 0%{?rel_build}
%autosetup -n %{srcname}-%{version}
%else
%autosetup -n %{srcname}-%{commit}
%endif

%build
%py2_build

%if %{with_python3}
%py3_build
%endif

%install
%py2_install
# move and symlink python2 version-specific executables
mv %{buildroot}%{_bindir}/aexpect-helper %{buildroot}%{_bindir}/aexpect-helper-%{python2_version}
ln -s aexpect-helper-%{python2_version} %{buildroot}%{_bindir}/aexpect-helper-2

%if %{with_python3}
%py3_install
mv %{buildroot}%{_bindir}/aexpect-helper %{buildroot}%{_bindir}/aexpect-helper-%{python3_version}
ln -s aexpect-helper-%{python3_version} %{buildroot}%{_bindir}/aexpect-helper-3
%endif

# use python2 for unversioned executable
ln -s aexpect-helper-%{python2_version} %{buildroot}%{_bindir}/aexpect-helper

%check
%if %{with_tests}
selftests/checkall
%endif

%files -n python2-%{srcname}
%license LICENSE
%doc README.rst
%{python2_sitelib}/aexpect/
%{python2_sitelib}/aexpect-%{version}-py%{python2_version}.egg-info
%{_bindir}/aexpect-helper
%{_bindir}/aexpect-helper-2*

%if %{with_python3}
%files -n python%{python3_pkgversion}-%{srcname}
%license LICENSE
%doc README.rst
%{python3_sitelib}/aexpect/
%{python3_sitelib}/aexpect-%{version}-py%{python3_version}.egg-info
%{_bindir}/aexpect-helper-3*
%endif

%changelog
* Wed Mar 14 2018 Cleber Rosa <cleber@redhat.com> - 1.4.0-2
- Changed URL to aexpect repo
- Changed build to use a git archived based source
- Added released version builds
- Remove compatiblity with older package name
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
