Name:		llvm
Version:	7.0.0
Release:        6
Summary:	The Low Level Virtual Machine
License:	NCSA
URL:		http://llvm.org
Source0:	http://releases.llvm.org/7.0.0/%{name}-%{version}.src.tar.xz
Source1:        run-lit-tests
Patch0:         0001-CMake-Split-static-library-exports-into-their-own-ex.patch
Patch1:         0001-Filter-out-cxxflags-not-supported-by-clang.patch
Patch2:         0001-unittests-Don-t-install-TestPlugin.so.patch
Patch3:         0001-CMake-Don-t-prefer-python2.7.patch
Patch4:         0001-Don-t-set-rpath-when-installing.patch

BuildRequires:  gcc gcc-c++ cmake ninja-build zlib-devel libffi-devel ncurses-devel libstdc++-static
BuildRequires:	python3-sphinx multilib-rpm-config binutils-devel valgrind-devel
BuildRequires:  libedit-devel python3-devel

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages.

The LLVM compiler infrastructure supports a wide range of projects,
from industrial strength compilers to specialized JIT applications
to small research projects.

%package libs
Summary:LLVM shared libraries

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name} = %{version}-%{release}
Requires:       libedit-devel python3-lit binutils gcc
Requires(post):  %{_sbindir}/alternatives
Requires(postun):%{_sbindir}/alternatives
Provides:       %{name}-static = %{version}-%{release}
Obsoletes:      %{name}-static < %{version}-%{release}
Provides:       %{name}-googletest = %{version}-%{release}
Obsoletes:      %{name}-googletest < %{version}-%{release}
Provides:       %{name}-test = %{version}-%{release}
Obsoletes:      %{name}-test < %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package	help
Summary: 	Doc files for %{name}
Buildarch:	noarch
Requires:	man
Provides:       %{name}-doc = %{version}-%{release}
Obsoletes:      %{name}-doc < %{version}-%{release}

%description 	help
The %{name}-help package contains doc files for %{name}.

%prep
%autosetup -n %{name}-%{version}.src -p1
pathfix.py -i %{__python3} -pn test/BugPoint/compile-custom.ll.py tools/opt-viewer/*.py
sed -i 's~@TOOLS_DIR@~%{_libdir}/%{name}~' %{SOURCE1}

%build
mkdir -p _build
cd _build
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%cmake .. -G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%ifarch %ix86 x86_64
	-DLLVM_TARGETS_TO_BUILD="X86;AMDGPU;NVPTX;BPF;ARM;AArch64" \
%endif
%ifarch aarch64
	-DLLVM_TARGETS_TO_BUILD="AArch64;AMDGPU;BPF" \
%endif
%ifarch %{arm}
	-DLLVM_TARGETS_TO_BUILD="ARM;AMDGPU;BPF" \
%endif
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=%{buildroot}%{_libdir}/%{name} \
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_DYLIB_EXPORT_ALL:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DCMAKE_INSTALL_PREFIX=%{buildroot}/usr \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{buildroot}%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3

ninja -v

%install
cd _build
ninja -v install

mv -v %{buildroot}%{_bindir}/llvm-config{,-%{__isa_bits}}

%multilib_fix_c_header --file %{_includedir}/llvm/Config/llvm-config.h

for f in lli-child-target llvm-isel-fuzzer llvm-opt-fuzzer yaml-bench; do
install -m 0755 ./bin/$f %{buildroot}%{_libdir}/%{name}
done

%global install_srcdir %{buildroot}%{_datadir}/llvm/src
%global lit_cfg test/lit.site.cfg.py
%global lit_unit_cfg test/Unit/lit.site.cfg.py

cd ..

install -d %{install_srcdir}
install -d %{install_srcdir}/utils/
cp -R utils/unittest %{install_srcdir}/utils/

cat _build/test/lit.site.cfg.py >> %{lit_cfg}
cat _build/test/Unit/lit.site.cfg.py >> %{lit_unit_cfg}
sed -i -e s~`pwd`/_build~%{_prefix}~g -e s~`pwd`~.~g %{lit_cfg} %{lit_cfg} %{lit_unit_cfg}

sed -i 's~\(config.llvm_obj_root = \)"[^"]\+"~\1"%{_libdir}/%{name}"~' %{lit_unit_cfg}

install -d %{buildroot}%{_libexecdir}/tests/llvm
install -m 0755 %{SOURCE1} %{buildroot}%{_libexecdir}/tests/llvm

install -d %{buildroot}%{_datadir}/llvm/
tar -czf %{install_srcdir}/test.tar.gz test/

cp -R _build/unittests %{buildroot}%{_libdir}/%{name}/
find %{buildroot}%{_libdir}/%{name} -ignore_readdir_race -iname 'cmake*' -exec rm -Rf '{}' ';' || true

%check
cd _build
ninja check-all || :

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%post devel
%{_sbindir}/update-alternatives --install %{_bindir}/llvm-config llvm-config %{_bindir}/llvm-config-%{__isa_bits} %{__isa_bits}

%postun devel
if [ $1 -eq 0 ]; then
  %{_sbindir}/update-alternatives --remove llvm-config %{_bindir}/llvm-config-%{__isa_bits}
fi

%files
%license LICENSE.TXT
%{_bindir}/*
%{_libdir}/%{name}/*
%{_datadir}/opt-viewer/*
%exclude %{_bindir}/llvm-config-%{__isa_bits}
%exclude %{_libdir}/%{name}/unittests/

%files libs
%{_libdir}/*.so*
%exclude %{_libdir}/libLLVM.so

%files devel
%{_bindir}/llvm-config-%{__isa_bits}
%{_includedir}/llvm/*
%{_includedir}/llvm-c/*
%{_libdir}/cmake/llvm/*
%{_libdir}/libLLVM.so
%{_libdir}/*.a
%{_datadir}/llvm/src/utils
%{_libexecdir}/tests/llvm/
%{_libdir}/%{name}/unittests/
%{_datadir}/llvm/src/test.tar.gz
%{_libdir}/%{name}/yaml-bench
%{_libdir}/%{name}/lli-child-target
%{_libdir}/%{name}/llvm-isel-fuzzer
%{_libdir}/%{name}/llvm-opt-fuzzer

%files help
%doc %{_pkgdocdir}/html
%{_mandir}/man1/*

%changelog
* Fri Nov 1 2019 jiangchuangang <jiangchuangang@huawei.com> -7.0.0-6
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: add libs package

* Mon Oct 28 2019 jiangchuangang <jiangchuangang@huawei.com> -7.0.0-5
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: add test files

* Sun Sep 29 2019 luhuaxin <luhuaxin@huawei.com> - 7.0.0-4
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: add license file

* Fri Sep 20 2019 luhuaxin <luhuaxin@huawei.com> - 7.0.0-3
- Package init
