%global srcname aexpect

Summary: Aexpect is a python library to control interactive applications
Name: python-%{srcname}
Version: 1.4.0
Release: 1%{?dist}
License: GPLv2
Group: Development/Tools
URL: http://avocado-framework.readthedocs.org/
Source: %{srcname}-%{version}.tar.gz
BuildArch: noarch
Requires: python
BuildRequires: python, python-setuptools

# For compatibility reasons, let's mark this package as one that
# provides the same functionality as the old package name and also
# one that obsoletes the old package name, so that the new name is
# favored.  These could (and should) be removed in the future.
# These changes are backed by the following guidelines:
# https://fedoraproject.org/wiki/Upgrade_paths_%E2%80%94_renaming_or_splitting_packages
Obsoletes: %{srcname} < 1.3.1-1
Provides: %{srcname} = %{version}-%{release}

%description
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%prep
%setup -q -n %{srcname}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install --root %{buildroot} --skip-build
mv %{buildroot}%{_bindir}/aexpect-helper %{buildroot}%{_bindir}/aexpect-helper-%{python_version}

%files
%defattr(-,root,root,-)
%{python_sitelib}/aexpect*
%{_bindir}/aexpect-helper-*

%changelog
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
