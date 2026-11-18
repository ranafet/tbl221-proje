Name:           tbl221-monitor
Version:        1.0.0
Release:        1%{?dist}
Summary:        Linux system resource recorder and graphical dashboard
License:        BSD-3-Clause
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

%description
TBL221 periodically records Linux CPU, memory, swap, disk, process and load
metrics in SQLite and presents them in a PySide6 graphical dashboard.

%package -n tbl221-record
Summary:        Linux system resource recorder
Requires:       python3 >= 3.11
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description -n tbl221-record
Periodically records Linux resource metrics in SQLite and emits threshold
alerts through a hardened systemd service.

%package -n tbl221-graphui
Summary:        Graphical dashboard for TBL221 resource measurements
Requires:       python3 >= 3.11
Requires:       python3dist(pyside6) >= 6.8
Recommends:     tbl221-record = %{version}

%description -n tbl221-graphui
Displays live cards, history charts and alerts from the SQLite database
maintained by tbl221-record, and exports selected measurements as CSV.

%prep
%autosetup

%build
python3 -m compileall -q tbl221-record tbl221-graphui

%install
install -d %{buildroot}%{_prefix}/libexec/tbl221-record
install -m 0644 tbl221-record/main.py %{buildroot}%{_prefix}/libexec/tbl221-record/main.py
cp -a tbl221-record/config tbl221-record/db tbl221-record/model tbl221-record/util \
    %{buildroot}%{_prefix}/libexec/tbl221-record/
find %{buildroot}%{_prefix}/libexec/tbl221-record -type d -name __pycache__ -prune -exec rm -rf '{}' +
find %{buildroot}%{_prefix}/libexec/tbl221-record -type f -exec chmod 0644 '{}' +
install -D -m 0755 packaging/bin/tbl221-record %{buildroot}%{_bindir}/tbl221-record
install -D -m 0644 packaging/systemd/tbl221-record.service %{buildroot}%{_unitdir}/tbl221-record.service
install -D -m 0644 tbl221-record/config/default.toml %{buildroot}%{_sysconfdir}/tbl221-record.toml
install -d %{buildroot}%{_sharedstatedir}/tbl221-record
install -D -m 0644 docs/tbl221-record.8 %{buildroot}%{_mandir}/man8/tbl221-record.8

install -D -m 0644 tbl221-graphui/main.py %{buildroot}%{_prefix}/libexec/tbl221-graphui/main.py
install -D -m 0755 packaging/bin/tbl221-graphui %{buildroot}%{_bindir}/tbl221-graphui
install -D -m 0644 packaging/applications/tbl221-graphui.desktop %{buildroot}%{_datadir}/applications/tbl221-graphui.desktop
install -D -m 0644 docs/tbl221-graphui.8 %{buildroot}%{_mandir}/man8/tbl221-graphui.8

%post -n tbl221-record
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload >/dev/null 2>&1 || :
    systemctl preset tbl221-record.service >/dev/null 2>&1 || :
fi

%preun -n tbl221-record
if [ "$1" -eq 0 ] && command -v systemctl >/dev/null 2>&1; then
    systemctl disable --now tbl221-record.service >/dev/null 2>&1 || :
fi

%postun -n tbl221-record
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload >/dev/null 2>&1 || :
fi

%files -n tbl221-record
%license LICENSE
%doc README.md
%{_bindir}/tbl221-record
%{_prefix}/libexec/tbl221-record/
%{_unitdir}/tbl221-record.service
%config(noreplace) %{_sysconfdir}/tbl221-record.toml
%dir %{_sharedstatedir}/tbl221-record
%{_mandir}/man8/tbl221-record.8%{?ext_man}

%files -n tbl221-graphui
%license LICENSE
%doc README.md
%{_bindir}/tbl221-graphui
%{_prefix}/libexec/tbl221-graphui/
%{_datadir}/applications/tbl221-graphui.desktop
%{_mandir}/man8/tbl221-graphui.8%{?ext_man}

%changelog
* Wed Nov 18 2026 Yiğit Cemal Öztürk <251307091@kocaeli.edu.tr> - 1.0.0-1
- Initial RPM package
