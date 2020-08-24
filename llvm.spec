Name:		llvm
Version:	10.0.1
Release:        1
Summary:	The Low Level Virtual Machine
License:	NCSA
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/%{name}-%{version}.src.tar.xz

BuildRequires:  gcc gcc-c++ cmake ninja-build zlib-devel libffi-devel ncurses-devel libstdc++-static
BuildRequires:	python3-sphinx binutils-devel valgrind-devel libedit-devel python3-devel
BuildRequires:  python3-recommonmark
BuildRequires:  llvm-libs

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

%build
#TODO: -DLLVM_TARGETS_TO_BUILD=all in needed(temporarily) when build rust,
#      clarification is required in the future
mkdir -p _build
cd _build
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%cmake .. -G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=1 \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_INSTALL_RPATH=";" \
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
%if 0
%ifarch %ix86 x86_64
	-DLLVM_TARGETS_TO_BUILD="X86;AMDGPU;NVPTX;BPF;ARM;AArch64" \
%endif
%ifarch aarch64
	-DLLVM_TARGETS_TO_BUILD="AArch64;AMDGPU;BPF" \
%endif
%ifarch %{arm}
	-DLLVM_TARGETS_TO_BUILD="ARM;AMDGPU;BPF" \
%endif
%endif
	-DLLVM_TARGETS_TO_BUILD=all \
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
	-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=AVR \
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_UTILS_INSTALL_DIR:PATH=%{_bindir} \
	-DLLVM_TOOLS_INSTALL_DIR:PATH=bin \
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	-DLLVM_VERSION_SUFFIX='' \
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_DYLIB_EXPORT_ALL:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3

%ninja_build LLVM
%ninja_build

%install
%ninja_install -C _build

find %{buildroot}%{_libdir}/cmake/llvm -type f | xargs sed -i "s|%{buildroot}||g"
mv -v %{buildroot}%{_bindir}/llvm-config{,-%{__isa_bits}}

for f in llvm-isel-fuzzer llvm-opt-fuzzer; do
install -m 0755 ./_build/bin/$f %{buildroot}%{_bindir}
done

%global install_srcdir %{buildroot}%{_datadir}/llvm/src
%global lit_cfg test/lit.site.cfg.py
%global lit_unit_cfg test/Unit/lit.site.cfg.py

install -d %{install_srcdir}
install -d %{install_srcdir}/utils/
cp -R utils/unittest %{install_srcdir}/utils/

cat _build/test/lit.site.cfg.py >> %{lit_cfg}
cat _build/test/Unit/lit.site.cfg.py >> %{lit_unit_cfg}
sed -i -e s~`pwd`/_build~%{_prefix}~g -e s~`pwd`~.~g %{lit_cfg} %{lit_cfg} %{lit_unit_cfg}

sed -i 's~\(config.llvm_obj_root = \)"[^"]\+"~\1"%{_libdir}/%{name}"~' %{lit_unit_cfg}

install -d %{buildroot}%{_libexecdir}/tests/llvm

install -d %{buildroot}%{_datadir}/llvm/
tar -czf %{install_srcdir}/test.tar.gz test/

mkdir -p %{buildroot}%{_libdir}/%{name}
cp -R _build/unittests %{buildroot}%{_libdir}/%{name}/
find %{buildroot}%{_libdir}/%{name} -ignore_readdir_race -iname 'cmake*' -exec rm -Rf '{}' ';' || true

#TODO: clang rust mesa packages will be unresolvable without this work-around
cp -p %{_libdir}/libLLVM-7*.so %{buildroot}%{_libdir}
cp -p %{_libdir}/libLTO.so.7 %{buildroot}%{_libdir}

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
%{_libdir}/%{name}/unittests/
%{_datadir}/llvm/src/test.tar.gz

%files help
%doc %{_pkgdocdir}/html
%{_mandir}/man1/*

%changelog
* Mon Aug 24 2020 Liquor <lirui130@huawei.com> - 10.0.1-1
- Type: update
- ID: NA
- SUG: NA
- DESC:update to 10.0.1

* Mon May 18 2020 wangchen <wangchen137@huawei.com> - 7.0.0-10
- rebuild for llvm

* Wed Mar 18 2020 openEuler Buildteam <buildteam@openeuler.org> - 7.0.0-9
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: add four patches

* Sat Jan 11 2020 openEuler Buildteam <buildteam@openeuler.org> - 7.0.0-8
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: remove unnecessary files

* Tue Dec 31 2019 openEuler Buildteam <buildteam@openeuler.org> -7.0.0-7
- Type: enhancement
- ID: NA
- SUG: NA
- DESC: delete conflict files in llvm

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
