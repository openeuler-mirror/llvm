%bcond_without sys_llvm
%bcond_without check

%global maj_ver 15
%global min_ver 0
%global patch_ver 7

%if %{with sys_llvm}
%global pkg_name llvm
%global bin_suffix %{nil}
%global install_prefix %{_prefix}
%else
%global pkg_name llvm%{maj_ver}
%global bin_suffix -%{maj_ver}
%global install_prefix %{_libdir}/%{name}
%endif

%global install_bindir %{install_prefix}/bin
%global install_includedir %{install_prefix}/include
%if 0%{?__isa_bits} == 64
%global install_libdir %{install_prefix}/lib64
%else
%global install_libdir %{install_prefix}/lib
%endif
%global install_srcdir %{install_prefix}/src

%global pkg_bindir %{install_bindir}
%global pkg_includedir %{install_includedir}
%global pkg_libdir %{install_libdir}
%global pkg_srcdir %{install_srcdir}

%global max_link_jobs 2
%global targets_to_build "all"
%global experimental_targets_to_build ""

%global build_install_prefix %{buildroot}%{install_prefix}
%global llvm_triple %{_host}

Name:		%{pkg_name}
Version:	%{maj_ver}.%{min_ver}.%{patch_ver}
Release:	3
Summary:	The Low Level Virtual Machine

License:	NCSA
URL:		http://llvm.org
Source0:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/llvm-%{version}.src.tar.xz
Source1:	https://github.com/llvm/llvm-project/releases/download/llvmorg-%{version}/cmake-%{version}.src.tar.xz

Patch1:		0001-Backport-RISCV-Handle-o-inline-asm-memory-constraint.patch

BuildRequires:	binutils-devel
BuildRequires:	cmake
BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	libedit-devel
BuildRequires:	libffi-devel
BuildRequires:	multilib-rpm-config
BuildRequires:	ncurses-devel
BuildRequires:	ninja-build
BuildRequires:	python3-devel
BuildRequires:	python3-psutil
BuildRequires:	python3-recommonmark
BuildRequires:	python3-sphinx
BuildRequires:	python3-setuptools
BuildRequires:	zlib-devel

Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

Provides:	llvm(major) = %{maj_ver}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages. The compiler infrastructure includes mirror sets of programming
tools as well as libraries with equivalent functionality.

%package devel
Summary:	Libraries and header files for LLVM
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
Requires:	libedit-devel
Requires:	%{name}-static%{?_isa} = %{version}-%{release}

Requires(post):	%{_sbindir}/alternatives
Requires(postun):	%{_sbindir}/alternatives

Provides:	llvm-devel(major) = %{maj_ver}

%description devel
This package contains library and header files needed to develop new native
programs that use the LLVM infrastructure.

%package doc
Summary:	Documentation for LLVM
BuildArch:	noarch
Requires:	%{name} = %{version}-%{release}

%description doc
Documentation for the LLVM compiler infrastructure.

%package libs
Summary:	LLVM shared libraries

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package static
Summary:	LLVM static libraries
Conflicts:	%{name}-devel < 8

Provides:	llvm-static(major) = %{maj_ver}

%description static
Static libraries for the LLVM compiler infrastructure.

%package test
Summary:	LLVM regression tests
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	%{name}-libs%{?_isa} = %{version}-%{release}
 
Provides:	llvm-test(major) = %{maj_ver}

%description test
LLVM regression tests.
 
%package googletest
Summary: LLVM's modified googletest sources
 
%description googletest
LLVM's modified googletest sources.

%prep
%setup -T -q -b 1 -n cmake-%{version}.src
cd ..
mv cmake-%{version}.src cmake
%autosetup -n llvm-%{version}.src
%autopatch -p2

