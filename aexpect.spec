Summary: Aexpect is a python library to control interactive applications
Name: aexpect
Version: 1.3.1
Release: 0%{?dist}
License: GPLv2
Group: Development/Tools
URL: http://avocado-framework.readthedocs.org/
Source: aexpect-%{version}.tar.gz
BuildArch: noarch
Requires: python
BuildRequires: python, python-setuptools

%description
Aexpect is a python library used to control interactive applications, very
similar to pexpect. You can use it to control applications such as ssh, scp
sftp, telnet, among others.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install --root %{buildroot} --skip-build

%files
%defattr(-,root,root,-)
%{python_sitelib}/aexpect*
%{_bindir}/aexpect-helper

%changelog
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
