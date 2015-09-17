Summary: Aexpect is a python library to control interactive applications
Name: aexpect
Version: 1.1.0
Release: 1%{?dist}
License: GPLv2
Group: Development/Tools
URL: http://avocado-framework.readthedocs.org/
Source: aexpect-%{version}.tar.gz
BuildArch: noarch
Requires: python
BuildRequires: python

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
* Thu Sep 17 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.1.0-1
- Update to upstream version 1.1.0.

* Fri Jul 31 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.1-2
- Fix spec bug

* Fri Jul 31 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.1-1
- First COPR build

* Thu Apr 23 2015 Lucas Meneghel Rodrigues <lmr@redhat.com> - 1.0.0-1
- First RPM
