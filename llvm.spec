%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}

Name:		llvm
Version:	7.0.0
Release:        4
Summary:	The Low Level Virtual Machine
License:	NCSA	
URL:		http://llvm.org
Source0:	http://releases.llvm.org/7.0.0/%{name}-%{version}.src.tar.xz
Patch0:         0001-CMake-Split-static-library-exports-into-their-own-ex.patch
Patch1:         0001-Filter-out-cxxflags-not-supported-by-clang.patch
Patch2:         0001-unittests-Don-t-install-TestPlugin.so.patch
Patch3:         0001-CMake-Don-t-prefer-python2.7.patch
Patch4:         0001-Don-t-set-rpath-when-installing.patch

BuildRequires:  gcc gcc-c++ cmake git ninja-build
BuildRequires:	zlib-devel libffi-devel ncurses-devel
BuildRequires:	python3-sphinx
BuildRequires:	multilib-rpm-config binutils-devel valgrind-devel
BuildRequires:  libedit-devel python3-devel
Provides:       %{name}-libs = %{version}-%{release}
Obsoletes:      %{name}-libs < %{version}-%{release}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages.

The LLVM compiler infrastructure supports a wide range of projects,
from industrial strength compilers to specialized JIT applications
to small research projects.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name} = %{version}-%{release}
Requires:       libedit-devel
Requires(post): %{_sbindir}/alternatives
Requires(postun): %{_sbindir}/alternatives
Provides:       %{name}-static = %{version}-%{release}
Obsoletes:      %{name}-static < %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package	help
Summary: 	Doc files for %{name}
Buildarch:	noarch
Requires:	man

%description 	help
The %{name}-help package contains doc files for %{name}.

%prep
%autosetup -n %{name}-%{version}.src -p1
pathfix.py -i %{__python3} -pn test/BugPoint/compile-custom.ll.py tools/opt-viewer/*.py

%build
mkdir -p _build; pushd _build

%cmake .. -G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
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
	-DLLVM_INCLUDE_TESTS:BOOL=OFF \
	-DLLVM_BUILD_TESTS:BOOL=OFF \
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=%{buildroot}/%{_libdir}/%{name} \
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
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{buildroot}/%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3

ninja -v

%install
pushd _build
ninja -v install
mv -v %{buildroot}/%{_bindir}/llvm-config{,-%{__isa_bits}}

for f in lli-child-target llvm-isel-fuzzer llvm-opt-fuzzer yaml-bench; do
    install -m 0755 ./bin/$f %{buildroot}/%{_libdir}/%{name}
done

popd

find %{buildroot}/%{_libdir}/%{name} -ignore_readdir_race -iname 'cmake*' -exec rm -Rf '{}' ';' || true

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
%{_libdir}/*.so*

%files devel
%{_bindir}/llvm-config-%{__isa_bits}
%{_includedir}/llvm/*
%{_includedir}/llvm-c/*
%{_libdir}/cmake/llvm/*
%{_libdir}/libLLVM.so
%{_libdir}/*.a

%files help
%doc %{_pkgdocdir}/html
%{_mandir}/man1/*

%changelog
* Sat Sep 29 2019 luhuaxin <luhuaxin@huawei.com> - 7.0.0-4
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: add license file

* Fri Sep 20 2019 luhuaxin <luhuaxin@huawei.com> - 7.0.0-3
- Package init