pathfix.py -i %{__python3} -pn \
	test/BugPoint/compile-custom.ll.py \
	tools/opt-viewer/*.py \
	utils/update_cc_test_checks.py

%build
mkdir -p _build
cd _build

%cmake	.. -G Ninja \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DLLVM_PARALLEL_LINK_JOBS=%{max_link_jobs} \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_SKIP_RPATH:BOOL=ON \
	-DLLVM_TARGETS_TO_BUILD=%{targets_to_build} \
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
	-DLLVM_USE_PERF:BOOL=ON \
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
	-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=%{experimental_targets_to_build} \
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	-DLLVM_LIT_ARGS=-v \
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=ON \
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	-DLLVM_DEFAULT_TARGET_TRIPLE=%{llvm_triple} \
	-DSPHINX_WARNINGS_AS_ERRORS=OFF \
	-DCMAKE_INSTALL_PREFIX=%{install_prefix} \
	-DLLVM_INSTALL_SPHINX_HTML_DIR=%{_pkgdocdir}/html \
	-DSPHINX_EXECUTABLE=%{_bindir}/sphinx-build-3 \
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
	-DLLVM_INCLUDE_BENCHMARKS=OFF

%ninja_build LLVM
%ninja_build

%install
%ninja_install -C _build

mkdir -p %{buildroot}/%{_bindir}

# Install binaries needed for lit tests
for f in llvm-isel-fuzzer llvm-opt-fuzzer
do
   install -m 0755 %{_builddir}/llvm-%{version}.src/_build/bin/$f %{buildroot}%{install_bindir}
done

%if 0%{?__isa_bits} == 64
install %{_builddir}/llvm-%{version}.src/_build/lib64/libLLVMTestingSupport.a %{buildroot}%{install_libdir}
%else
install %{_builddir}/llvm-%{version}.src/_build/lib/libLLVMTestingSupport.a %{buildroot}%{install_libdir}
%endif

# Install gtest sources so clang can use them for gtest
install -d %{buildroot}%{install_srcdir}
install -d %{buildroot}%{install_srcdir}/utils/
cp -R %{_builddir}/llvm-%{version}.src/utils/unittest %{buildroot}%{install_srcdir}/utils/
 
# Clang needs these for running lit tests.
cp %{_builddir}/llvm-%{version}.src/utils/update_cc_test_checks.py %{buildroot}%{install_srcdir}/utils/
cp -R %{_builddir}/llvm-%{version}.src/utils/UpdateTestChecks %{buildroot}%{install_srcdir}/utils/

%if %{without sys_llvm}
# Add version suffix to binaries
for f in %{buildroot}/%{install_bindir}/*; do
  filename=`basename $f`
  ln -s ../../%{install_bindir}/$filename %{buildroot}/%{_bindir}/$filename%{bin_suffix}
done
%endif

# Move header files
mkdir -p %{buildroot}/%{pkg_includedir}
ln -s ../../../%{install_includedir}/llvm %{buildroot}/%{pkg_includedir}/llvm
ln -s ../../../%{install_includedir}/llvm-c %{buildroot}/%{pkg_includedir}/llvm-c

# Fix multi-lib
%multilib_fix_c_header --file %{install_includedir}/llvm/Config/llvm-config.h

# Create ld.so.conf.d entry
mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d
cat >> %{buildroot}%{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf << EOF
%{pkg_libdir}
EOF

%if %{without sys_llvm}
mkdir -p %{buildroot}/%{_mandir}/man1
for f in %{build_install_prefix}/share/man/man1/*; do
  filename=`basename $f | cut -f 1 -d '.'`
  mv $f %{buildroot}%{_mandir}/man1/$filename%{bin_suffix}.1
done

rm %{buildroot}%{_bindir}/llvm-config%{bin_suffix}
(cd %{buildroot}/%{pkg_bindir} ; ln -s llvm-config llvm-config%{bin_suffix}-%{__isa_bits} )

touch %{buildroot}%{_bindir}/llvm-config%{bin_suffix}
%endif

# Remove opt-viewer, since this is just a compatibility package.
rm -Rf %{build_install_prefix}/share/opt-viewer

cp -Rv ../cmake/Modules/* %{buildroot}%{pkg_libdir}/cmake/llvm

%check
%if %{with check}
LD_LIBRARY_PATH=%{buildroot}/%{pkg_libdir}  %{__ninja} check-all -C ./_build/
%endif

%ldconfig_scriptlets libs

%post devel
%if %{without sys_llvm}
%{_sbindir}/update-alternatives --install %{_bindir}/llvm-config%{bin_suffix} llvm-config%{bin_suffix} %{pkg_bindir}/llvm-config%{bin_suffix}-%{__isa_bits} %{__isa_bits}
%endif

%postun devel
%if %{without sys_llvm}
if [ $1 -eq 0 ]; then
  %{_sbindir}/update-alternatives --remove llvm-config%{bin_suffix} %{pkg_bindir}/llvm-config%{bin_suffix}-%{__isa_bits}
fi
%endif

%files
%license LICENSE.TXT
%exclude %{_mandir}/man1/llvm-config*
%{_mandir}/man1/*
%{pkg_bindir}/*

%if %{without sys_llvm}
%{_bindir}/*
%exclude %{_bindir}/llvm-config%{bin_suffix}
%exclude %{pkg_bindir}/llvm-config%{bin_suffix}-%{__isa_bits}
%exclude %{_bindir}/not%{bin_suffix}
%exclude %{_bindir}/count%{bin_suffix}
%exclude %{_bindir}/yaml-bench%{bin_suffix}
%exclude %{_bindir}/lli-child-target%{bin_suffix}
%exclude %{_bindir}/llvm-isel-fuzzer%{bin_suffix}
%exclude %{_bindir}/llvm-opt-fuzzer%{bin_suffix}
%endif

%exclude %{pkg_bindir}/not
%exclude %{pkg_bindir}/count
%exclude %{pkg_bindir}/yaml-bench
%exclude %{pkg_bindir}/lli-child-target
%exclude %{pkg_bindir}/llvm-isel-fuzzer
%exclude %{pkg_bindir}/llvm-opt-fuzzer

%files libs
%license LICENSE.TXT
%{pkg_libdir}/libLLVM-%{maj_ver}.so
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/%{name}-%{_arch}.conf
%{pkg_libdir}/LLVMgold.so
%{pkg_libdir}/libLLVM-%{maj_ver}.%{min_ver}*.so
%{pkg_libdir}/libLTO.so*
%exclude %{pkg_libdir}/libLTO.so
%{pkg_libdir}/libRemarks.so*

%files devel
%license LICENSE.TXT

%if %{without sys_llvm}
%ghost %{_bindir}/llvm-config%{bin_suffix}
%{pkg_bindir}/llvm-config%{bin_suffix}-%{__isa_bits}
%endif

%{_mandir}/man1/llvm-config*
%{pkg_includedir}/llvm
%{pkg_includedir}/llvm-c
%{pkg_libdir}/libLTO.so
%{pkg_libdir}/libLLVM.so
%{pkg_libdir}/cmake/llvm

%files doc
%license LICENSE.TXT
%doc %{_pkgdocdir}/html

%files static
%license LICENSE.TXT
%{pkg_libdir}/*.a
%exclude %{pkg_libdir}/libLLVMTestingSupport.a

%files test
%license LICENSE.TXT
%if %{without sys_llvm}
%{_bindir}/not%{bin_suffix}
%{_bindir}/count%{bin_suffix}
%{_bindir}/yaml-bench%{bin_suffix}
%{_bindir}/lli-child-target%{bin_suffix}
%{_bindir}/llvm-isel-fuzzer%{bin_suffix}
%{_bindir}/llvm-opt-fuzzer%{bin_suffix}
%endif
%{pkg_bindir}/not
%{pkg_bindir}/count
%{pkg_bindir}/yaml-bench
%{pkg_bindir}/lli-child-target
%{pkg_bindir}/llvm-isel-fuzzer
%{pkg_bindir}/llvm-opt-fuzzer
 
%files googletest
%license LICENSE.TXT
%{pkg_srcdir}/utils
%{pkg_libdir}/libLLVMTestingSupport.a

%changelog
* Tue Jul 04 2023 cf-zhao <zhaochuanfeng@huawei.com> - 15.0.7-3
- [RISCV] Handle "o" inline asm memory constraint

* Fri May 19 2023 cf-zhao <zhaochuanfeng@huawei.com> -15.0.7-2
- Make this spec file support both system-version and multi-version.

* Mon Feb 20 2023 Chenxi Mao <chenxi.mao@suse.com> - 15.0.7-1
- Upgrade to 15.0.7.

* Wed Feb 8 2023 Chenxi Mao <chenxi.mao@suse.com> - 15.0.6-3
- Create llvm-test/googletest to support clang/lld unit test.

* Fri Feb 3 2023 Chenxi Mao <chenxi.mao@suse.com> - 15.0.6-2
- Enable llvm utils tools.

* Mon Jan 2 2023 Chenxi Mao <chenxi.mao@suse.com> - 15.0.6-1
- Package init
